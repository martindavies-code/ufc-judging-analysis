"""Resilient, thread-safe web scraper for UFC scorecards archive.

Implements exponential backoff, atomic file caching, thread-local connection pools,
and strict path sanitization.
"""

import contextlib
import json
import logging
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import cast

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

from src.security import (
    safe_resolve_path,
    sanitize_filename,
    validate_numeric_id,
    validate_safe_url,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://mmadecisions.com"
DEFAULT_TIMEOUT = 15.0
MAX_RETRIES = 3
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_HTML_DIR = DATA_DIR / "events_html"
EVENTS_JSON_PATH = DATA_DIR / "ufc_events.json"

# Thread-local storage ensures each worker thread has an isolated requests.Session
_thread_local = threading.local()


def get_thread_session() -> requests.Session:
    """Return a thread-isolated requests.Session instance."""
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        session.headers.update(DEFAULT_HEADERS)
        # Configure connection pool limits per thread
        adapter = requests.adapters.HTTPAdapter(pool_connections=5, pool_maxsize=5, max_retries=1)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        _thread_local.session = session
    return cast(requests.Session, _thread_local.session)


def atomic_write_text(filepath: Path, content: str, encoding: str = "utf-8") -> None:
    """Atomically write text content to a file via a temporary file."""
    temp_path = filepath.with_suffix(f"{filepath.suffix}.tmp.{os.getpid()}_{threading.get_ident()}")
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_path, "w", encoding=encoding, errors="replace") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, filepath)
    except Exception:
        if temp_path.exists():
            with contextlib.suppress(OSError):
                temp_path.unlink()
        raise


def get_available_years() -> list[str]:
    """Discover all available event archive years on mmadecisions."""
    url = f"{BASE_URL}/decisions-by-event/"
    session = get_thread_session()

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                years: set[str] = set()
                for a in soup.find_all("a", href=True):
                    m = re.search(r"decisions-by-event/(\d{4})/", a["href"])
                    if m:
                        years.add(m.group(1))
                years.add("2026")
                return sorted(years, reverse=True)
            time.sleep(0.5 * (2**attempt))
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.error("Failed to retrieve archive years: %s", e)
                # Fallback to standard range
                return [str(y) for y in range(2026, 1994, -1)]
            time.sleep(1.0 * (2**attempt))

    return [str(y) for y in range(2026, 1994, -1)]


def fetch_events_for_year(year: str) -> list[dict[str, str]]:
    """Fetch and filter UFC event listings for a given year."""
    clean_year = sanitize_filename(str(year))
    url = f"{BASE_URL}/decisions-by-event/{clean_year}/"
    session = get_thread_session()

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code != 200:
                return []

            soup = BeautifulSoup(resp.text, "html.parser")
            events: list[dict[str, str]] = []

            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                title = a.get_text(strip=True)
                m = re.search(r"event/(\d+)/([^/\s]+)", href)
                if m:
                    event_id_str = m.group(1)
                    event_slug = m.group(2)

                    # Validate that event_id is strictly integer digits
                    validate_numeric_id(event_id_str, "event_id")

                    # Check UFC / TUF affiliation
                    is_ufc = bool(
                        re.search(r"\b(UFC|Ultimate Fighter|TUF)\b", title, re.IGNORECASE)
                        or re.search(r"\b(UFC|Ultimate-Fighter|TUF)\b", event_slug, re.IGNORECASE)
                    )

                    if is_ufc:
                        events.append(
                            {
                                "event_id": event_id_str,
                                "title": title,
                                "slug": event_slug,
                                "year": clean_year,
                                "url": f"{BASE_URL}/{href.lstrip('/')}",
                            }
                        )
            return events
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                logger.warning("Error fetching year %s: %s", year, e)
                return []
            time.sleep(0.5 * (2**attempt))

    return []


def get_all_ufc_events(max_workers: int = 5) -> list[dict[str, str]]:
    """Retrieve, validate, and persist all UFC events across all years."""
    years = get_available_years()
    print(f"Checking events across {len(years)} years ({years[-1]} to {years[0]})...")

    all_events: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_events_for_year, yr): yr for yr in years}
        for future in as_completed(futures):
            yr_events = future.result()
            for ev in yr_events:
                eid = ev["event_id"]
                if eid not in seen_ids:
                    seen_ids.add(eid)
                    all_events.append(ev)

    all_events.sort(key=lambda x: int(x["event_id"]), reverse=True)
    print(f"Found {len(all_events)} unique UFC events.")

    # Save indexed events atomically
    temp_json = EVENTS_JSON_PATH.with_suffix(".tmp")
    with open(temp_json, "w", encoding="utf-8") as f:
        json.dump(all_events, f, indent=2)
    os.replace(temp_json, EVENTS_JSON_PATH)

    return all_events


def download_single_event(event: dict[str, str]) -> tuple[str, bool, str]:
    """Download and cache an event HTML page with path security checks."""
    event_id = event["event_id"]
    validate_numeric_id(event_id, "event_id")

    # Securely resolve output path preventing directory traversal
    file_path = safe_resolve_path(EVENTS_HTML_DIR, f"{event_id}.html")

    # Cache hit check
    if file_path.exists() and file_path.stat().st_size > 1000:
        return event_id, True, "cached"

    safe_url = validate_safe_url(event["url"])
    session = get_thread_session()

    for attempt in range(MAX_RETRIES):
        try:
            resp = session.get(safe_url, timeout=DEFAULT_TIMEOUT)
            if resp.status_code == 200 and len(resp.text) > 1000:
                atomic_write_text(file_path, resp.text)
                return event_id, True, "downloaded"
            time.sleep(0.5 * (2**attempt))
        except requests.RequestException as e:
            if attempt == MAX_RETRIES - 1:
                return event_id, False, str(e)
            time.sleep(1.0 * (2**attempt))

    return event_id, False, "HTTP Failed"


def download_all_events(events: list[dict[str, str]], max_workers: int = 8) -> tuple[int, int, int]:
    """Download HTML for all events in parallel."""
    print(f"\nDownloading/caching HTML for {len(events)} UFC events...")
    EVENTS_HTML_DIR.mkdir(parents=True, exist_ok=True)

    success = 0
    cached = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(download_single_event, ev) for ev in events]
        for f in tqdm(as_completed(futures), total=len(futures), desc="Events"):
            eid, ok, status = f.result()
            if ok:
                if status == "cached":
                    cached += 1
                else:
                    success += 1
            else:
                failed += 1
                logger.error("Failed to download event %s: %s", eid, status)

    print(f"\nCompleted: {success} newly downloaded, {cached} loaded from cache, {failed} failed.")
    return success, cached, failed


if __name__ == "__main__":
    events = get_all_ufc_events()
    download_all_events(events)
