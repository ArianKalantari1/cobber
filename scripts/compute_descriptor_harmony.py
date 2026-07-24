#!/usr/bin/env python3
"""Mine flavour-family co-occurrence ("harmonious notes") from Cobber's corpus.

This is the descriptor-level analogue of the tradition table, built with the same
machinery: for every recipe we resolve which flavour families are present (by
mapping each ingredient's compounds through their descriptors into families), then
score how often each pair of families co-occurs. Two numbers per family pair:

  * ``npmi``    — normalised pointwise mutual information (co-occurrence above
                  chance), exactly as ``compute_npmi.py`` does for ingredient pairs.
  * ``harmony`` — log-scaled prevalence ``log1p(count)/log1p(max_count)``, the same
                  transform ``write_tradition.py`` uses, so "how often do these two
                  notes actually turn up together" reads on a 0..1 scale that does
                  not zero out the ubiquitous combos (citrus + sweet).

The signal is generated from Cobber's OWN recipe corpus (data/recipes_normalized.json)
— no external pairing claims. Output: data/descriptor_harmony.json, read by
engine.harmonious_notes / harmonious_families.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RECIPES_PATH = DATA / "recipes_normalized.json"
INGREDIENTS_PATH = DATA / "ingredients.json"
COMPOSITES_PATH = DATA / "composites.json"
DESCRIPTORS_PATH = DATA / "compound_descriptors.json"
FAMILIES_PATH = DATA / "flavor_families.json"
OUTPUT_PATH = DATA / "descriptor_harmony.json"


def _load_ingredient_families() -> dict[str, frozenset[str]]:
    """Map every ingredient id -> the set of flavour families it carries.

    Raw ingredients use their declared compounds; composites use the union of
    their botanicals' compounds (the same derivation the data layer does). Each
    compound's odour words are resolved to families via the approved family map.
    """
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        compound_desc = json.load(handle)["compounds"]
    with FAMILIES_PATH.open(encoding="utf-8") as handle:
        odor_families = json.load(handle)["odor_families"]
    word_to_family = {w: fam for fam, words in odor_families.items() for w in words}

    def compound_families(compound_id: str) -> set[str]:
        record = compound_desc.get(compound_id)
        if not record:
            return set()
        return {
            word_to_family[w]
            for w in record.get("odor", [])
            if w in word_to_family
        }

    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        raw_entries = json.load(handle)
    raw_compounds: dict[str, list[str]] = {
        e["id"]: list(e.get("compounds", [])) for e in raw_entries
    }

    families: dict[str, frozenset[str]] = {}
    for entry in raw_entries:
        fams: set[str] = set()
        for compound in entry.get("compounds", []):
            fams |= compound_families(compound)
        families[entry["id"]] = frozenset(fams)

    with COMPOSITES_PATH.open(encoding="utf-8") as handle:
        composite_entries = json.load(handle)
    for entry in composite_entries:
        fams = set()
        for botanical in entry.get("botanicals", []):
            for compound in raw_compounds.get(botanical, []):
                fams |= compound_families(compound)
        families[entry["id"]] = frozenset(fams)

    return families


def _load_recipes(path: Path) -> list[list[str]]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    recipes: list[list[str]] = []
    for recipe in payload:
        if isinstance(recipe, list):
            recipes.append([str(x).strip() for x in recipe if str(x).strip()])
    return recipes


def compute(recipes: list[list[str]], ingredient_families: dict[str, frozenset[str]]) -> list[dict]:
    """Return family-pair rows with count, npmi, and log-prevalence harmony."""
    family_counts: Counter[str] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()
    total = 0

    for recipe in recipes:
        present: set[str] = set()
        for ingredient_id in recipe:
            present |= ingredient_families.get(ingredient_id, frozenset())
        if len(present) < 1:
            continue
        total += 1
        family_counts.update(present)
        for a, b in combinations(sorted(present), 2):
            pair_counts[(a, b)] += 1

    if not pair_counts:
        return []

    max_count = max(pair_counts.values())
    log_max = math.log1p(max_count)

    rows: list[dict] = []
    for (a, b), count in pair_counts.items():
        p_a = family_counts[a] / total
        p_b = family_counts[b] / total
        p_ab = count / total
        pmi = math.log(p_ab / (p_a * p_b))
        npmi = 1.0 if p_ab == 1.0 else pmi / (-math.log(p_ab))
        harmony = (math.log1p(count) / log_max) if log_max > 0 else 0.0
        rows.append(
            {
                "pair": [a, b],
                "count": count,
                "npmi": round(npmi, 6),
                "harmony": round(harmony, 6),
            }
        )

    rows.sort(key=lambda r: (r["harmony"], r["count"], r["pair"]), reverse=True)
    return rows


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recipes", type=Path, default=RECIPES_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    ingredient_families = _load_ingredient_families()
    recipes = _load_recipes(args.recipes)
    rows = compute(recipes, ingredient_families)

    payload = {
        "_meta": {
            "description": "Flavour-family co-occurrence ('harmonious notes') mined from the recipe corpus.",
            "generated_by": "scripts/compute_descriptor_harmony.py",
            "source_corpus": "data/recipes_normalized.json (Cobber's own canon corpus)",
            "npmi": "normalised PMI, co-occurrence above chance (per compute_npmi.py).",
            "harmony": "log-scaled prevalence log1p(count)/log1p(max_count), 0..1 (per write_tradition.py).",
            "recipes_used": len(recipes),
            "pair_count": len(rows),
        },
        "pairs": rows,
    }
    _write_json(args.output, payload)
    print(f"Wrote {len(rows)} family-pair rows from {len(recipes)} recipes -> {args.output}")


if __name__ == "__main__":
    main()
