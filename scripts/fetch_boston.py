#!/usr/bin/env python3
"""Fetch and persist the Mr. Boston cocktail dataset (CSV).

Source: the TidyTuesday mirror of the Mr. Boston Official Bartender's Guide
recipe data (~989 drinks, one row per ingredient with clean oz measures).
Saved verbatim to ``data/raw/boston_cocktails.csv``; normalize.py groups the
rows back into drinks.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

SOURCE_URL = (
    "https://raw.githubusercontent.com/rfordatascience/tidytuesday/"
    "main/data/2020/2020-05-26/boston_cocktails.csv"
)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "boston_cocktails.csv"


def fetch(timeout: float, retries: int, delay_s: float) -> bytes:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(SOURCE_URL, timeout=timeout) as response:  # nosec: B310 - fixed HTTPS host
                payload = response.read()
            if not payload.startswith(b"name,category,"):
                raise ValueError("Unexpected Mr. Boston CSV header.")
            return payload
        except (URLError, TimeoutError, ValueError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(delay_s)
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch Mr. Boston data after {retries} attempts") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the Mr. Boston cocktail recipes CSV.")
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
    lines = payload.count(b"\n")
    print(f"Wrote {lines} CSV rows to {args.output}")


if __name__ == "__main__":
    main()
