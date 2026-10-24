"""Export verified judging aggregations to JSON format for web dashboard consumption."""

import json
import logging
import sqlite3
import sys
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
DB_PATH = DATA_DIR / "ufc_judging.db"
PAIRS_CSV = DATA_DIR / "judge_pair_disagreements.csv"
OUTPUT_JSON_PATH = OUTPUT_DIR / "ufc_judging_data.json"


def export_web_data(db_path: Path = DB_PATH) -> Path:
    """Generate sanitized JSON payload containing summary, rankings, and round-level data."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database {db_path} does not exist. Run parser first.")

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA busy_timeout = 5000")
        df_fights = pd.read_sql("SELECT * FROM fights", conn)
        df_judges = pd.read_sql("SELECT * FROM judge_appearances", conn)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='round_scores'")
        has_rounds = cursor.fetchone() is not None
        df_rounds = pd.read_sql("SELECT * FROM round_scores", conn) if has_rounds else pd.DataFrame()
    finally:
        conn.close()

    total_fights = len(df_fights)
    total_scorecards = len(df_judges)

    # Fight-level judge stats
    if df_judges.empty:
        stats_list: List[Dict[str, Any]] = []
        unique_judges = 0
    else:
        stats = df_judges.groupby('judge_name').agg(
            total_fights=('fight', 'count'),
            dissents=('disagreed_with_both', 'sum'),
            score_dissents=('disagreed_on_score', 'sum'),
            unanimous_fights=('decision_type', lambda s: s.str.contains('Unanimous', case=False, na=False).sum()),
            split_fights=('decision_type', lambda s: s.str.contains('Split', case=False, na=False).sum()),
            first_year=('event_year', 'min'),
            last_year=('event_year', 'max')
        ).reset_index()

        stats['dissent_pct'] = ((stats['dissents'] / stats['total_fights']) * 100).round(2)
        stats['score_dissent_pct'] = ((stats['score_dissents'] / stats['total_fights']) * 100).round(2)
        stats['unanimous_pct'] = ((stats['unanimous_fights'] / stats['total_fights']) * 100).round(2)
        stats['first_year'] = pd.to_numeric(stats['first_year'], errors='coerce').fillna(1995).astype(int)
        stats['last_year'] = pd.to_numeric(stats['last_year'], errors='coerce').fillna(2026).astype(int)

        stats_list = stats.sort_values(by=['total_fights', 'dissents'], ascending=[False, False]).to_dict(orient='records')
        unique_judges = int(stats['judge_name'].nunique())

    # Round-level judge stats
    round_judges_list: List[Dict[str, Any]] = []
    round_pairs_list: List[Dict[str, Any]] = []
    recent_round_dissents: List[Dict[str, Any]] = []
    round_summary: Dict[str, Any] = {}

    if not df_rounds.empty:
        from src.analyzer import calculate_judge_round_metrics, calculate_round_pair_clashes
        round_stats = calculate_judge_round_metrics(df_rounds)
        round_stats['round_dissent_pct'] = round_stats['round_dissent_pct'].round(2)
        round_stats['consensus_dissent_pct'] = round_stats['consensus_dissent_pct'].round(2)
        round_stats['ten_eight_pct'] = round_stats['ten_eight_pct'].round(2)

        # Calculate era per judge
        era_dict = {}
        for r in df_rounds[['judge_name', 'event_year']].dropna().itertuples(index=False):
            jname, eyear = r[0], str(r[1])
            if eyear.isdigit():
                y = int(eyear)
                if jname not in era_dict:
                    era_dict[jname] = [y, y]
                else:
                    era_dict[jname][0] = min(era_dict[jname][0], y)
                    era_dict[jname][1] = max(era_dict[jname][1], y)

        round_pairs = calculate_round_pair_clashes(df_rounds, min_rounds=15)
        round_pairs['round_disagree_pct'] = round_pairs['round_disagree_pct'].round(2)
        round_pairs_list = round_pairs.head(50).to_dict(orient='records')

        # Find top clash partner for each judge
        top_clash_map: Dict[str, Dict[str, Any]] = {}
        for p in round_pairs.itertuples(index=False):
            ja, jb, pct, rds = p.judge_a, p.judge_b, p.round_disagree_pct, p.rounds_together
            if ja not in top_clash_map or pct > top_clash_map[ja]['pct']:
                top_clash_map[ja] = {'partner': jb, 'pct': pct, 'rounds': rds}
            if jb not in top_clash_map or pct > top_clash_map[jb]['pct']:
                top_clash_map[jb] = {'partner': ja, 'pct': pct, 'rounds': rds}

        # Build sample dissents per judge
        dissents_by_judge: Dict[str, List[Dict[str, Any]]] = {}
        df_diss = df_rounds[df_rounds['round_dissented'] == 1]
        for row in df_diss.itertuples(index=False):
            jname = row.judge_name
            if jname not in dissents_by_judge:
                dissents_by_judge[jname] = []
            if len(dissents_by_judge[jname]) < 4:
                dissents_by_judge[jname].append({
                    'fight': row.fight,
                    'year': row.event_year,
                    'round': row.round_num,
                    'score': f"{row.score_f1}-{row.score_f2}",
                    'pick': row.round_pick,
                    'c1': row.colleague_1,
                    'c2': row.colleague_2
                })

        # Enrich round_judges_list
        enriched_judges = []
        for j in round_stats.to_dict(orient='records'):
            jname = j['judge_name']
            era = era_dict.get(jname, [1995, 2026])
            clash = top_clash_map.get(jname, {})
            j['first_year'] = era[0]
            j['last_year'] = era[1]
            j['top_clash_partner'] = clash.get('partner', 'None recorded')
            j['top_clash_pct'] = clash.get('pct', 0.0)
            j['top_clash_rounds'] = clash.get('rounds', 0)
            j['sample_dissents'] = dissents_by_judge.get(jname, [])
            enriched_judges.append(j)

        round_judges_list = enriched_judges

        total_rounds = len(df_rounds)
        total_round_dissents = int(df_rounds['round_dissented'].sum())
        total_ten_eight = int(df_rounds['is_ten_eight'].sum())

        diff = (df_rounds['score_f1'] - df_rounds['score_f2']).abs()
        round_summary = {
            'total_rounds': total_rounds,
            'total_round_dissents': total_round_dissents,
            'round_dissent_pct': round((total_round_dissents / total_rounds) * 100, 2) if total_rounds > 0 else 0.0,
            'total_ten_eight': total_ten_eight,
            'ten_eight_pct': round((total_ten_eight / total_rounds) * 100, 2) if total_rounds > 0 else 0.0,
            'score_distribution': {
                'ten_nine': int((diff == 1).sum()),
                'ten_eight': int((diff == 2).sum()),
                'ten_seven_plus': int((diff >= 3).sum()),
                'draws': int((diff == 0).sum())
            }
        }

        # Recent round dissents sample
        dissented_rounds = df_rounds[df_rounds['round_dissented'] == 1].copy()
        if not dissented_rounds.empty:
            cols = ['decision_id', 'event_year', 'fight', 'round_num', 'judge_name', 'score_f1', 'score_f2', 'round_pick', 'colleague_1', 'colleague_2']
            avail = [c for c in cols if c in dissented_rounds.columns]
            recent_round_dissents = dissented_rounds[avail].head(150).to_dict(orient='records')

    # Read pair clashes (fight level)
    if PAIRS_CSV.exists():
        df_pairs = pd.read_csv(PAIRS_CSV)
        pair_list = df_pairs[df_pairs['fights_together'] >= 20].sort_values(
            by='disagree_pct', ascending=False
        ).head(30).to_dict(orient='records')
    else:
        pair_list = []

    # Recent split dissents (fight level)
    if not df_fights.empty and 'has_dissenter' in df_fights.columns:
        split_fights = df_fights[df_fights['has_dissenter'] == 1].copy()
        split_cols = [
            'event_title', 'event_date', 'fight', 'decision_type',
            'dissenter_judge_name', 'j1_name', 'j1_score',
            'j2_name', 'j2_score', 'j3_name', 'j3_score', 'decision_url'
        ]
        available_cols = [c for c in split_cols if c in split_fights.columns]
        split_sample = split_fights[available_cols].sort_values(by='event_date', ascending=False).head(100).to_dict(orient='records')
    else:
        split_sample = []

    unanimous_count = int(df_fights['decision_type'].str.contains('Unanimous', case=False, na=False).sum()) if not df_fights.empty else 0
    split_count = int(df_fights['decision_type'].str.contains('Split', case=False, na=False).sum()) if not df_fights.empty else 0
    majority_count = int(df_fights['decision_type'].str.contains('Majority', case=False, na=False).sum()) if not df_fights.empty else 0

    web_payload = {
        'summary': {
            'total_fights': total_fights,
            'total_scorecards': total_scorecards,
            'total_judges': unique_judges,
            'unanimous_count': unanimous_count,
            'split_count': split_count,
            'majority_count': majority_count,
            'rounds': round_summary
        },
        'round_judges': round_judges_list,
        'round_pairs': round_pairs_list,
        'recent_round_dissents': recent_round_dissents,
        'judges': stats_list,
        'pairs': pair_list,
        'recent_dissents': split_sample
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    temp_json = OUTPUT_JSON_PATH.with_suffix(".tmp")
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(web_payload, f, indent=2)
    temp_json.replace(OUTPUT_JSON_PATH)

    print(f"Exported web data with {len(round_judges_list)} round judges and {len(stats_list)} fight judges to {OUTPUT_JSON_PATH}")
    return OUTPUT_JSON_PATH


if __name__ == "__main__":
    export_web_data()
