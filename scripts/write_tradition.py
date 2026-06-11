#!/usr/bin/env python3
"""Convert computed co-occurrence rows into data/tradition.json format.

The ``tradition`` score is log-scaled prevalence — how often a pair is actually
made, ``log(1 + count) / log(1 + max_count)`` — NOT raw NPMI. NPMI measures how
far above chance two ingredients co-occur, which structurally penalises
ubiquitous classics (gin + lime lands near zero because both are common) and
rewards one-off pairs (two ingredients seen together in a single recipe score a
perfect 1.0). For Cobber's novelty signal we want "how canonical is this", so
prevalence is the right transform. The raw ``npmi`` is retained per row for
transparency and for any later hybrid.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NPMI_PATH = ROOT / "data" / "tradition_npmi.json"
TRADITION_PATH = ROOT / "data" / "tradition.json"


def _load_npmi(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("tradition_npmi.json must contain a list.")
    return [row for row in payload if isinstance(row, dict)]


def _confidence(count: int) -> str:
    if count >= 10:
        return "solid"
    if count >= 3:
        return "moderate"
    return "sparse"


def build_tradition_rows(npmi_rows: list[dict]) -> list[dict]:
    valid = [
        row
        for row in npmi_rows
        if isinstance(row.get("pair"), list) and len(row["pair"]) == 2
    ]
    max_count = max((int(r.get("count", 0)) for r in valid), default=0)
    log_max = math.log1p(max_count) if max_count > 0 else 0.0

    rows: list[dict] = []
    for row in valid:
        pair = row["pair"]
        count = int(row.get("count", 0))
        a, b = str(pair[0]), str(pair[1])
        # Tradition = log-scaled prevalence in [0, 1], not raw NPMI (see module docstring).
        tradition = (math.log1p(count) / log_max) if log_max > 0 else 0.0
        rows.append(
            {
                "pair": [a, b],
                "tradition": round(tradition, 6),
                "count": count,
                "confidence": _confidence(count),
                "npmi": round(float(row.get("npmi", row.get("tradition", 0.0))), 6),
            }
        )
    rows.sort(key=lambda row: (row["tradition"], row["count"], row["pair"]), reverse=True)
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write tradition.json from NPMI pair rows.")
    parser.add_argument(
        "--input",
        type=Path,
        default=NPMI_PATH,
        help=f"Input NPMI rows (default: {NPMI_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=TRADITION_PATH,
        help=f"Output tradition file (default: {TRADITION_PATH})",
    )
    args = parser.parse_args()

    npmi_rows = _load_npmi(args.input)
    tradition_rows = build_tradition_rows(npmi_rows)
    _write_json(args.output, tradition_rows)
    print(f"Wrote {len(tradition_rows)} tradition rows to {args.output}")


if __name__ == "__main__":
    main()
