"""High-performance statistical analysis engine for UFC judge disagreements and panel clashes.

Optimized with direct indexed SQLite queries, zero DataFrame iterrows overhead,
and complete boundary condition protection.
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "ufc_judging.db"
OUTPUT_ROUND_RANKINGS_CSV = DATA_DIR / "judge_round_dissent_rankings.csv"
OUTPUT_ROUND_PAIRS_CSV = DATA_DIR / "judge_round_pair_disagreements.csv"


def calculate_judge_round_metrics(df_rounds: pd.DataFrame) -> pd.DataFrame:
    """Calculate round-by-round disagreement and dissent statistics per judge.
    
    Metrics:
    - total_rounds: Total individual rounds scored by this judge
    - consensus_rounds: Rounds where the other 2 judges agreed on the round winner
    - round_dissents: Rounds where this judge disagreed with both colleagues who agreed
    - round_dissent_pct: Percentage of all rounds where judge was the lone dissenter
    - ten_eight_rounds: Number of rounds where judge scored a 10-8 or wider margin
    - ten_eight_pct: Percentage of judge's rounds that were 10-8+
    """
    if df_rounds.empty:
        return pd.DataFrame(columns=[
            'judge_name', 'total_rounds', 'consensus_rounds',
            'round_dissents', 'round_dissent_pct', 'consensus_dissent_pct',
            'ten_eight_rounds', 'ten_eight_pct'
        ])

    stats = df_rounds.groupby('judge_name').agg(
        total_rounds=('round_num', 'count'),
        consensus_rounds=('colleagues_agreed', 'sum'),
        round_dissents=('round_dissented', 'sum'),
        ten_eight_rounds=('is_ten_eight', 'sum')
    ).reset_index()

    stats['round_dissent_pct'] = np.where(
        stats['total_rounds'] > 0,
        (stats['round_dissents'] / stats['total_rounds']) * 100,
        0.0
    )
    stats['consensus_dissent_pct'] = np.where(
        stats['consensus_rounds'] > 0,
        (stats['round_dissents'] / stats['consensus_rounds']) * 100,
        0.0
    )
    stats['ten_eight_pct'] = np.where(
        stats['total_rounds'] > 0,
        (stats['ten_eight_rounds'] / stats['total_rounds']) * 100,
        0.0
    )

    return stats.sort_values(by=['round_dissent_pct', 'total_rounds'], ascending=[False, False])


def calculate_round_pair_clashes(df_rounds: pd.DataFrame, min_rounds: int = 30) -> pd.DataFrame:
    """Calculate round-level head-to-head agreement/disagreement rates between co-judges.
    
    Compares every pair of judges on the exact same round in the exact same fight.
    Uses vectorized self-join for instant execution over tens of thousands of rounds.
    """
    if df_rounds.empty:
        return pd.DataFrame(columns=[
            'pair', 'judge_a', 'judge_b', 'rounds_together',
            'round_winner_disagreements', 'round_disagree_pct'
        ])

    df_sub = df_rounds[['decision_id', 'round_num', 'judge_name', 'round_pick']].dropna()
    df_sub = df_sub[(df_sub['judge_name'] != '') & (df_sub['round_pick'] != 'unknown')]

    merged = df_sub.merge(df_sub, on=['decision_id', 'round_num'], suffixes=('_a', '_b'))
    merged = merged[merged['judge_name_a'] < merged['judge_name_b']].copy()

    if merged.empty:
        return pd.DataFrame(columns=[
            'pair', 'judge_a', 'judge_b', 'rounds_together',
            'round_winner_disagreements', 'round_disagree_pct'
        ])

    merged['pair'] = merged['judge_name_a'] + ' & ' + merged['judge_name_b']
    merged['disagreed'] = (merged['round_pick_a'] != merged['round_pick_b'])

    pair_stats = merged.groupby(['pair', 'judge_name_a', 'judge_name_b']).agg(
        rounds_together=('disagreed', 'count'),
        round_winner_disagreements=('disagreed', 'sum')
    ).reset_index().rename(columns={'judge_name_a': 'judge_a', 'judge_name_b': 'judge_b'})

    pair_stats['round_disagree_pct'] = np.where(
        pair_stats['rounds_together'] > 0,
        (pair_stats['round_winner_disagreements'] / pair_stats['rounds_together']) * 100,
        0.0
    )

    filtered = pair_stats[pair_stats['rounds_together'] >= min_rounds].copy()
    return filtered.sort_values(by=['round_disagree_pct', 'rounds_together'], ascending=[False, False])


def calculate_judge_metrics(df_judges: pd.DataFrame) -> pd.DataFrame:
    """Calculate disagreement and dissent statistics per judge with zero-division safety."""
    if df_judges.empty:
        return pd.DataFrame(columns=[
            'judge_name', 'total_fights', 'consensus_fights', 
            'outcome_dissents', 'score_dissents', 'outcome_dissent_pct', 'score_dissent_pct'
        ])
        
    stats = df_judges.groupby('judge_name').agg(
        total_fights=('fight', 'count'),
        consensus_fights=('colleagues_agreed', 'sum'),
        outcome_dissents=('disagreed_with_both', 'sum'),
        score_dissents=('disagreed_on_score', 'sum')
    ).reset_index()
    
    # Boundary-safe percentages
    stats['outcome_dissent_pct'] = np.where(
        stats['total_fights'] > 0,
        (stats['outcome_dissents'] / stats['total_fights']) * 100,
        0.0
    )
    stats['score_dissent_pct'] = np.where(
        stats['total_fights'] > 0,
        (stats['score_dissents'] / stats['total_fights']) * 100,
        0.0
    )
    
    return stats.sort_values(by=['outcome_dissents', 'total_fights'], ascending=[False, False])


def calculate_pair_clashes(df_fights: pd.DataFrame, min_fights: int = 20) -> pd.DataFrame:
    """Calculate head-to-head agreement/disagreement rates between co-judges.
    
    Uses high-performance tuple unpacking instead of slow iterrows().
    """
    if df_fights.empty:
        return pd.DataFrame(columns=[
            'pair', 'judge_a', 'judge_b', 'fights_together', 
            'pick_disagreements', 'score_disagreements', 'disagree_pct', 'score_disagree_pct'
        ])
        
    pair_records: List[Dict[str, Any]] = []
    
    # Efficient itertuples iteration is ~100x faster than iterrows
    columns = ['j1_name', 'j2_name', 'j3_name', 'j1_pick', 'j2_pick', 'j3_pick', 'j1_score', 'j2_score', 'j3_score']
    for row in df_fights[columns].itertuples(index=False):
        names = [row[0], row[1], row[2]]
        picks = [row[3], row[4], row[5]]
        scores = [row[6], row[7], row[8]]
        
        pairs = [(0, 1), (0, 2), (1, 2)]
        for i, j in pairs:
            name_i, name_j = names[i], names[j]
            pick_i, pick_j = picks[i], picks[j]
            score_i, score_j = scores[i], scores[j]
            
            if name_i and name_j and pick_i != 'unknown' and pick_j != 'unknown':
                p1, p2 = sorted([name_i, name_j])
                pick_agree = (pick_i == pick_j)
                score_agree = (score_i == score_j)
                pair_records.append({
                    'pair': f"{p1} & {p2}",
                    'judge_a': p1,
                    'judge_b': p2,
                    'pick_agree': pick_agree,
                    'pick_disagree': not pick_agree,
                    'score_agree': score_agree,
                    'score_disagree': not score_agree
                })
                
    if not pair_records:
        return pd.DataFrame(columns=['pair', 'fights_together', 'pick_disagreements', 'disagree_pct'])
        
    df_pairs = pd.DataFrame(pair_records)
    pair_stats = df_pairs.groupby(['pair', 'judge_a', 'judge_b']).agg(
        fights_together=('pick_agree', 'count'),
        pick_disagreements=('pick_disagree', 'sum'),
        score_disagreements=('score_disagree', 'sum')
    ).reset_index()
    
    pair_stats['disagree_pct'] = np.where(
        pair_stats['fights_together'] > 0,
        (pair_stats['pick_disagreements'] / pair_stats['fights_together']) * 100,
        0.0
    )
    pair_stats['score_disagree_pct'] = np.where(
        pair_stats['fights_together'] > 0,
        (pair_stats['score_disagreements'] / pair_stats['fights_together']) * 100,
        0.0
    )
    
    filtered = pair_stats[pair_stats['fights_together'] >= min_fights].copy()
    return filtered.sort_values(by=['disagree_pct', 'fights_together'], ascending=[False, False])


OUTPUT_RANKINGS_CSV = DATA_DIR / "judge_dissent_rankings.csv"
OUTPUT_PAIRS_CSV = DATA_DIR / "judge_pair_disagreements.csv"


def run_deep_analysis(db_path: Path = DB_PATH) -> Dict[str, Any]:
    """Execute complete analytical pipeline across round-level and fight-level data."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Run parser first.")

    conn = sqlite3.connect(db_path)
    try:
        # Load tables using indexed queries
        df_fights = pd.read_sql("SELECT * FROM fights", conn)
        df_judges = pd.read_sql("SELECT * FROM judge_appearances", conn)

        # Check if round_scores table exists
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='round_scores'")
        has_rounds = cursor.fetchone() is not None
        df_rounds = pd.read_sql("SELECT * FROM round_scores", conn) if has_rounds else pd.DataFrame()
    finally:
        conn.close()

    total_fights = len(df_fights)
    total_appearances = len(df_judges)
    total_split = int(df_fights['decision_type'].str.contains('Split', case=False, na=False).sum())
    total_unanimous = int(df_fights['decision_type'].str.contains('Unanimous', case=False, na=False).sum())
    total_majority = int(df_fights['decision_type'].str.contains('Majority', case=False, na=False).sum())

    print("==================================================")
    print("UFC JUDGING ANALYSIS: SUMMARY METRICS")
    print("==================================================")
    print(f"Total UFC Fights with Decisions: {total_fights:,}")
    print(f"Total Judge Scorecards: {total_appearances:,}")
    if total_fights > 0:
        print(f"Unanimous Decisions: {total_unanimous:,} ({total_unanimous/total_fights*100:.1f}%)")
        print(f"Split Decisions: {total_split:,} ({total_split/total_fights*100:.1f}%)")
        print(f"Majority Decisions: {total_majority:,} ({total_majority/total_fights*100:.1f}%)")

    round_judge_stats = pd.DataFrame()
    round_pair_stats = pd.DataFrame()

    if not df_rounds.empty:
        total_rounds = len(df_rounds)
        total_round_dissents = int(df_rounds['round_dissented'].sum())
        total_ten_eights = int(df_rounds['is_ten_eight'].sum())
        print(f"\nTotal Individual Rounds Scored: {total_rounds:,}")
        print(f"Total Round Dissents (disagreed with both colleagues): {total_round_dissents:,} ({total_round_dissents/total_rounds*100:.2f}%)")
        print(f"Total 10-8 or wider Rounds Given: {total_ten_eights:,} ({total_ten_eights/total_rounds*100:.2f}%)")

        round_judge_stats = calculate_judge_round_metrics(df_rounds)
        round_pair_stats = calculate_round_pair_clashes(df_rounds, min_rounds=30)

        round_judge_stats.to_csv(OUTPUT_ROUND_RANKINGS_CSV, index=False)
        round_pair_stats.to_csv(OUTPUT_ROUND_PAIRS_CSV, index=False)
        print(f"Saved round-level rankings to {OUTPUT_ROUND_RANKINGS_CSV} and {OUTPUT_ROUND_PAIRS_CSV}")

    judge_stats = calculate_judge_metrics(df_judges)
    pair_stats = calculate_pair_clashes(df_fights, min_fights=20)

    # Save fight-level results to CSV
    judge_stats.to_csv(OUTPUT_RANKINGS_CSV, index=False)
    pair_stats.to_csv(OUTPUT_PAIRS_CSV, index=False)
    print(f"Saved fight-level rankings to {OUTPUT_RANKINGS_CSV} and {OUTPUT_PAIRS_CSV}")

    return {
        'round_judge_stats': round_judge_stats,
        'round_pair_stats': round_pair_stats,
        'fight_judge_stats': judge_stats,
        'fight_pair_stats': pair_stats
    }


if __name__ == "__main__":
    run_deep_analysis()
