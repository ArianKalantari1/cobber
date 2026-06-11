#!/usr/bin/env python3
"""Fetch and persist raw cocktail recipes from TheCocktailDB."""

from __future__ import annotations

import argparse
import json
import string
import time
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen

API_TEMPLATE = "https://www.thecocktaildb.com/api/json/v1/1/search.php?f={token}"
TOKENS = tuple(string.ascii_lowercase + string.digits)
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "raw" / "thecocktaildb.json"


def _fetch_letter(token: str, timeout: float) -> list[dict[str, Any]]:
    url = API_TEMPLATE.format(token=token)
    with urlopen(url, timeout=timeout) as response:  # nosec: B310 - fixed HTTPS host
        payload = json.load(response)
    drinks = payload.get("drinks")
    if not drinks:
        return []
    if not isinstance(drinks, list):
        raise ValueError(f"Unexpected drinks payload type for token {token!r}")
    return [item for item in drinks if isinstance(item, dict)]


def _fetch_with_retries(token: str, timeout: float, retries: int, delay_s: float) -> list[dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            return _fetch_letter(token, timeout=timeout)
        except (URLError, TimeoutError, json.JSONDecodeError, ValueError) as error:
            last_error = error
            if attempt == retries:
                break
            time.sleep(delay_s)
    assert last_error is not None
    raise RuntimeError(f"Failed to fetch token {token!r} after {retries} attempts") from last_error


def fetch_all(delay_s: float, timeout: float, retries: int) -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for token in TOKENS:
        drinks = _fetch_with_retries(token, timeout=timeout, retries=retries, delay_s=delay_s)
        for drink in drinks:
            drink_id = str(drink.get("idDrink", "")).strip()
            if not drink_id:
                continue
            if drink_id not in by_id:
                by_id[drink_id] = drink
        time.sleep(delay_s)
    return [by_id[drink_id] for drink_id in sorted(by_id)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Fetch full raw drink objects from TheCocktailDB and deduplicate by idDrink."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.2,
        help="Delay between requests in seconds (default: 0.2).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Request timeout in seconds (default: 20).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="Retry attempts per token on transient failures (default: 3).",
    )
    args = parser.parse_args()

    if args.delay < 0:
        raise ValueError("--delay must be >= 0")
    if args.timeout <= 0:
        raise ValueError("--timeout must be > 0")
    if args.retries < 1:
        raise ValueError("--retries must be >= 1")

    recipes = fetch_all(delay_s=args.delay, timeout=args.timeout, retries=args.retries)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(recipes, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {len(recipes)} unique drinks to {args.output}")


if __name__ == "__main__":
    main()
