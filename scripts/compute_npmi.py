#!/usr/bin/env python3
"""Compute pairwise NPMI tradition scores from normalized recipes."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES_PATH = ROOT / "data" / "recipes_normalized.json"
OUTPUT_PATH = ROOT / "data" / "tradition_npmi.json"
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
COMPOSITES_PATH = ROOT / "data" / "composites.json"


def _load_excluded_pairs() -> set[frozenset[str]]:
    """Pairs of a composite and its own flavor_forward component.

    Since normalization implies these components into every recipe containing
    the composite, the pair co-occurs by construction (amaretto + almond,
    citron vodka + vodka). Scoring them as "tradition" would be circular, so
    they are excluded from the pair counts.
    """
    excluded: set[frozenset[str]] = set()
    for path in (INGREDIENTS_PATH, COMPOSITES_PATH):
        with path.open(encoding="utf-8") as handle:
            entries = json.load(handle)
        for entry in entries:
            for component in entry.get("flavor_forward", []):
                excluded.add(frozenset((entry["id"], str(component))))
    return excluded


def _load_recipes(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("recipes_normalized.json must contain a list.")

    recipes: list[list[str]] = []
    for recipe in payload:
        if not isinstance(recipe, list):
            continue
        normalized = sorted({str(item).strip() for item in recipe if str(item).strip()})
        if len(normalized) >= 2:
            recipes.append(normalized)
    if not recipes:
        raise ValueError("No usable recipes found in recipes_normalized.json.")
    return recipes


def compute_npmi(recipes: list[list[str]]) -> list[dict[str, object]]:
    total_recipes = len(recipes)
    ingredient_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    for recipe in recipes:
        ingredient_counts.update(recipe)
        pair_counts.update(combinations(recipe, 2))

    excluded_pairs = _load_excluded_pairs()
    rows: list[dict[str, object]] = []
    for (a, b), pair_count in pair_counts.items():
        if frozenset((a, b)) in excluded_pairs:
            continue
        p_x = ingredient_counts[a] / total_recipes
        p_y = ingredient_counts[b] / total_recipes
        p_xy = pair_count / total_recipes

        pmi = math.log(p_xy / (p_x * p_y))
        npmi = 1.0 if p_xy == 1.0 else pmi / (-math.log(p_xy))
        tradition = max(0.0, npmi)

        rows.append(
            {
                "pair": [a, b],
                "count": pair_count,
                "npmi": round(npmi, 6),
                "tradition": round(tradition, 6),
            }
        )

    rows.sort(key=lambda row: (row["npmi"], row["count"], row["pair"]), reverse=True)
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Compute NPMI pair scores from normalized recipes.")
    parser.add_argument(
        "--recipes",
        type=Path,
        default=RECIPES_PATH,
        help=f"Normalized recipes input (default: {RECIPES_PATH})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT_PATH,
        help=f"NPMI output path (default: {OUTPUT_PATH})",
    )
    args = parser.parse_args()

    recipes = _load_recipes(args.recipes)
    rows = compute_npmi(recipes)
    _write_json(args.output, rows)
    print(f"Computed NPMI for {len(rows)} pairs from {len(recipes)} recipes -> {args.output}")


if __name__ == "__main__":
    main()
