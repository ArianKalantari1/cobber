#!/usr/bin/env python3
"""Fetch and persist the Hotaling & Co. craft cocktail dataset (CSV).

Source: the OzanGenc/CocktailAnalysis mirror of the Kaggle "Cocktails —
Hotaling & Co." dataset: ~687 modern craft cocktails with bartender, bar, and
location attribution. This is Cobber's **frontier corpus** — recipes from
working craft bartenders rather than the canon. normalize.py routes it to
``data/frontier_evidence.json`` (validated-novel pairings with attribution),
NOT into the tradition score: one bartender using a pairing doesn't make it
traditional, and counting it would hide exactly the novelty Cobber hunts.

Saved verbatim to ``data/raw/hotaling_cocktails.csv``.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

SOURCE_URL = "https://raw.githubusercontent.com/OzanGenc/CocktailAnalysis/master/cocktails.csv"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "hotaling_cocktails.csv"


def fetch(timeout: float, retries: int, delay_s: float) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(SOURCE_URL, timeout=timeout) as response:  # nosec: B310 - fixed HTTPS host
                payload = response.read()
            if not payload.startswith(b"Cocktail Name,"):
                raise ValueError("Unexpected Hotaling CSV header.")
            return payload
        except (URLError, TimeoutError, ValueError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(delay_s)
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch Hotaling data after {retries} attempts") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the Hotaling craft cocktail CSV.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--timeout", type=float, default=30.0,
                        help="Request timeout in seconds (default: 30).")
    parser.add_argument("--retries", type=int, default=3,
                        help="Retry attempts on transient failures (default: 3).")
    args = parser.parse_args()

    payload = fetch(timeout=args.timeout, retries=args.retries, delay_s=2.0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    newline = b"\n"
    print(f"Wrote {payload.count(newline)} CSV rows to {args.output}")


if __name__ == "__main__":
    main()
