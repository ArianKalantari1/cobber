#!/usr/bin/env python3
"""Convert computed NPMI rows into data/tradition.json format."""

from __future__ import annotations

import argparse
import json
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
    rows: list[dict] = []
    for row in npmi_rows:
        pair = row.get("pair")
        count = int(row.get("count", 0))
        tradition = float(row.get("tradition", 0.0))
        if not isinstance(pair, list) or len(pair) != 2:
            continue
        a, b = str(pair[0]), str(pair[1])
        rows.append(
            {
                "pair": [a, b],
                "tradition": round(tradition, 6),
                "count": count,
                "confidence": _confidence(count),
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
