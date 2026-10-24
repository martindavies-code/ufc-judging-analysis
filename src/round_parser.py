"""Parser for round-by-round UFC judging scorecards.

Extracts round-level scores (10-9, 10-8, etc.) for each judge on each round,
evaluates round-level consensus and dissents, and stores structured records
to CSV and SQLite.
"""

import logging
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.models import RoundScore
from src.parser import clean_judge_name
from src.security import safe_resolve_path, sanitize_text, validate_numeric_id

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
DECISIONS_HTML_DIR = DATA_DIR / "decisions_html"
SCORECARDS_CSV = DATA_DIR / "ufc_scorecards.csv"
ROUND_SCORES_CSV = DATA_DIR / "ufc_round_scores.csv"
DB_PATH = DATA_DIR / "ufc_judging.db"


def parse_round_cells(cells: List[Any]) -> Optional[Tuple[int, int, int]]:
    """Parse round row cells: [round_num, score_f1, score_f2].
    
    Validates that round is 1-5 and scores are plausible integers (7-10).
    """
    if len(cells) < 3:
        return None

    t0 = sanitize_text(cells[0].get_text(strip=True))
    t1 = sanitize_text(cells[1].get_text(strip=True))
    t2 = sanitize_text(cells[2].get_text(strip=True))

    if not t0.isdigit() or not t1.isdigit() or not t2.isdigit():
        return None

    r_num = int(t0)
    s1 = int(t1)
    s2 = int(t2)

    # In UFC standard bouts, rounds are 1 through 5
    if not (1 <= r_num <= 5):
        return None

    # Plausible individual round scores (typically 7-10)
    if not (5 <= s1 <= 10 and 5 <= s2 <= 10):
        return None

    return r_num, s1, s2


def parse_decision_rounds(html_text: str, decision_id: str, metadata: Optional[Dict[str, Any]] = None) -> List[RoundScore]:
    """Parse all round scorecards from a single decision HTML page.
    
    Calculates round-by-round consensus and identifies dissenting judges per round.
    """
    if not html_text:
        return []

    meta = metadata or {}
    event_id = str(meta.get('event_id', ''))
    event_year = str(meta.get('event_year', ''))
    fight = str(meta.get('fight', ''))
    fighter_1 = str(meta.get('fighter_1', ''))
    fighter_2 = str(meta.get('fighter_2', ''))

    soup = BeautifulSoup(html_text, 'html.parser')
    judge_tds = soup.find_all('td', class_='judge')

    if len(judge_tds) != 3:
        # Fallback: some pages might have 3 tables with class 'judge' in a different hierarchy
        return []

    judge_data: List[Dict[str, Any]] = []

    for td in judge_tds:
        tbl = td.find_parent('table')
        if not tbl:
            continue

        a_tag = td.find('a', href=True)
        slug = a_tag['href'] if a_tag else None
        judge_id = None
        if slug:
            m = re.search(r'judge/(\d+)/', slug)
            if m:
                judge_id = m.group(1)

        name = clean_judge_name(td.get_text(strip=True), slug)

        rounds_dict: Dict[int, Dict[str, Any]] = {}
        for r_row in tbl.find_all('tr', class_='decision'):
            cells = r_row.find_all(['td', 'th'])
            parsed = parse_round_cells(cells)
            if parsed is not None:
                r_num, s1, s2 = parsed
                pick = 'fighter_1' if s1 > s2 else ('fighter_2' if s2 > s1 else 'draw')
                is_ten_eight = abs(s1 - s2) >= 2
                rounds_dict[r_num] = {
                    's1': s1,
                    's2': s2,
                    'pick': pick,
                    'is_ten_eight': is_ten_eight
                }

        judge_data.append({
            'judge_id': judge_id,
            'judge_name': name,
            'rounds': rounds_dict
        })

    if len(judge_data) != 3:
        return []

    # Find common round numbers across all 3 judges
    common_rounds = set(judge_data[0]['rounds'].keys()) & set(judge_data[1]['rounds'].keys()) & set(judge_data[2]['rounds'].keys())
    if not common_rounds:
        return []

    results: List[RoundScore] = []

    for r_num in sorted(list(common_rounds)):
        j0_round = judge_data[0]['rounds'][r_num]
        j1_round = judge_data[1]['rounds'][r_num]
        j2_round = judge_data[2]['rounds'][r_num]

        p0 = j0_round['pick']
        p1 = j1_round['pick']
        p2 = j2_round['pick']

        # Judge 0 consensus check
        j0_colleagues_agreed = (p1 == p2)
        j0_dissented = bool(j0_colleagues_agreed and (p0 != p1))

        # Judge 1 consensus check
        j1_colleagues_agreed = (p0 == p2)
        j1_dissented = bool(j1_colleagues_agreed and (p1 != p0))

        # Judge 2 consensus check
        j2_colleagues_agreed = (p0 == p1)
        j2_dissented = bool(j2_colleagues_agreed and (p2 != p0))

        # Build RoundScore records
        results.append(RoundScore(
            decision_id=str(decision_id),
            event_id=event_id,
            event_year=event_year,
            fight=fight,
            fighter_1=fighter_1,
            fighter_2=fighter_2,
            round_num=r_num,
            judge_name=judge_data[0]['judge_name'],
            judge_id=judge_data[0]['judge_id'],
            score_f1=j0_round['s1'],
            score_f2=j0_round['s2'],
            round_pick=p0,
            colleagues_agreed=j0_colleagues_agreed,
            round_dissented=j0_dissented,
            colleague_1=judge_data[1]['judge_name'],
            colleague_2=judge_data[2]['judge_name'],
            is_ten_eight=j0_round['is_ten_eight']
        ))

        results.append(RoundScore(
            decision_id=str(decision_id),
            event_id=event_id,
            event_year=event_year,
            fight=fight,
            fighter_1=fighter_1,
            fighter_2=fighter_2,
            round_num=r_num,
            judge_name=judge_data[1]['judge_name'],
            judge_id=judge_data[1]['judge_id'],
            score_f1=j1_round['s1'],
            score_f2=j1_round['s2'],
            round_pick=p1,
            colleagues_agreed=j1_colleagues_agreed,
            round_dissented=j1_dissented,
            colleague_1=judge_data[0]['judge_name'],
            colleague_2=judge_data[2]['judge_name'],
            is_ten_eight=j1_round['is_ten_eight']
        ))

        results.append(RoundScore(
            decision_id=str(decision_id),
            event_id=event_id,
            event_year=event_year,
            fight=fight,
            fighter_1=fighter_1,
            fighter_2=fighter_2,
            round_num=r_num,
            judge_name=judge_data[2]['judge_name'],
            judge_id=judge_data[2]['judge_id'],
            score_f1=j2_round['s1'],
            score_f2=j2_round['s2'],
            round_pick=p2,
            colleagues_agreed=j2_colleagues_agreed,
            round_dissented=j2_dissented,
            colleague_1=judge_data[0]['judge_name'],
            colleague_2=judge_data[1]['judge_name'],
            is_ten_eight=j2_round['is_ten_eight']
        ))

    return results


def parse_all_cached_decisions(
    decisions_dir: Path = DECISIONS_HTML_DIR,
    scorecards_csv: Path = SCORECARDS_CSV
) -> List[RoundScore]:
    """Parse all downloaded decision HTML files into round score records."""
    if not scorecards_csv.exists():
        raise FileNotFoundError(f"Scorecards CSV not found at {scorecards_csv}")

    df_meta = pd.read_csv(scorecards_csv)
    df_meta_clean = df_meta.dropna(subset=['decision_id'])
    # Create lookup map by decision_id (as string) using fast itertuples
    meta_map: Dict[str, Dict[str, Any]] = {}
    for r in df_meta_clean.itertuples():
        did_str = str(int(r.decision_id))
        meta_map[did_str] = {
            'event_id': str(getattr(r, 'event_id', '') or ''),
            'event_year': str(getattr(r, 'event_year', '') or ''),
            'fight': str(getattr(r, 'fight', '') or ''),
            'fighter_1': str(getattr(r, 'fighter_1', '') or ''),
            'fighter_2': str(getattr(r, 'fighter_2', '') or ''),
        }

    html_files = list(decisions_dir.glob("*.html"))
    print(f"Parsing round scorecards from {len(html_files)} decision HTML files...")

    all_round_scores: List[RoundScore] = []
    skipped = 0

    for f in tqdm(html_files, desc="Parsing Rounds"):
        decision_id = f.stem
        try:
            content = f.read_text(encoding='utf-8', errors='replace')
            metadata = meta_map.get(decision_id, {})
            scores = parse_decision_rounds(content, decision_id, metadata)
            if scores:
                all_round_scores.extend(scores)
            else:
                skipped += 1
        except Exception as e:
            logger.warning("Error parsing decision %s: %s", decision_id, e)
            skipped += 1

    print(f"Extracted {len(all_round_scores)} total round scorecards ({skipped} decisions skipped or without round tables).")
    return all_round_scores


def save_round_scores(
    scores: List[RoundScore],
    csv_path: Path = ROUND_SCORES_CSV,
    db_path: Path = DB_PATH
) -> None:
    """Save parsed round scores to CSV and SQLite with indices."""
    if not scores:
        print("No round scores to save.")
        return

    records = [s.to_dict() for s in scores]
    df = pd.DataFrame(records)

    # Save to CSV atomically
    temp_csv = csv_path.with_suffix(".csv.tmp")
    df.to_csv(temp_csv, index=False, encoding="utf-8")
    os.replace(temp_csv, csv_path)
    print(f"Saved {len(df)} round scores to {csv_path}")

    # Save to SQLite database
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS round_scores")
        df.to_sql("round_scores", conn, index=False)

        # Create optimized query indices
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rs_judge ON round_scores(judge_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rs_decision ON round_scores(decision_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rs_year ON round_scores(event_year)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_rs_dissented ON round_scores(round_dissented)")
        conn.commit()
        print(f"Saved and indexed {len(df)} round scores into SQLite table 'round_scores' at {db_path}")
    finally:
        conn.close()


if __name__ == "__main__":
    scores = parse_all_cached_decisions()
    save_round_scores(scores)
