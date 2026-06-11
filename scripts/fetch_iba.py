#!/usr/bin/env python3
"""Fetch and persist the IBA official cocktail list (structured JSON).

Source: the teijo/iba-cocktails dataset — the IBA official list transcribed to
JSON with per-ingredient amounts in cl. The structured amounts are the reason
this source was chosen: they feed the dose-aware decomposition in normalize.py
without any measure-string parsing. The list is the older 77-drink edition of
the IBA canon (the current official list has 102); the missing additions can
come from a later source.

Saves the full raw objects to ``data/raw/iba.json``.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

SOURCE_URL = "https://raw.githubusercontent.com/teijo/iba-cocktails/master/recipes.json"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "iba.json"


def fetch(timeout: float, retries: int, delay_s: float) -> list[dict]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with urlopen(SOURCE_URL, timeout=timeout) as response:  # nosec: B310 - fixed HTTPS host
                payload = json.load(response)
            if not isinstance(payload, list) or not payload:
                raise ValueError("Unexpected IBA payload shape.")
            return [item for item in payload if isinstance(item, dict)]
        except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            last_error = error
            if attempt < retries:
                time.sleep(delay_s)
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch IBA recipes after {retries} attempts") from last_error


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch the IBA official cocktail recipes.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help=f"Output path (default: {DEFAULT_OUTPUT})")
    parser.add_argument("--timeout", type=float, default=20.0,
                        help="Request timeout in seconds (default: 20).")
    parser.add_argument("--retries", type=int, default=3,
                        help="Retry attempts on transient failures (default: 3).")
    args = parser.parse_args()

    recipes = fetch(timeout=args.timeout, retries=args.retries, delay_s=2.0)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(recipes, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {len(recipes)} IBA recipes to {args.output}")


if __name__ == "__main__":
    main()
