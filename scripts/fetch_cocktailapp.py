#!/usr/bin/env python3
"""Fetch the cocktailApp (CRAN) recipe dataset and extract Difford's + Kindred.

Source: the ``cocktails`` data shipped with the cocktailApp R package
(Steven E. Pav, LGPL-3, CRAN) — ~21k cocktails scraped from four websites in
2017-18. We keep only the two quality sources, per Ari's call:

- **Difford's Guide** (~4k, expert-curated) -> canon corpus
- **Kindred Cocktails** (~5.8k, community craft) -> frontier corpus

Webtender and Drinks Mixer (2000s amateur web recipes) are deliberately left
out so "tradition" keeps meaning what bartenders make, not what the internet
mixed in 2005. The package author notes the scrape "falls in a legal gray
area" and claims no copyright; we mirror it as a published research dataset,
build-time only.

Writes the verbatim ``data/raw/cocktailapp.rda`` plus the filtered
``data/raw/cocktailapp_recipes.json`` (per-drink records with ingredient
amounts, proportions, rating, votes). Requires ``pyreadr`` at fetch time only;
the committed JSON keeps the rest of the pipeline dependency-free.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

SOURCE_URL = "https://raw.githubusercontent.com/shabbychef/cocktailApp/master/data/cocktails.rda"
ROOT = Path(__file__).resolve().parents[1]
RDA_OUTPUT = ROOT / "data" / "raw" / "cocktailapp.rda"
JSON_OUTPUT = ROOT / "data" / "raw" / "cocktailapp_recipes.json"
KEEP_SITES = {"diffordsguide.com": "diffords", "kindredcocktails.com": "kindred"}


def fetch(timeout: float, retries: int, delay_s: float) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(SOURCE_URL, timeout=timeout) as response:  # nosec: B310 - fixed HTTPS host
                return response.read()
        except (URLError, TimeoutError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(delay_s)
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch cocktailApp data after {retries} attempts") from last_error


def convert(rda_path: Path) -> list[dict]:
    try:
        import pyreadr
    except ImportError as error:
        raise SystemExit("pyreadr is required at fetch time: pip install pyreadr") from error

    frame = pyreadr.read_r(str(rda_path))["cocktails"]
    frame["site"] = frame["url"].fillna("").str.extract(r"https?://(?:www\.)?([^/]+)")[0]
    frame = frame[frame["site"].isin(KEEP_SITES)]

    drinks: dict[tuple, dict] = {}
    for row in frame.itertuples(index=False):
        key = (row.site, row.cocktail)
        drink = drinks.setdefault(
            key,
            {
                "name": row.cocktail,
                "source": KEEP_SITES[row.site],
                "rating": None if row.rating != row.rating else round(float(row.rating), 2),
                "votes": None if row.votes != row.votes else int(row.votes),
                "attribution": None,
                "ingredients": [],
            },
        )
        src = getattr(row, "src", None)
        if isinstance(src, str) and src.strip() and not drink["attribution"]:
            drink["attribution"] = src.strip()
        unit = row.unit if isinstance(row.unit, str) else ""
        if unit == "garnish":
            continue  # garnishes excluded for consistency with the other corpora
        item = {
            "name": str(row.short_ingredient),
            "full_name": str(row.ingredient),
            "unit": unit or None,
            "amt": None if row.amt != row.amt else round(float(row.amt), 3),
            "proportion": None if row.proportion != row.proportion else round(float(row.proportion), 4),
        }
        drink["ingredients"].append(item)

    records = [d for d in drinks.values() if d["ingredients"]]
    records.sort(key=lambda d: (d["source"], d["name"]))
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch cocktailApp data (Difford's + Kindred).")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--retries", type=int, default=3)
    args = parser.parse_args()

    payload = fetch(timeout=args.timeout, retries=args.retries, delay_s=2.0)
    RDA_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    RDA_OUTPUT.write_bytes(payload)
    print(f"Wrote {len(payload)} bytes to {RDA_OUTPUT}")

    records = convert(RDA_OUTPUT)
    with JSON_OUTPUT.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, separators=(",", ":"))
        handle.write("\n")
    counts: dict[str, int] = {}
    for record in records:
        counts[record["source"]] = counts.get(record["source"], 0) + 1
    print(f"Wrote {len(records)} drinks to {JSON_OUTPUT} ({counts})")


if __name__ == "__main__":
    main()
