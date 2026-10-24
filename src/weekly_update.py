"""Automated weekly update pipeline for UFC judging scorecards.

Checks mmadecisions.com for newly completed UFC events (typically from the weekend),
downloads any new decision and round scorecards, ingests them into the SQLite database
and CSVs, updates the statistical analysis, and recompiles the standalone dashboard.
"""

import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from bs4 import BeautifulSoup

from src.analyzer import run_deep_analysis
from src.build_dashboard import build_dashboard_html
from src.download_decisions import download_single_decision
from src.export_web_data import export_web_data
from src.parser import parse_event_html, clean_judge_name
from src.round_parser import parse_decision_rounds, save_round_scores
from src.scraper import (
    atomic_write_text,
    fetch_events_for_year,
    get_thread_session,
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
)
from src.security import safe_resolve_path, validate_numeric_id
from src.visualizer import generate_visualizations

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
EVENTS_HTML_DIR = DATA_DIR / "events_html"
EVENTS_JSON_PATH = DATA_DIR / "ufc_events.json"
DECISIONS_HTML_DIR = DATA_DIR / "decisions_html"
SCORECARDS_CSV = DATA_DIR / "ufc_scorecards.csv"
APPEARANCES_CSV = DATA_DIR / "ufc_judge_appearances.csv"
ROUND_SCORES_CSV = DATA_DIR / "ufc_round_scores.csv"
DB_PATH = DATA_DIR / "ufc_judging.db"


def fetch_new_events(target_years: Optional[List[int]] = None) -> List[Dict[str, str]]:
    """Check archive for recent events and download new ones."""
    if target_years is None:
        curr_year = datetime.now().year
        target_years = [curr_year, curr_year - 1]

    existing_events: List[Dict[str, str]] = []
    if EVENTS_JSON_PATH.exists():
        try:
            with open(EVENTS_JSON_PATH, "r", encoding="utf-8") as f:
                existing_events = json.load(f)
        except Exception as e:
            logger.warning("Could not read %s: %s", EVENTS_JSON_PATH, e)

    existing_ids: Set[str] = {str(e.get("event_id")) for e in existing_events if e.get("event_id")}

    new_events_found: List[Dict[str, str]] = []
    session = get_thread_session()

    for year in target_years:
        logger.info("Scanning mmadecisions archive for year %d...", year)
        scraped_events = fetch_events_for_year(str(year))
        for ev in scraped_events:
            ev_id = str(ev.get("event_id"))
            ev_file = EVENTS_HTML_DIR / f"{ev_id}.html"

            # Check if event is new or needs download
            if ev_id not in existing_ids or not ev_file.exists() or ev_file.stat().st_size < 500:
                logger.info("Discovered new/updated UFC event: %s (ID: %s)", ev.get("title"), ev_id)
                new_events_found.append(ev)
                existing_events.append(ev)
                existing_ids.add(ev_id)

                # Download event HTML
                try:
                    resp = session.get(ev["url"], timeout=DEFAULT_TIMEOUT)
                    if resp.status_code == 200:
                        atomic_write_text(ev_file, resp.text)
                except Exception as ex:
                    logger.warning("Failed downloading event %s: %s", ev_id, ex)

    # Save updated ufc_events.json
    if new_events_found:
        atomic_write_text(EVENTS_JSON_PATH, json.dumps(existing_events, indent=2))
        logger.info("Added %d new events to %s", len(new_events_found), EVENTS_JSON_PATH)
    else:
        logger.info("No new UFC events detected in mmadecisions archive.")

    return new_events_found


def ingest_new_decisions_and_rounds(new_events: List[Dict[str, str]], force: bool = False) -> Tuple[int, int]:
    """Parse new decisions and their round-by-round tables into the database.
    
    If new_events is empty and force is False, returns (0, 0) immediately.
    """
    EVENTS_HTML_DIR.mkdir(parents=True, exist_ok=True)
    DECISIONS_HTML_DIR.mkdir(parents=True, exist_ok=True)

    if not new_events and not force:
        return 0, 0

    # 1. Load existing decisions & round scores
    existing_dec_ids: Set[str] = set()
    if SCORECARDS_CSV.exists():
        try:
            df_existing = pd.read_csv(SCORECARDS_CSV, usecols=["decision_id"])
            existing_dec_ids = set(df_existing["decision_id"].astype(str))
        except Exception as e:
            logger.warning("Could not load %s: %s", SCORECARDS_CSV, e)

    # 2. Only parse event HTML files for the newly discovered events (or all if force)
    if force:
        target_event_files = list(EVENTS_HTML_DIR.glob("*.html"))
    else:
        target_event_files = [
            EVENTS_HTML_DIR / f"{ev['event_id']}.html"
            for ev in new_events
            if (EVENTS_HTML_DIR / f"{ev['event_id']}.html").exists()
        ]

    all_new_fights: List[Any] = []
    all_new_appearances: List[Any] = []

    for ev_path in target_event_files:
        try:
            content = ev_path.read_text(encoding="utf-8", errors="replace")
            event_id = ev_path.stem
            fights, appearances = parse_event_html(content, event_id)
            for f in fights:
                if str(f.decision_id) not in existing_dec_ids:
                    all_new_fights.append(f)
            all_new_appearances.extend(appearances)
        except Exception as ex:
            logger.warning("Error parsing event HTML %s: %s", ev_path, ex)

    logger.info("Identified %d new fights/decisions to process.", len(all_new_fights))

    if not all_new_fights and not force:
        return 0, 0

    # 3. Download decision pages for new fights
    new_decisions_to_dl = [(f.decision_id, f.decision_url) for f in all_new_fights]
    downloaded_count = 0
    for item in new_decisions_to_dl:
        _, success, reason = download_single_decision(item)
        if success and reason == "downloaded":
            downloaded_count += 1

    if downloaded_count:
        logger.info("Downloaded %d new decision HTML pages.", downloaded_count)

    # 4. Extract round scores for newly downloaded decisions
    new_round_scores: List[Any] = []
    meta_map = {
        str(f.decision_id): {
            'event_id': str(f.event_id),
            'event_title': f.event_name,
            'event_date': str(f.event_date),
            'event_year': int(f.event_year) if f.event_year else datetime.now().year,
            'decision_type': f.decision_type,
            'fighter_1': f.fighter_1,
            'fighter_2': f.fighter_2,
        }
        for f in all_new_fights
    }

    for f in all_new_fights:
        dec_file = DECISIONS_HTML_DIR / f"{f.decision_id}.html"
        if dec_file.exists():
            try:
                html_text = dec_file.read_text(encoding="utf-8", errors="replace")
                scores = parse_decision_rounds(html_text, str(f.decision_id), meta_map.get(str(f.decision_id), {}))
                if scores:
                    new_round_scores.extend(scores)
            except Exception as e:
                logger.warning("Failed parsing rounds for decision %s: %s", f.decision_id, e)

    # 5. Append new records to CSV and SQLite
    if all_new_fights:
        df_new_fights = pd.DataFrame([f.to_dict() for f in all_new_fights])
        df_new_fights.to_csv(SCORECARDS_CSV, mode="a", header=not SCORECARDS_CSV.exists(), index=False)
        
        # Append to SQLite fights table
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        df_new_fights.to_sql("fights", conn, if_exists="append", index=False)
        conn.close()

    if all_new_appearances:
        df_new_app = pd.DataFrame([a.to_dict() for a in all_new_appearances])
        df_new_app.to_csv(APPEARANCES_CSV, mode="a", header=not APPEARANCES_CSV.exists(), index=False)
        
        # Append to SQLite appearances table
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        df_new_app.to_sql("judge_appearances", conn, if_exists="append", index=False)
        conn.close()

    if new_round_scores:
        df_new_rounds = pd.DataFrame([s.to_dict() for s in new_round_scores])
        df_new_rounds.to_csv(ROUND_SCORES_CSV, mode="a", header=not ROUND_SCORES_CSV.exists(), index=False)

        # Append to SQLite round_scores table
        import sqlite3
        conn = sqlite3.connect(str(DB_PATH))
        df_new_rounds.to_sql("round_scores", conn, if_exists="append", index=False)
        conn.close()

    return len(all_new_fights), len(new_round_scores)


def run_weekly_pipeline(force: bool = False) -> Dict[str, Any]:
    """Execute the complete weekly update pipeline.
    
    Returns a summary dictionary of updates performed.
    """
    logger.info("=== Starting Weekly UFC Judging Data Update ===")
    start_time = datetime.now()

    new_events = fetch_new_events()
    new_fights_count, new_rounds_count = ingest_new_decisions_and_rounds(new_events, force=force)

    has_changes = (len(new_events) > 0 or new_fights_count > 0 or new_rounds_count > 0 or force)

    if not has_changes:
        logger.info("✓ Everything up to date. No new events or rounds to ingest.")
        return {
            "status": "up_to_date",
            "new_events": 0,
            "new_fights": 0,
            "new_rounds": 0,
            "duration_seconds": (datetime.now() - start_time).total_seconds(),
        }

    logger.info("Changes detected! Recomputing analytics and visualisations...")
    # Re-run statistical analyzer
    run_deep_analysis()

    # Re-generate charts
    generate_visualizations()

    # Export enriched web data JSON
    export_web_data()

    # Recompile standalone dashboard HTML
    build_dashboard_html()

    duration = (datetime.now() - start_time).total_seconds()
    logger.info("=== Weekly Update Complete in %.2f seconds! ===", duration)

    return {
        "status": "updated",
        "new_events": len(new_events),
        "new_fights": new_fights_count,
        "new_rounds": new_rounds_count,
        "duration_seconds": duration,
    }


if __name__ == "__main__":
    force_update = "--force" in sys.argv
    result = run_weekly_pipeline(force=force_update)
    print(json.dumps(result, indent=2))
