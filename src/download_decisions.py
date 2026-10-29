"""High-concurrency downloader for UFC decision scorecards pages.

Downloads and caches all decision HTML pages locally into data/decisions_html/{decision_id}.html
with rate limiting, atomic writes, exponential backoff, and path sanitization.
"""

import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import contextlib

import pandas as pd
import requests
from tqdm import tqdm

from src.scraper import (
    DEFAULT_TIMEOUT,
    MAX_RETRIES,
    atomic_write_text,
    get_thread_session,
)
from src.security import safe_resolve_path, validate_numeric_id, validate_safe_url

logger = logging.getLogger(__name__)

DATA_DIR = PROJECT_ROOT / "data"
DECISIONS_HTML_DIR = DATA_DIR / "decisions_html"
SCORECARDS_CSV = DATA_DIR / "ufc_scorecards.csv"


def download_single_decision(item: tuple[int, str]) -> tuple[int, bool, str]:
    """Download and cache an individual decision page HTML with security checks."""
    decision_id, decision_url = item
    try:
        val_id = validate_numeric_id(decision_id, "decision_id")
        file_path = safe_resolve_path(DECISIONS_HTML_DIR, f"{val_id}.html")

        # Cache check (> 800 bytes is valid HTML for decision page)
        if file_path.exists() and file_path.stat().st_size > 800:
            return val_id, True, "cached"

        # Validate URL against SSRF and protocol manipulation
        safe_url = validate_safe_url(decision_url)

        session = get_thread_session()

        for attempt in range(MAX_RETRIES):
            try:
                resp = session.get(safe_url, timeout=DEFAULT_TIMEOUT)
                if resp.status_code == 200 and len(resp.text) > 800:
                    atomic_write_text(file_path, resp.text)
                    return val_id, True, "downloaded"
                elif resp.status_code == 404:
                    return val_id, False, "404 Not Found"
                time.sleep(0.3 * (2**attempt))
            except requests.RequestException as e:
                if attempt == MAX_RETRIES - 1:
                    return val_id, False, str(e)
                time.sleep(0.5 * (2**attempt))

        return val_id, False, "HTTP Failed"
    except (ValueError, OSError) as e:
        return decision_id, False, str(e)


def download_all_decisions(
    max_workers: int = 16, reverse: bool = False, start_idx: int = 0, end_idx: int | None = None
) -> tuple[int, int, int]:
    """Download HTML for all indexed decisions using a thread pool."""
    DECISIONS_HTML_DIR.mkdir(parents=True, exist_ok=True)

    if not SCORECARDS_CSV.exists():
        raise FileNotFoundError(f"Scorecards CSV not found at {SCORECARDS_CSV}")

    df = pd.read_csv(SCORECARDS_CSV)
    df_valid = df.dropna(subset=["decision_id", "decision_url"])
    items = [(int(row["decision_id"]), str(row["decision_url"])) for _, row in df_valid.iterrows()]
    if reverse:
        items.reverse()

    total_all = len(items)
    end = end_idx if end_idx is not None else total_all
    items = items[start_idx:end]

    order_str = "reversed order" if reverse else "standard order"
    logger.info(
        "Starting download/cache check for %d decision scorecards (range [%d:%s] of %d, workers=%d, %s)...",
        len(items),
        start_idx,
        str(end),
        total_all,
        max_workers,
        order_str,
    )

    success = 0
    cached = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_single_decision, item) for item in items]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Decisions"):
            did, ok, status = f.result()
            if ok:
                if status == "cached":
                    cached += 1
                else:
                    success += 1
            else:
                failed += 1
                if failed <= 10:
                    logger.warning("Failed decision %s: %s", did, status)

    logger.info("Finished: %d downloaded, %d cached, %d failed.", success, cached, failed)
    return success, cached, failed


if __name__ == "__main__":
    is_reverse = "--reverse" in sys.argv
    workers = 16
    start = 0
    end = None
    for arg in sys.argv:
        if arg.startswith("--workers="):
            with contextlib.suppress(ValueError):
                workers = int(arg.split("=")[1])
        elif arg.startswith("--start="):
            with contextlib.suppress(ValueError):
                start = int(arg.split("=")[1])
        elif arg.startswith("--end="):
            with contextlib.suppress(ValueError):
                end = int(arg.split("=")[1])
    download_all_decisions(max_workers=workers, reverse=is_reverse, start_idx=start, end_idx=end)
