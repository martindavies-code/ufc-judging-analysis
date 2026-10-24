"""Rigorous, type-checked parser for UFC judge scorecards.

Extracts fight decisions, validates score constraints, isolates consensus logic,
and persists structured records to CSV and indexed SQLite.
"""

import json
import logging
import os
import re
import sqlite3
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.models import FightRecord, JudgeAppearance, JudgeScorecard, PanelConsensus
from src.security import safe_resolve_path, sanitize_text, validate_numeric_id

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_HTML_DIR = DATA_DIR / "events_html"
EVENTS_JSON_PATH = DATA_DIR / "ufc_events.json"
CSV_OUTPUT_PATH = DATA_DIR / "ufc_scorecards.csv"
JUDGE_CSV_OUTPUT_PATH = DATA_DIR / "ufc_judge_appearances.csv"
DB_OUTPUT_PATH = DATA_DIR / "ufc_judging.db"

# Minimum and maximum plausible total scores in 1 to 5 round MMA fights (10-point must system)
MIN_PLAUSIBLE_SCORE = 10
MAX_PLAUSIBLE_SCORE = 50


def parse_score(score_str: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """Parse string representation of round or fight scores (e.g., '48 - 47', '29-28').
    
    Validates that parsed integers fall within legitimate MMA scoring limits.
    Returns (None, None) on empty or invalid input.
    """
    if not score_str or not isinstance(score_str, str):
        return None, None
        
    cleaned = sanitize_text(score_str).strip()
    if cleaned.startswith('-') or cleaned.startswith('+'):
        return None, None

    # Match two numbers separated by hyphen or spaces, ignoring trailing deduction notes
    match = re.search(r'(?:^|[^\d-])(\d{1,2})\s*[-–—:]\s*(\d{1,2})', ' ' + cleaned)
    if not match:
        nums = re.findall(r'\b\d{1,2}\b', cleaned)
        if len(nums) >= 2:
            s1, s2 = int(nums[0]), int(nums[1])
        else:
            return None, None
    else:
        s1, s2 = int(match.group(1)), int(match.group(2))
        
    # Boundary validation: Reject corrupted or absurd point values
    if not (MIN_PLAUSIBLE_SCORE <= s1 <= MAX_PLAUSIBLE_SCORE and MIN_PLAUSIBLE_SCORE <= s2 <= MAX_PLAUSIBLE_SCORE):
        return None, None
        
    return s1, s2


def clean_judge_name(raw_name: Optional[str], slug: Optional[str] = None) -> str:
    """Normalize judge names to canonical title-case representations.
    
    Handles URL slugs (e.g. 'judge/357/Michael-Bell' -> 'Michael Bell'),
    strips control characters, repairs encoding artifacts, and normalizes spacing.
    """
    candidate = None
    if slug:
        slug_clean = re.sub(r'[\r\n\t]+', '', slug).strip()
        m = re.search(r'judge/\d+/([^/]+)', slug_clean)
        candidate = m.group(1) if m else slug_clean
        candidate = candidate.replace('-', ' ')
        candidate = candidate.replace('%C3%B3', 'ó').replace('%C3%A9', 'é').replace('%C3%AD', 'í')

    if not candidate:
        candidate = raw_name

    raw_clean = sanitize_text(candidate)
    if not raw_clean:
        return "Unknown Judge"

    # Repair common latin-1/cp1252 encoding replacement artifacts
    raw_clean = re.sub(r'\bCol[oó\ufffd]?n\b', 'Colón', raw_clean, flags=re.IGNORECASE)
    raw_clean = re.sub(r'\bPatl[aá\ufffd]?n\b', 'Patlán', raw_clean, flags=re.IGNORECASE)
    raw_clean = raw_clean.replace('\ufffd', '')

    cleaned = " ".join(raw_clean.split()).title()

    # Canonical spelling for prominent UFC judges
    canonical_map = {
        "Sal Damato": "Sal D'Amato",
        "Sal D Amato": "Sal D'Amato",
        "John Mccarthy": "John McCarthy",
        "Ron Mccarthy": "Ron McCarthy",
        "Eric Colon": "Eric Colón",
        "Eric Coln": "Eric Colón",
        "Patrick Patlan": "Patrick Patlán",
        "Patrick Patln": "Patrick Patlán",
    }
    return canonical_map.get(cleaned, cleaned)


def determine_panel_consensus(judges: List[JudgeScorecard]) -> PanelConsensus:
    """Evaluate consensus and identify dissenting judge in a 3-judge panel.
    
    Pure, side-effect-free function:
    - If 2 or 3 judges agree on pick -> majority_pick is established.
    - If exactly 1 judge differs from the 2-judge majority -> has_dissenter = True.
    - If all 3 judges differ (split draw 1-1-1) -> is_three_way_split = True, has_dissenter = False.
    """
    if len(judges) != 3:
        raise ValueError(f"Panel must contain exactly 3 judges, got {len(judges)}")
        
    picks = [j.pick for j in judges]
    pick_counts: Dict[str, int] = {}
    for p in picks:
        pick_counts[p] = pick_counts.get(p, 0) + 1
        
    majority_pick: Optional[str] = None
    for pick, count in pick_counts.items():
        if count >= 2 and pick != "unknown":
            majority_pick = pick
            break
            
    if majority_pick is not None:
        dissenter_idx: Optional[int] = None
        dissenter_name: Optional[str] = None
        for idx, j in enumerate(judges):
            if j.pick != majority_pick:
                dissenter_idx = idx
                dissenter_name = j.judge_name
                break
                
        return PanelConsensus(
            majority_pick=majority_pick,
            has_dissenter=(dissenter_idx is not None),
            dissenter_idx=dissenter_idx,
            dissenter_name=dissenter_name,
            is_three_way_split=False
        )
    else:
        # 3-way disagreement or unknown picks
        return PanelConsensus(
            majority_pick=None,
            has_dissenter=False,
            dissenter_idx=None,
            dissenter_name=None,
            is_three_way_split=True
        )


def parse_event_html(
    html_content: str, 
    event_id: str, 
    default_title: str = "", 
    default_year: str = ""
) -> Tuple[List[FightRecord], List[JudgeAppearance]]:
    """Parse HTML content of a UFC event into typed fight and appearance records."""
    validate_numeric_id(event_id, "event_id")
    
    # Try accelerated lxml parser, fallback to html.parser
    try:
        soup = BeautifulSoup(html_content, 'lxml')
    except Exception:
        soup = BeautifulSoup(html_content, 'html.parser')
        
    title_el = soup.find('td', class_='decision-top2')
    event_title = default_title
    event_location = ""
    if title_el:
        lines = [x.strip() for x in title_el.stripped_strings]
        if lines:
            event_title = lines[0]
            if len(lines) > 1:
                event_location = ", ".join(lines[1:])
                
    date_el = soup.find('td', class_='decision-bottom2')
    event_date = date_el.get_text(strip=True) if date_el else ""
    
    fights: List[FightRecord] = []
    appearances: List[JudgeAppearance] = []
    
    for a in soup.find_all('a', href=re.compile(r'decision/\d+/')):
        decision_href = a['href'].strip()
        m_dec = re.search(r'decision/(\d+)/', decision_href)
        if not m_dec:
            continue
        decision_id = m_dec.group(1)
        validate_numeric_id(decision_id, "decision_id")
        
        tr = a.find_parent('tr')
        if not tr:
            continue
        tds = tr.find_all('td')
        if len(tds) < 4:
            continue
            
        fight_td = tds[0]
        fight_text = sanitize_text(a.get_text(strip=True))
        dec_type_el = fight_td.find('i')
        decision_type = sanitize_text(dec_type_el.get_text(strip=True)) if dec_type_el else "Unknown"
        
        # Fighter and outcome extraction
        fighter1, fighter2, outcome = "", "", ""
        if " def. " in fight_text:
            parts = fight_text.split(" def. ", 1)
            fighter1 = sanitize_text(parts[0])
            fighter2 = sanitize_text(parts[1])
            outcome = "def"
        elif " drew with " in fight_text:
            parts = fight_text.split(" drew with ", 1)
            fighter1 = sanitize_text(parts[0])
            fighter2 = sanitize_text(parts[1])
            outcome = "draw"
        else:
            fighter1 = fight_text
            outcome = "other"
            
        judges: List[JudgeScorecard] = []
        for j_td in tds[1:4]:
            j_a = j_td.find('a', href=re.compile(r'judge/\d+/'))
            j_id: Optional[str] = None
            j_name: str = ""
            j_short: str = ""
            
            if j_a:
                j_href = j_a['href'].strip()
                j_short = sanitize_text(j_a.get_text(strip=True))
                m_j = re.search(r'judge/(\d+)/([^/\s]+)', j_href)
                if m_j:
                    j_id = m_j.group(1)
                    validate_numeric_id(j_id, "judge_id")
                    j_name = clean_judge_name(j_short, m_j.group(2))
                else:
                    j_name = clean_judge_name(j_short)
            else:
                j_name = clean_judge_name(j_td.get_text(strip=True))
                j_short = j_name
                
            score_span = j_td.find('span')
            if score_span:
                score_raw = " ".join(score_span.get_text(strip=True).split())
            else:
                score_raw = j_td.get_text(strip=True).replace(j_short, '').strip()
                
            s1, s2 = parse_score(score_raw)
            if s1 is not None and s2 is not None:
                if s1 > s2:
                    pick = "fighter_1"
                elif s1 < s2:
                    pick = "fighter_2"
                else:
                    pick = "draw"
            else:
                pick = "unknown"
                
            has_selected_class = 'selected' in j_td.get('class', [])
            
            judges.append(JudgeScorecard(
                judge_id=j_id,
                judge_name=j_name,
                judge_short=j_short,
                score_text=score_raw if score_raw else "N/A",
                score_f1=s1,
                score_f2=s2,
                pick=pick,
                has_selected_class=has_selected_class
            ))
            
        if len(judges) != 3:
            continue
            
        consensus = determine_panel_consensus(judges)
        scores = [(j.score_f1, j.score_f2) for j in judges]
        
        fight_record = FightRecord(
            event_id=event_id,
            event_title=event_title,
            event_date=event_date,
            event_year=default_year,
            event_location=event_location,
            decision_id=decision_id,
            decision_url=f"https://mmadecisions.com/{decision_href}",
            fight=fight_text,
            fighter_1=fighter1,
            fighter_2=fighter2,
            outcome=outcome,
            decision_type=decision_type,
            majority_pick=consensus.majority_pick,
            has_dissenter=consensus.has_dissenter,
            dissenter_judge_name=consensus.dissenter_name,
            j1_name=judges[0].judge_name,
            j1_score=judges[0].score_text,
            j1_pick=judges[0].pick,
            j1_dissented=(consensus.dissenter_idx == 0),
            j2_name=judges[1].judge_name,
            j2_score=judges[1].score_text,
            j2_pick=judges[1].pick,
            j2_dissented=(consensus.dissenter_idx == 1),
            j3_name=judges[2].judge_name,
            j3_score=judges[2].score_text,
            j3_pick=judges[2].pick,
            j3_dissented=(consensus.dissenter_idx == 2),
        )
        fights.append(fight_record)
        
        # Individual appearances
        for idx, j in enumerate(judges):
            other_judges = [judges[k].judge_name for k in range(3) if k != idx]
            other_picks = [judges[k].pick for k in range(3) if k != idx]
            other_scores = [scores[k] for k in range(3) if k != idx]
            
            colleagues_agreed = (
                other_picks[0] == other_picks[1] and 
                other_picks[0] != "unknown"
            )
            disagreed_with_both = (
                colleagues_agreed and 
                j.pick != other_picks[0]
            )
            colleagues_same_score = (
                other_scores[0] == other_scores[1] and 
                other_scores[0][0] is not None
            )
            disagreed_on_score = (
                colleagues_same_score and 
                scores[idx] != other_scores[0]
            )
            
            appearance = JudgeAppearance(
                judge_id=j.judge_id,
                judge_name=j.judge_name,
                event_id=event_id,
                event_title=event_title,
                event_date=event_date,
                event_year=default_year,
                decision_id=decision_id,
                fight=fight_text,
                decision_type=decision_type,
                judge_score=j.score_text,
                judge_pick=j.pick,
                colleagues_agreed=colleagues_agreed,
                disagreed_with_both=disagreed_with_both,
                colleagues_same_score=colleagues_same_score,
                disagreed_on_score=disagreed_on_score,
                has_selected_class=j.has_selected_class,
                colleague_1=other_judges[0],
                colleague_2=other_judges[1]
            )
            appearances.append(appearance)
            
    return fights, appearances


def init_database_schema(conn: sqlite3.Connection) -> None:
    """Initialize strict SQLite schema with high-performance indexes."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fights (
            event_id TEXT NOT NULL,
            event_title TEXT,
            event_date TEXT,
            event_year TEXT,
            event_location TEXT,
            decision_id TEXT PRIMARY KEY,
            decision_url TEXT,
            fight TEXT NOT NULL,
            fighter_1 TEXT,
            fighter_2 TEXT,
            outcome TEXT,
            decision_type TEXT,
            majority_pick TEXT,
            has_dissenter INTEGER,
            dissenter_judge_name TEXT,
            j1_name TEXT,
            j1_score TEXT,
            j1_pick TEXT,
            j1_dissented INTEGER,
            j2_name TEXT,
            j2_score TEXT,
            j2_pick TEXT,
            j2_dissented INTEGER,
            j3_name TEXT,
            j3_score TEXT,
            j3_pick TEXT,
            j3_dissented INTEGER
        );
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS judge_appearances (
            judge_id TEXT,
            judge_name TEXT NOT NULL,
            event_id TEXT NOT NULL,
            event_title TEXT,
            event_date TEXT,
            event_year TEXT,
            decision_id TEXT NOT NULL,
            fight TEXT NOT NULL,
            decision_type TEXT,
            judge_score TEXT,
            judge_pick TEXT,
            colleagues_agreed INTEGER,
            disagreed_with_both INTEGER,
            colleagues_same_score INTEGER,
            disagreed_on_score INTEGER,
            has_selected_class INTEGER,
            colleague_1 TEXT,
            colleague_2 TEXT
        );
    """)
    # Performance Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ja_judge_name ON judge_appearances(judge_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ja_event_year ON judge_appearances(event_year);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ja_decision_id ON judge_appearances(decision_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_fights_has_dissenter ON fights(has_dissenter);")
    conn.commit()


def parse_all_events() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Parse all downloaded UFC event HTML files and persist to CSV/SQLite."""
    if not EVENTS_JSON_PATH.exists():
        raise FileNotFoundError(f"{EVENTS_JSON_PATH} not found. Run scraper first.")
        
    with open(EVENTS_JSON_PATH, 'r', encoding='utf-8') as f:
        events = json.load(f)
        
    print(f"Parsing HTML scorecards for {len(events)} events...")
    
    all_fights: List[Dict[str, Any]] = []
    all_appearances: List[Dict[str, Any]] = []
    
    for event in tqdm(events, desc="Parsing"):
        event_id = event['event_id']
        validate_numeric_id(event_id, "event_id")
        
        file_path = safe_resolve_path(EVENTS_HTML_DIR, f"{event_id}.html")
        if not file_path.exists():
            continue
            
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            html = f.read()
            
        fights, appearances = parse_event_html(
            html_content=html,
            event_id=event_id,
            default_title=event.get('title', ''),
            default_year=event.get('year', '')
        )
        
        for f in fights:
            all_fights.append(f.to_dict())
        for a in appearances:
            all_appearances.append(a.to_dict())
            
    df_fights = pd.DataFrame(all_fights)
    df_judge_fights = pd.DataFrame(all_appearances)
    
    # Save CSV files
    df_fights.to_csv(CSV_OUTPUT_PATH, index=False)
    df_judge_fights.to_csv(JUDGE_CSV_OUTPUT_PATH, index=False)
    
    # Save SQLite database with strict transactions
    conn = sqlite3.connect(DB_OUTPUT_PATH)
    try:
        init_database_schema(conn)
        df_fights.to_sql('fights', conn, if_exists='replace', index=False)
        df_judge_fights.to_sql('judge_appearances', conn, if_exists='replace', index=False)
        # Re-apply indexes after table replacement
        init_database_schema(conn)
    finally:
        conn.close()
        
    print(f"\nParsing Complete!")
    print(f"Total Fights Parsed: {len(df_fights)}")
    print(f"Total Judge-Fight Scorecard Records: {len(df_judge_fights)}")
    print(f"Unique Judges: {df_judge_fights['judge_name'].nunique()}")
    print(f"Persisted to {CSV_OUTPUT_PATH} and {DB_OUTPUT_PATH}")
    
    return df_fights, df_judge_fights


if __name__ == "__main__":
    parse_all_events()
