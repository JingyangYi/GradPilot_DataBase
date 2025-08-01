"""
Generate import-ready CSV files (tags, universities, cities, state/provinces, country/regions, majors)
from the translated program data CSV.

Usage:
    python generate_import_csvs.py [--source path/to/program_translated.csv] [--output-dir Data/]

Outputs (to the given output-dir):
    import_tags.csv
    import_universities.csv
    import_cities.csv
    import_state_provinces.csv
    import_country_regions.csv
    import_majors.csv

Requirements:
    - pandas
    - requests (only if you want to auto-fetch university websites via DeepSeek)
    - Set environment variable DEEPSEEK_API_KEY if website lookup is desired.

Note:
    If DEEPSEEK_API_KEY is not provided, the `website` column in university output will be left blank.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Set

import pandas as pd


import requests  # type: ignore

from dotenv import load_dotenv  # type: ignore

# ------------------------- Gemini helper ------------------------- #

def fetch_university_website(univ_name: str, api_key: str | None) -> str:
    """Query Gemini 2.5 Pro for the university's official website.

    If *api_key* is missing or *requests* is unavailable, returns an empty string.
    """
    if not api_key or not requests:
        return ""

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    prompt = f"What is the official website URL of {univ_name}? Please answer with only the URL."
    try:
        resp = requests.post(
            endpoint,
            params={"key": api_key},
            json={
                "contents": [
                    {
                        "parts": [
                            {"text": prompt}
                        ]
                    }
                ]
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        # Gemini response structure: candidates -> content -> parts -> text
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        # Extract first URL from text
        match = re.search(r"(https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})", text)
        url = match.group(0).lstrip("https://").lstrip("http://") if match else ""
        return url.rstrip("\n\r") if url else ""
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Gemini lookup failed for {univ_name}: {exc.__class__.__name__}", file=sys.stderr)
    return ""

# ------------------------- Extraction helpers ------------------------- #

def parse_city_state(value: str) -> tuple[str, str]:
    """Split a string like "Cambridge, MA" into (city, state_province).
    If the comma is missing, return value as city and empty state.
    """
    parts = [p.strip() for p in value.split(",")]
    if len(parts) == 2:
        return parts[0], parts[1]
    if len(parts) == 3:
        return parts[0], parts[1]  # ignore country if present here
    return value.strip(), ""


# ------------------------- Main pipeline ------------------------- #

def build_tags(df: pd.DataFrame) -> pd.DataFrame:
    col = "tags"
    if col not in df.columns:
        raise KeyError(f"Column '{col}' not found in source CSV.")
    unique: Set[str] = set()
    for cell in df[col].dropna():
        for tag in str(cell).split(","):
            tag = tag.strip()
            if tag:
                unique.add(tag)
    return pd.DataFrame(sorted(unique), columns=["tag_name"])


def build_universities(df: pd.DataFrame, api_key: str | None) -> pd.DataFrame:
    required_cols = {"univ_name", "city", "univ_rank"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Missing columns in source CSV: {', '.join(missing)}")

    # Use dict to keep first seen info per university
    records: Dict[str, Dict[str, str]] = {}

    for _, row in df.iterrows():
        name = str(row["univ_name"]).strip()
        if not name:
            continue
        if name not in records:
            city_raw = str(row["city"]).strip()
            city, state = parse_city_state(city_raw)
            ranking = row["univ_rank"]
            try:
                ranking = int(ranking)
            except Exception:
                ranking = ""
            website = fetch_university_website(name, api_key)
            records[name] = {
                "univ_name": name,
                "city": city,
                "state_province": state,
                "country_region": "United States" if state else "",  # naive assumption; adjust as needed
                "ranking": ranking,
                "website": website,
            }

    return pd.DataFrame(records.values()).sort_values("univ_name")


def build_cities_states_countries(univ_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    city_records: Set[tuple[str, str]] = set()
    state_records: Set[tuple[str, str]] = set()

    for _, row in univ_df.iterrows():
        city = row["city"]
        state = row["state_province"]
        country = row["country_region"] or "United States"
        city_records.add((city, state, country))
        state_records.add((state, country))

    cities_df = pd.DataFrame(sorted(city_records), columns=["city", "state_province", "country_region"])
    states_df = pd.DataFrame(sorted(state_records), columns=["state_province", "country_region"])
    countries_df = pd.DataFrame(sorted({c for *_, c in city_records}), columns=["country_region"])
    return cities_df, states_df, countries_df


def build_majors_from_filename(source_path: Path, api_key: str | None) -> pd.DataFrame:
    """Use Gemini to extract English major name(s) from the source CSV filename."""
    filename = source_path.name
    majors: list[str] = []
    if api_key and requests:
        majors = llm_extract_majors(filename, api_key)

    if not majors:
        # Fallback heuristic (ASCII segments or default)
        stem = source_path.stem
        stem = re.sub(r"\(.*\)", "", stem).strip()
        parts = [p.strip() for p in re.split(r"[-_]", stem)]
        majors = [p for p in parts if re.search(r"[A-Za-z]", p)] or ["Data Science"]

    unique = sorted({m.strip() for m in majors if m.strip()})
    return pd.DataFrame(unique, columns=["major_name"])


def llm_extract_majors(filename: str, api_key: str) -> list[str]:
    """Ask Gemini to list English majors inferred from the filename."""
    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent"
    prompt = (
        "Given the following data file name, extract the academic major name it refers to. "
        "Return ONLY a single concise English major name. "
        "If none can be identified, return an empty string.\n\n"
        f"Filename: {filename}"
    )
    try:
        resp = requests.post(
            endpoint,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15,
        )
        resp.raise_for_status()
        text = (
            resp.json().get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
            .strip()
        )
        majors = [m.strip() for m in text.split(",") if m.strip()]
        return majors
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] Gemini major extraction failed: {exc}", file=sys.stderr)
    return []

# ------------------------- CLI ------------------------- #

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate import CSVs for gradpilot DB.")
    parser.add_argument("--source", default="Data/美研-数据科学 - Sheet1 (1)_cleaned_translated.csv", help="Path to translated program CSV.")
    parser.add_argument("--output-dir", default="Data", help="Directory to store generated CSVs.")
    args = parser.parse_args()

    source_path = Path(args.source)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Load .env (if dotenv available) to populate environment variables
    if load_dotenv is not None:
        env_path = Path(__file__).with_name(".env")
        if env_path.exists():
            load_dotenv(env_path)

    df = pd.read_csv(source_path)
    api_key = os.getenv("GEMINI_API_KEY")

    # Tags   
    tags_df = build_tags(df)
    tags_df.to_csv(out_dir / "import_tags.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    # Universities (+ derived geo tables)
    univ_df = build_universities(df, api_key)
    univ_df.to_csv(out_dir / "import_universities.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    cities_df, states_df, countries_df = build_cities_states_countries(univ_df)
    cities_df.to_csv(out_dir / "import_cities.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    states_df.to_csv(out_dir / "import_state_provinces.csv", index=False, quoting=csv.QUOTE_MINIMAL)
    countries_df.to_csv(out_dir / "import_country_regions.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    # Majors
    majors_df = build_majors_from_filename(source_path, api_key)
    majors_df.to_csv(out_dir / "import_majors.csv", index=False, quoting=csv.QUOTE_MINIMAL)

    print("Generated CSVs:")
    for fp in sorted(out_dir.glob("import_*.csv")):
        try:
            rel = fp.resolve().relative_to(Path.cwd())
        except ValueError:
            rel = fp
        print(" -", rel)


if __name__ == "__main__":
    main()
