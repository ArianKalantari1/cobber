#!/usr/bin/env python3
"""Link ingredients to the non-volatile tastants that cause their taste axes.

This is the "why" behind Cobber's taste numbers: `lemon` isn't just `sour: 0.9`,
it's sour *because of* citric and malic acid. Each ingredient gets a `tastants`
field — a list of causal compound ids — kept SEPARATE from the aroma `compounds`
list so tastants never pollute the aroma-harmony Jaccard.

Only defensible, documented causes are asserted. Where a taste has no known
single molecule — the proprietary bitterness of Campari/Fernet/Cynar (secret
recipes), or `fat`/`funk` (texture / microbial-aromatic, not a basic taste) — the
ingredient is left WITHOUT that tastant on purpose. The engine then reports an
honest "provenance gap" rather than a fabricated principle.

Tastant compound ids must already exist in compound_descriptors.json (built by
fetch_descriptors.py) with a taste_class. Build-time, human-approved, idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
COMPOSITES_PATH = ROOT / "data" / "composites.json"
DESCRIPTORS_PATH = ROOT / "data" / "compound_descriptors.json"

# ingredient id -> causal tastant compound ids (documented causes only).
CURATED_TASTANTS: dict[str, list[str]] = {
    # ---- sour: organic acids ----
    "lemon":            ["citric_acid", "malic_acid"],
    "lime":             ["citric_acid", "malic_acid"],
    "grapefruit":       ["citric_acid", "malic_acid", "naringin"],
    "orange":           ["citric_acid", "malic_acid"],
    "apple":            ["malic_acid"],
    "pineapple":        ["citric_acid", "malic_acid"],
    "tomato":           ["citric_acid", "malic_acid", "glutamic_acid"],
    "tamarind":         ["tartaric_acid", "citric_acid", "glutamic_acid"],
    "hot_sauce":        ["acetic_acid", "sodium_chloride"],
    # ---- wine-based (tartaric) + wormwood bitterness (absinthin) ----
    "dry_vermouth":     ["tartaric_acid", "absinthin"],
    "sweet_vermouth":   ["tartaric_acid", "absinthin", "sucrose"],
    "sherry":           ["tartaric_acid"],
    # ---- sweeteners: sugars ----
    "sugar_syrup":      ["sucrose"],
    "brown_sugar":      ["sucrose"],
    "demerara":         ["sucrose"],
    "maple_syrup":      ["sucrose"],
    "grenadine":        ["sucrose"],
    "honey":            ["fructose", "glucose"],
    "agave":            ["fructose", "glucose"],
    # ---- sugar-sweetened liqueurs (added cane sugar = sucrose) ----
    "triple_sec":       ["sucrose"],
    "cointreau":        ["sucrose"],
    "limoncello":       ["sucrose", "citric_acid"],
    "maraschino":       ["sucrose"],
    "amaretto":         ["sucrose"],
    "creme_de_cacao":   ["sucrose"],
    "creme_de_menthe":  ["sucrose"],
    "blue_curacao":     ["sucrose"],
    "st_germain":       ["sucrose", "fructose"],
    "peach_schnapps":   ["sucrose"],
    "sambuca":          ["sucrose"],
    "galliano":         ["sucrose"],
    "anisette":         ["sucrose"],
    "coconut_liqueur":  ["sucrose"],
    "ginger_liqueur":   ["sucrose"],
    "allspice_dram":    ["sucrose"],
    "irish_cream":      ["sucrose"],
    "spiced_rum":       ["sucrose"],
    "creme_de_cassis":  ["sucrose", "malic_acid"],
    "raspberry_liqueur":["sucrose", "citric_acid"],
    "sloe_gin":         ["sucrose", "malic_acid"],
    "cherry_liqueur":   ["sucrose", "malic_acid"],
    "apricot_brandy":   ["sucrose", "malic_acid"],
    "calvados":         ["malic_acid"],
    "falernum":         ["sucrose", "citric_acid"],
    # honey-based liqueurs
    "drambuie":         ["fructose", "glucose"],
    "benedictine":      ["sucrose", "fructose"],
    # sweet amari (sugar is the sweetener; their BITTERNESS is proprietary -> gap)
    "campari":          ["sucrose"],
    "aperol":           ["sucrose"],
    "averna":           ["sucrose"],
    "amaro_montenegro": ["sucrose"],
    "green_chartreuse": ["sucrose"],
    "yellow_chartreuse":["sucrose"],
    "coffee_liqueur":   ["sucrose", "caffeine"],
    # ---- bitter: documented principles only ----
    "coffee":           ["caffeine"],
    "tonic_water":      ["quinine"],
    "angostura_bitters":["gentiopicroside", "amarogentin"],
    "peychauds_bitters":["gentiopicroside"],
    "orange_bitters":   ["gentiopicroside"],
    "absinthe":         ["absinthin"],
    # ---- umami + salty: the savoury crossovers ----
    "miso":             ["glutamic_acid", "sodium_chloride"],
    "shio_koji":        ["glutamic_acid", "sodium_chloride"],
    "soy_sauce":        ["glutamic_acid", "sodium_chloride"],
    "fish_sauce":       ["glutamic_acid", "inosinate", "sodium_chloride"],
    "worcestershire":   ["glutamic_acid", "inosinate", "acetic_acid", "sodium_chloride"],
    "mushroom":         ["glutamic_acid"],
    "olive":            ["glutamic_acid", "sodium_chloride"],
    "salt":             ["sodium_chloride"],
}


def main() -> None:
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        descriptors = json.load(handle)["compounds"]

    # Validate every tastant exists and carries a taste_class (never dangle a ref).
    for iid, tastants in CURATED_TASTANTS.items():
        for compound in tastants:
            rec = descriptors.get(compound)
            if rec is None:
                raise SystemExit(f"{iid}: tastant {compound!r} has no descriptor entry.")
            if not rec.get("taste_class"):
                raise SystemExit(f"{iid}: tastant {compound!r} has no taste_class.")

    touched = 0
    for path in (INGREDIENTS_PATH, COMPOSITES_PATH):
        with path.open(encoding="utf-8") as handle:
            entries = json.load(handle)
        by_id = {e["id"]: e for e in entries}
        changed = False
        for iid, tastants in CURATED_TASTANTS.items():
            entry = by_id.get(iid)
            if entry is None:
                continue
            have = list(entry.get("tastants", []))
            merged = have + [t for t in tastants if t not in have]
            if merged != have:
                entry["tastants"] = merged
                changed = True
                touched += 1
                print(f"  {iid}: tastants = {merged}")
        if changed:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(entries, handle, indent=2, ensure_ascii=False)
                handle.write("\n")

    unknown = [i for i in CURATED_TASTANTS if i not in _all_ids()]
    if unknown:
        print(f"NOTE: {len(unknown)} mapped ids not found in data (skipped): {unknown}")
    print(f"Linked tastants on {touched} ingredients.")
    print("Now rebuild descriptors coverage + run tests: "
          "python3 scripts/fetch_descriptors.py && python -m pytest tests/ -q")


def _all_ids() -> set[str]:
    ids: set[str] = set()
    for path in (INGREDIENTS_PATH, COMPOSITES_PATH):
        with path.open(encoding="utf-8") as handle:
            ids.update(e["id"] for e in json.load(handle))
    return ids


if __name__ == "__main__":
    main()
