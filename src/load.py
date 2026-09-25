"""
Transforms nested SportRadar JSON into flat rows and loads them into MySQL.

Uses the already-downloaded JSON files from data/raw/ instead of
calling the SportRadar API again.
"""

import json
import logging
from pathlib import Path

import pandas as pd
from sqlalchemy.engine import Engine

from src.db import get_engine, run_schema


RAW_DIR = Path("data/raw")


def load_json(filename):
    path = RAW_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

log = logging.getLogger(__name__)


# ---------- Parsers: nested JSON -> flat DataFrames ----------

def parse_competitions(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    categories = {}
    competitions = []

    for c in payload.get("competitions", []):
        cat = c.get("category", {})

        if cat.get("id"):
            categories[cat["id"]] = cat.get("name", "")

        competitions.append({
            "competition_id": c.get("id"),
            "competition_name": c.get("name"),
            "parent_id": c.get("parent_id"),
            "type": c.get("type", "unknown"),
            "gender": c.get("gender", "unknown"),
            "category_id": cat.get("id"),
        })

    cat_df = pd.DataFrame(
        [
            {
                "category_id": k,
                "category_name": v
            }
            for k, v in categories.items()
        ]
    )

    comp_df = pd.DataFrame(competitions).dropna(
        subset=["competition_id", "category_id"]
    )

    return cat_df, comp_df


def parse_complexes(payload: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    complexes = []
    venues = []

    for cx in payload.get("complexes", []):

        complexes.append({
            "complex_id": cx.get("id"),
            "complex_name": cx.get("name")
        })

        for v in cx.get("venues", []):

            venues.append({
                "venue_id": v.get("id"),
                "venue_name": v.get("name"),
                "city_name": v.get("city_name", ""),
                "country_name": v.get("country_name", ""),
                "country_code": v.get("country_code", ""),
                "timezone": v.get("timezone", ""),
                "complex_id": cx.get("id"),
            })

    return (
        pd.DataFrame(complexes),
        pd.DataFrame(venues)
    )


def parse_rankings(
    payload: dict,
    gender: str
) -> tuple[pd.DataFrame, pd.DataFrame]:

    competitors = {}
    rankings = []

    for block in payload.get("rankings", []):

        year = block.get("year")
        week = block.get("week")

        # SportRadar ranking response may contain competitor_rankings
        # rather than rankings inside each block.
        ranking_items = block.get(
            "competitor_rankings",
            block.get("rankings", [])
        )

        for r in ranking_items:

            comp = r.get("competitor", {})
            cid = comp.get("id")

            if cid:
                competitors[cid] = {
                    "competitor_id": cid,
                    "name": comp.get("name", ""),
                    "country": comp.get("country", ""),
                    "country_code": comp.get("country_code", ""),
                    "abbreviation": comp.get("abbreviation", ""),
                }

            if cid:
                rankings.append({
                    "rank": r.get("rank"),
                    "movement": r.get("movement", 0),
                    "points": r.get("points", 0),
                    "competitions_played": r.get(
                        "competitions_played", 0
                    ),
                    "competitor_id": cid,
                    "rank_type": "doubles",
                    "gender": gender,
                    "year": year,
                    "week": week,
                })

    comp_df = pd.DataFrame(
        list(competitors.values())
    )

    rank_df = pd.DataFrame(rankings)

    if not rank_df.empty:
        rank_df = rank_df.dropna(
            subset=["competitor_id", "rank"]
        )

    return comp_df, rank_df


# ---------- Load: DataFrames -> MySQL ----------

def upsert(
    engine: Engine,
    df: pd.DataFrame,
    table: str
) -> None:

    if df.empty:
        log.warning(
            "Skipping %s — no rows parsed.",
            table
        )
        return

    # Remove duplicate records based on the first column.
    df = df.drop_duplicates(
        subset=[df.columns[0]]
    )

    df.to_sql(
        table,
        engine,
        if_exists="append",
        index=False,
        method="multi",
        chunksize=500
    )

    log.info(
        "Loaded %d rows -> %s",
        len(df),
        table
    )


# ---------- Main Pipeline ----------

def run_pipeline() -> None:

    engine = get_engine()

    # Create tables if required.
    # CREATE INDEX statements are skipped by src/db.py
    # because the indexes already exist in the database.
    run_schema(engine)

    # -------------------------------------------------
    # 1. COMPETITIONS
    # -------------------------------------------------

    log.info(
        "Loading competitions from local JSON..."
    )

    competitions_payload = load_json(
        "competitions.json"
    )

    cat_df, comp_df = parse_competitions(
        competitions_payload
    )

    upsert(
        engine,
        cat_df,
        "categories"
    )

    upsert(
        engine,
        comp_df,
        "competitions"
    )

    # -------------------------------------------------
    # 2. COMPLEXES + VENUES
    # -------------------------------------------------

    log.info(
        "Loading complexes/venues from local JSON..."
    )

    complexes_payload = load_json(
        "complexes.json"
    )

    cx_df, venue_df = parse_complexes(
        complexes_payload
    )

    upsert(
        engine,
        cx_df,
        "complexes"
    )

    upsert(
        engine,
        venue_df,
        "venues"
    )

    # -------------------------------------------------
    # 3. DOUBLES RANKINGS
    # -------------------------------------------------

    log.info(
        "Loading doubles rankings from local JSON..."
    )

    rankings_payload = load_json(
        "double_competitors_rankings.json"
    )

    competitor_df, ranking_df = parse_rankings(
        rankings_payload,
        "men"
    )

    upsert(
        engine,
        competitor_df,
        "competitors"
    )

    upsert(
        engine,
        ranking_df,
        "competitor_rankings"
    )

    # -------------------------------------------------
    # COMPLETE
    # -------------------------------------------------

    log.info(
        "Pipeline complete."
    )


if __name__ == "__main__":
    run_pipeline()