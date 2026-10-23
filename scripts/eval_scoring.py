#!/usr/bin/env python3
"""Regression panel for Cobber's drink-level scoring.

Scores a fixed panel with the engine as it stands and compares the result
against a committed baseline, so a scoring change shows what it did to real
drinks before it ships. The panel:

  * ``olivia`` — the Olivia versions from the house specs (the house gin is the
                 generic London dry ``gin`` until its label is in);
  * ``pairs``  — two-ingredient drinks whose verdict is known: ``duplicate``
                 pairs are the same aroma and should earn no bridge credit,
                 ``distinct`` pairs are real bridges and should keep theirs;
  * ``stacks`` — the same note piled up (citrus on citrus);
  * ``iba``    — every IBA drink in the recipe corpus.

Each entry records the drink-level harmony and novelty that ``build_around``
ranks by. The comparison prints the IBA rank correlation, the biggest movers,
and every Olivia, pair and stack score before and after.

    python3 scripts/eval_scoring.py                  # compare against the baseline
    python3 scripts/eval_scoring.py --save-baseline  # record the current scores

Build-time only: the server never reads the baseline.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from cobber import engine

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RECIPES_PATH = DATA / "recipes_components.json"
BASELINE_PATH = DATA / "scoring_baseline.json"

OLIVIA = {
    "restaurant (menu)": ["gin", "amaretto", "honey", "lemon", "olive"],
    "M1": ["gin", "dry_vermouth", "amaretto", "maraschino", "lemon", "olive"],
    "M2": ["gin", "amaretto", "maraschino", "vanilla", "lemon", "olive"],
    "P": ["gin", "amaretto", "peach_schnapps", "vanilla", "lemon", "olive"],
    "B": ["gin", "amaretto", "benedictine", "vanilla", "lemon", "olive"],
}

PAIRS = {
    # Same aroma: one is a copy of the other, or an aroma botanical already on
    # the other's bill. Benedictine + vanilla is a data gap, not a real copy;
    # it stays here until Benedictine's bill is fixed.
    "duplicate": [
        ["amaretto", "almond"],
        ["limoncello", "lemon"],
        ["gin", "coriander_seed"],
        ["coffee_liqueur", "coffee"],
        ["triple_sec", "orange"],
        ["benedictine", "vanilla"],
    ],
    # Real bridges between different ingredients.
    "distinct": [
        ["gin", "lemon"],
        ["lemon", "lime"],
        ["amaretto", "maraschino"],
        ["gin", "lime"],
        ["olive", "amaretto"],
    ],
}

STACKS = [
    ["gin", "lemon"],
    ["gin", "lemon", "lime"],
    ["gin", "lemon", "limoncello"],
    ["gin", "lemon", "grapefruit"],
    ["gin", "dry_vermouth", "lemon"],
]


def _score(ingredient_ids: list[str]) -> dict:
    """The drink-level scores build_around ranks by, plus the ingredients scored."""
    scores = engine._score_combination(ingredient_ids)
    return {"ingredients": ingredient_ids, "harmony": scores["harmony"], "novelty": scores["novelty"]}


def _iba_drinks() -> list[dict]:
    with RECIPES_PATH.open(encoding="utf-8") as handle:
        recipes = json.load(handle)
    return [
        {"drink": row["drink"], "ingredients": list(dict.fromkeys(row["literal"]))}
        for row in recipes
        if row["source"] == "iba"
    ]


def run_panel() -> dict:
    """Score the whole panel with the current engine."""
    return {
        "olivia": {name: _score(ids) for name, ids in OLIVIA.items()},
        "pairs": {
            kind: {"+".join(ids): _score(ids) for ids in pairs} for kind, pairs in PAIRS.items()
        },
        "stacks": {"+".join(ids): _score(ids) for ids in STACKS},
        "iba": {drink["drink"]: _score(drink["ingredients"]) for drink in _iba_drinks()},
    }


def _ranks(values: list[float]) -> list[float]:
    """Average ranks (ties share the mean of their positions), for Spearman."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(order):
        end = position
        while end + 1 < len(order) and values[order[end + 1]] == values[order[position]]:
            end += 1
        for k in range(position, end + 1):
            ranks[order[k]] = (position + end) / 2
        position = end + 1
    return ranks


def spearman(xs: list[float], ys: list[float]) -> float:
    """Spearman rank correlation with tie-aware ranks (Pearson on the ranks)."""
    rx, ry = _ranks(xs), _ranks(ys)
    n = len(rx)
    mx, my = sum(rx) / n, sum(ry) / n
    cov = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sx = sum((a - mx) ** 2 for a in rx) ** 0.5
    sy = sum((b - my) ** 2 for b in ry) ** 0.5
    return cov / (sx * sy) if sx and sy else 1.0


def _line(label: str, before: dict | None, after: dict) -> str:
    if before is None:
        return f"  {label:34s} new          -> {after['harmony']:.3f}"
    delta = after["harmony"] - before["harmony"]
    mark = "" if abs(delta) < 0.0005 else f"  ({delta:+.3f})"
    return f"  {label:34s} {before['harmony']:.3f} -> {after['harmony']:.3f}{mark}"


def compare(baseline: dict, current: dict, movers: int = 6) -> None:
    """Print what changed between the baseline and the current engine."""
    print("Olivia (harmony, baseline -> now):")
    for name, after in current["olivia"].items():
        print(_line(name, baseline["olivia"].get(name), after))
    for kind, rows in current["pairs"].items():
        print(f"\n{kind.capitalize()} pairs:")
        for label, after in rows.items():
            print(_line(label, baseline["pairs"].get(kind, {}).get(label), after))
    print("\nStacks:")
    for label, after in current["stacks"].items():
        print(_line(label, baseline["stacks"].get(label), after))

    shared = [name for name in current["iba"] if name in baseline["iba"]]
    before = [baseline["iba"][name]["harmony"] for name in shared]
    after = [current["iba"][name]["harmony"] for name in shared]
    print(f"\nIBA: {len(shared)} drinks; rank correlation with the baseline {spearman(before, after):.2f}")
    changed = sum(1 for b, a in zip(before, after) if abs(a - b) >= 0.0005)
    print(f"  scores changed: {changed}; scoring 0 before: {sum(1 for b in before if b == 0)}, now: "
          f"{sum(1 for a in after if a == 0)}")
    deltas = sorted(zip((a - b for a, b in zip(after, before)), shared, before, after))
    falls = [f"{n} {b:.2f}->{a:.2f}" for d, n, b, a in deltas[:movers] if d <= -0.0005]
    rises = [f"{n} {b:.2f}->{a:.2f}" for d, n, b, a in reversed(deltas[-movers:]) if d >= 0.0005]
    print("  biggest falls: " + ("; ".join(falls) or "none"))
    print("  biggest rises: " + ("; ".join(rises) or "none"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save-baseline", action="store_true", help=f"write the current scores to {BASELINE_PATH.name}")
    args = parser.parse_args()

    current = run_panel()
    if args.save_baseline:
        payload = {
            "_meta": {
                "description": "Drink-level scores for the regression panel in scripts/eval_scoring.py. "
                "Regenerate with --save-baseline once a scoring change is approved.",
            },
            **current,
        }
        BASELINE_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"Saved the panel ({len(current['iba'])} IBA drinks) to {BASELINE_PATH.relative_to(ROOT)}")
        return
    if not BASELINE_PATH.exists():
        raise SystemExit(f"No baseline at {BASELINE_PATH.relative_to(ROOT)}; run with --save-baseline first.")
    with BASELINE_PATH.open(encoding="utf-8") as handle:
        baseline = json.load(handle)
    compare(baseline, current)


if __name__ == "__main__":
    main()
