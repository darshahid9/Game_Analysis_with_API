"""
API extraction layer.

NOTE on field names: SportRadar's exact JSON keys can drift slightly between
trial/production access levels and API versions. Run `python src/extract.py`
once with DEBUG_DUMP=1 to print a raw response and confirm key names match
what's assumed below before trusting the parsed output. This is a normal,
expected calibration step, not a bug.
"""
import json
import time
import logging
from pathlib import Path

import requests

from src.config import SPORTRADAR_API_KEY, SPORTRADAR_BASE_URL, REQUEST_DELAY_SECONDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


class SportRadarError(Exception):
    pass


def _get(endpoint: str, params: dict | None = None, retries: int = 3) -> dict:
    if not SPORTRADAR_API_KEY:
        raise SportRadarError("SPORTRADAR_API_KEY is not set. Add it to your .env file.")

    url = f"{SPORTRADAR_BASE_URL}/{endpoint}"
    headers = {"x-api-key": SPORTRADAR_API_KEY}

    for attempt in range(1, retries + 1):
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        time.sleep(REQUEST_DELAY_SECONDS)  # respect trial-key rate limit

        if resp.status_code == 200:
            return resp.json()
        if resp.status_code == 403:
            raise SportRadarError(
                f"{endpoint} failed: HTTP 403 (missing/invalid API key — check .env)"
            )
        if resp.status_code == 429:
            wait = REQUEST_DELAY_SECONDS * (2 ** attempt)
            log.warning("Rate limited (429). Backing off %.1fs (attempt %d/%d)", wait, attempt, retries)
            time.sleep(wait)
            continue

        raise SportRadarError(f"{endpoint} failed: HTTP {resp.status_code} — {resp.text[:300]}")

    raise SportRadarError(f"{endpoint} failed after {retries} retries (repeated 429s).")


def _dump_raw(name: str, payload: dict) -> None:
    path = RAW_DIR / f"{name}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    log.info("Saved raw response -> %s", path)


def get_competitions() -> dict:
    data = _get("competitions.json")
    _dump_raw("competitions", data)
    return data


def get_complexes() -> dict:
    data = _get("complexes.json")
    _dump_raw("complexes", data)
    return data


def get_doubles_rankings(gender: str = "men") -> dict:
    """gender: 'men' or 'women'."""
    data = _get("double_competitors_rankings.json")
    _dump_raw(f"doubles_rankings_{gender}", data)
    return data


if __name__ == "__main__":
    log.info("Fetching competitions...")
    comps = get_competitions()
    log.info("Top-level keys: %s", list(comps.keys()))

    log.info("Fetching complexes...")
    cxs = get_complexes()
    log.info("Top-level keys: %s", list(cxs.keys()))

    log.info("Fetching doubles rankings...")
    ranks = get_doubles_rankings()
    log.info("Top-level keys: %s", list(ranks.keys()))

    log.info("Raw JSON saved under data/raw/ — inspect these to confirm field names before running load.py")
