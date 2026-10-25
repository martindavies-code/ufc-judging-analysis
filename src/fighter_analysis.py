"""Fighter-centric controversy and decision disagreement analytics for UFC bouts.

Analyzes how often individual fighters are involved in split decisions,
majority decisions, and dissented rounds. Measures fighter 'luck' (net split differential),
contested rounds percentage, and identifies historical patterns of judges' discord.
"""

import json
import logging
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, TypedDict


class FighterStats(TypedDict):
    total_fights: int
    split_fights: int
    majority_fights: int
    unanimous_fights: int
    split_wins: int
    split_losses: int
    split_draws: int
    total_rounds: int
    contested_rounds: int
    first_year: int
    last_year: int
    fights_list: list[dict[str, Any]]


import pandas as pd

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "ufc_judging.db"
DECISIONS_HTML_DIR = DATA_DIR / "decisions_html"
FIGHTER_NAMES_CACHE = DATA_DIR / "decision_fighter_names.json"


def get_decision_fighter_names(
    decisions_dir: Path = DECISIONS_HTML_DIR, cache_path: Path = FIGHTER_NAMES_CACHE, force_refresh: bool = False
) -> dict[str, tuple[str, str]]:
    """Extract or load canonical full fighter names from decision HTML headers.

    Reads binary chunks to quickly parse HTML <title> without overhead.
    Caches the results to JSON for instant sub-millisecond retrieval.
    """
    names_map: dict[str, tuple[str, str]] = {}
    if not force_refresh and cache_path.exists():
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                names_map = {k: (v[0], v[1]) for k, v in data.items()}
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError, TypeError) as e:
            logger.warning(f"Error reading fighter names cache: {e}. Rebuilding...")
            names_map = {}

    if not decisions_dir.exists():
        return names_map

    all_files = [f for f in os.listdir(decisions_dir) if f.endswith(".html")]
    missing_files = [f for f in all_files if f[:-5] not in names_map]
    if not missing_files and names_map:
        return names_map

    from concurrent.futures import ThreadPoolExecutor

    title_re = re.compile(r"<title>(.*?)</title>", re.IGNORECASE)

    def _read_file_title(fname: str) -> tuple[str | None, tuple[str, str] | None]:
        if not fname.endswith(".html"):
            return None, None
        fpath = decisions_dir / fname
        try:
            with open(fpath, "rb") as f:
                head = f.read(600)
            text = head.decode("latin1", errors="ignore")
            m = title_re.search(text)
            if m:
                clean = m.group(1).replace("&nbsp;", " ").replace("&#160;", " ")
                clean = " ".join(clean.split())
                fight_part = clean.split("::")[0].strip()
                for sep in (" def. ", " drew with ", " vs. ", " vs "):
                    if sep in fight_part:
                        p = fight_part.split(sep, 1)
                        f1, f2 = p[0].strip(), p[1].strip()
                        if f1 and f2:
                            return fname[:-5], (f1, f2)
        except (OSError, UnicodeDecodeError) as err:
            logger.debug("Failed reading title from %s: %s", fname, err)
        return None, None

    with ThreadPoolExecutor(max_workers=16) as ex:
        results = list(ex.map(_read_file_title, missing_files))

    for dec_id, names in results:
        if dec_id and names:
            names_map[dec_id] = names

    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(names_map, f, indent=2)
    except (OSError, TypeError) as e:
        logger.warning(f"Failed to cache fighter names to {cache_path}: {e}")

    return names_map


def calculate_fighter_metrics(
    df_fights: pd.DataFrame, df_rounds: pd.DataFrame, names_map: dict[str, tuple[str, str]] | None = None
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Compute comprehensive controversy and split-decision metrics per fighter.

    Returns:
        fighters_list: Array of fighter dictionaries sorted by total fights and split fights.
        summary_kpis: High-level insights (most unlucky, most fortunate, highest split rate).
    """
    if df_fights.empty:
        return [], {}

    if names_map is None:
        names_map = get_decision_fighter_names()

    # Pre-calculate contested rounds per decision
    total_rounds_by_dec: dict[str, int] = defaultdict(int)
    contested_rounds_by_dec: dict[str, int] = defaultdict(int)

    if not df_rounds.empty:
        scored_rounds = df_rounds.groupby(["decision_id", "round_num"])["round_dissented"].max().reset_index()
        for r in scored_rounds.itertuples():
            did = str(r.decision_id)
            total_rounds_by_dec[did] += 1
            if r.round_dissented == 1:
                contested_rounds_by_dec[did] += 1

    fighters: dict[str, FighterStats] = defaultdict(
        lambda: FighterStats(
            total_fights=0,
            split_fights=0,
            majority_fights=0,
            unanimous_fights=0,
            split_wins=0,
            split_losses=0,
            split_draws=0,
            total_rounds=0,
            contested_rounds=0,
            first_year=9999,
            last_year=0,
            fights_list=[],
        )
    )

    for r in df_fights.itertuples():
        dec_id = str(r.decision_id)
        if dec_id in names_map:
            f1, f2 = names_map[dec_id]
        else:
            f1 = str(getattr(r, "fighter_1", ""))
            f2 = str(getattr(r, "fighter_2", ""))

        if not f1 or not f2:
            continue

        year_str = str(getattr(r, "event_year", ""))
        year = int(year_str) if year_str.isdigit() else 2020
        dec_type = str(r.decision_type or "")
        is_split = "Split" in dec_type
        is_majority = "Majority" in dec_type

        rds = total_rounds_by_dec.get(dec_id, 3)
        c_rds = contested_rounds_by_dec.get(dec_id, 0)

        # Fighter 1 (winner in 'def' or first participant in draw)
        d1 = fighters[f1]
        d1["total_fights"] += 1
        d1["total_rounds"] += rds
        d1["contested_rounds"] += c_rds
        d1["first_year"] = min(d1["first_year"], year)
        d1["last_year"] = max(d1["last_year"], year)
        if is_split:
            d1["split_fights"] += 1
            if r.outcome == "def":
                d1["split_wins"] += 1
            else:
                d1["split_draws"] += 1
        elif is_majority:
            d1["majority_fights"] += 1
        else:
            d1["unanimous_fights"] += 1

        d1["fights_list"].append(
            {
                "opponent": f2,
                "year": year,
                "result": "Win" if r.outcome == "def" else "Draw",
                "type": dec_type,
                "event": getattr(r, "event_title", None) or getattr(r, "fight", f"{f1} vs {f2}"),
                "decision_id": dec_id,
            }
        )

        # Fighter 2 (loser in 'def' or second participant in draw)
        d2 = fighters[f2]
        d2["total_fights"] += 1
        d2["total_rounds"] += rds
        d2["contested_rounds"] += c_rds
        d2["first_year"] = min(d2["first_year"], year)
        d2["last_year"] = max(d2["last_year"], year)
        if is_split:
            d2["split_fights"] += 1
            if r.outcome == "def":
                d2["split_losses"] += 1
            else:
                d2["split_draws"] += 1
        elif is_majority:
            d2["majority_fights"] += 1
        else:
            d2["unanimous_fights"] += 1

        d2["fights_list"].append(
            {
                "opponent": f1,
                "year": year,
                "result": "Loss" if r.outcome == "def" else "Draw",
                "type": dec_type,
                "event": getattr(r, "event_title", None) or getattr(r, "fight", f"{f1} vs {f2}"),
                "decision_id": dec_id,
            }
        )

    fighter_records: list[dict[str, Any]] = []
    for name, d in fighters.items():
        if d["total_fights"] < 1:
            continue

        disagreed_fights = d["split_fights"] + d["majority_fights"]
        split_pct = round((d["split_fights"] / d["total_fights"]) * 100, 2)
        disagreed_pct = round((disagreed_fights / d["total_fights"]) * 100, 2)
        contested_round_pct = round((d["contested_rounds"] / max(1, d["total_rounds"])) * 100, 2)
        net_split_diff = d["split_wins"] - d["split_losses"]

        # Determine fortune classification
        if d["split_fights"] >= 2:
            if net_split_diff <= -2:
                luck_badge = "Unlucky"
            elif net_split_diff >= 2:
                luck_badge = "Fortunate"
            else:
                luck_badge = "Even"
        else:
            luck_badge = "Neutral"

        # Prioritize split and majority fights for display
        close_fights = [f for f in d["fights_list"] if "Split" in f["type"] or "Majority" in f["type"]]
        other_fights = [f for f in d["fights_list"] if "Split" not in f["type"] and "Majority" not in f["type"]]
        sample_fights = (close_fights + other_fights)[:8]

        fighter_records.append(
            {
                "fighter_name": name,
                "total_fights": d["total_fights"],
                "split_fights": d["split_fights"],
                "split_pct": split_pct,
                "majority_fights": d["majority_fights"],
                "disagreed_fights": disagreed_fights,
                "disagreed_pct": disagreed_pct,
                "unanimous_fights": d["unanimous_fights"],
                "split_wins": d["split_wins"],
                "split_losses": d["split_losses"],
                "split_draws": d["split_draws"],
                "net_split_diff": net_split_diff,
                "luck_badge": luck_badge,
                "total_rounds": d["total_rounds"],
                "contested_rounds": d["contested_rounds"],
                "contested_round_pct": contested_round_pct,
                "first_year": d["first_year"] if d["first_year"] != 9999 else 2000,
                "last_year": d["last_year"] if d["last_year"] != 0 else 2026,
                "sample_close_fights": sample_fights,
            }
        )

    # Sort descending by split decisions and total fights
    fighter_records.sort(key=lambda x: (x["split_fights"], x["total_fights"], x["split_pct"]), reverse=True)

    # Derive high-impact narrative KPIs
    df_f = pd.DataFrame(fighter_records)

    # 1. Fighter with highest split decision % (minimum 6 decisions to avoid 1-fight outliers)
    qual_pct = df_f[df_f["total_fights"] >= 6]
    top_split_pct_f = (
        qual_pct.sort_values(by=["split_pct", "total_fights"], ascending=[False, False]).iloc[0].to_dict()
        if not qual_pct.empty
        else {}
    )

    # 2. Most Unlucky: Fighter with most split losses / lowest net differential
    qual_losses = df_f[df_f["total_fights"] >= 4]
    most_unlucky_f = (
        qual_losses.sort_values(by=["split_losses", "net_split_diff"], ascending=[False, True]).iloc[0].to_dict()
        if not qual_losses.empty
        else {}
    )

    # 3. Most Fortunate: Fighter with most split wins / highest net differential
    qual_wins = df_f[df_f["total_fights"] >= 4]
    most_fortunate_f = (
        qual_wins.sort_values(by=["split_wins", "net_split_diff"], ascending=[False, False]).iloc[0].to_dict()
        if not qual_wins.empty
        else {}
    )

    # 4. Most Contested Rounds (minimum 25 rounds)
    qual_rounds = df_f[df_f["total_rounds"] >= 25]
    top_contested_rounds_f = (
        qual_rounds.sort_values(by=["contested_round_pct", "total_rounds"], ascending=[False, False]).iloc[0].to_dict()
        if not qual_rounds.empty
        else {}
    )

    summary_kpis = {
        "total_fighters": len(fighter_records),
        "top_split_pct_fighter": top_split_pct_f,
        "most_unlucky_fighter": most_unlucky_f,
        "most_fortunate_fighter": most_fortunate_f,
        "top_contested_rounds_fighter": top_contested_rounds_f,
        "overall_split_decision_rate": round(
            (int(df_fights["decision_type"].str.contains("Split", case=False, na=False).sum()) / len(df_fights)) * 100,
            2,
        ),
    }

    return fighter_records, summary_kpis
