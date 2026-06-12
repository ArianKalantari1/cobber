"""Build-time script: mine technique associations from TheCocktailDB + IBA.

Reads instruction text and ingredient lists from the two sources that carry
preparation data; extracts technique signals (shake/stir/build/blend/muddle)
and glass/service information; builds a frequency table of
ingredient-signal → technique; then writes the validated rule set to
data/technique_associations.json.

The rules themselves are based on bartender fundamentals — they are
VALIDATED by the data but not DERIVED from it (the causation runs the other
way: bartenders know to shake citrus). The data gives us confidence numbers
and surfaces surprises.

Usage:
    python3 scripts/mine_techniques.py
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COCKTAILDB_PATH = DATA_DIR / "raw" / "thecocktaildb.json"
IBA_PATH = DATA_DIR / "raw" / "iba.json"
OUTPUT_PATH = DATA_DIR / "technique_associations.json"


# ---------------------------------------------------------------------------
# Technique extraction from free-text instructions
# ---------------------------------------------------------------------------

def extract_technique(text: str) -> str | None:
    """Parse the dominant preparation technique from instruction text.

    Returns one of: shake, stir, build, blend, muddle_build, muddle_shake,
    dry_shake_first_shake, layer, throw — or None if not parseable.
    Priority order matters: check specific before generic.
    """
    if not text:
        return None
    t = text.lower()

    if "dry shake" in t or ("shake" in t and "without ice" in t):
        return "dry_shake_first_shake"
    if "blend" in t:
        return "blend"
    if "muddle" in t and "shake" in t:
        return "muddle_shake"
    if "muddle" in t:
        return "muddle_build"
    if "layer" in t or ("float" in t and "on top" in t):
        return "layer"
    if "throw" in t:
        return "throw"
    if "shake" in t:
        return "shake"
    if "stir" in t:
        return "stir"
    # "build", "pour", "fill", "add" all indicate building in the glass
    if "build" in t or "pour" in t or "fill" in t or "add" in t or "combine" in t:
        return "build"
    return None


def extract_glass(glass_text: str) -> str | None:
    """Normalise a glass field to one of: coupe, rocks, highball, flute,
    shot, tiki, wine, punch — or None."""
    if not glass_text:
        return None
    t = glass_text.lower()

    if "shot" in t or "shooter" in t:
        return "shot"
    if "highball" in t or "collins" in t or "tall glass" in t:
        return "highball"
    # old fashioned / lowball / rocks
    if "old-fashioned" in t or "old fashioned" in t or "rocks" in t or "lowball" in t:
        return "rocks"
    if "coupe" in t or "nick" in t:
        return "coupe"
    if "martini" in t or "cocktail glass" in t:
        return "coupe"   # modern equivalent
    if "champagne" in t or "flute" in t:
        return "flute"
    if "wine" in t:
        return "wine"
    if "tiki" in t or "mug" in t or "hurricane" in t or "zombie" in t:
        return "tiki"
    if "punch" in t or "bowl" in t:
        return "punch"
    return None


# ---------------------------------------------------------------------------
# Ingredient signal detection (build-time, from raw name strings)
# ---------------------------------------------------------------------------

_ACID_FRAGMENTS = [
    "lime juice", "lemon juice", "grapefruit juice", "orange juice",
    "juice of", " juice",
]
_EGG_WHITE_FRAGMENTS = ["egg white"]
_DAIRY_FRAGMENTS = ["cream", "milk", "butter", "egg yolk", "whole egg", "egg"]
_CARB_FRAGMENTS = [
    "soda water", "club soda", "soda,", " soda",
    "tonic water", "tonic,",
    "ginger beer", "ginger ale",
    "champagne", "prosecco", "cava", "sparkling wine", "sparkling,",
    "coca-cola", "cola,", " cola", "lemonade", "ginger beer",
]
_HERB_FRAGMENTS = ["mint", "basil", "cucumber", "muddled"]


def _has(ingredient_list: list[str], fragments: list[str]) -> bool:
    """Return True if any ingredient name contains any fragment."""
    for ing in ingredient_list:
        low = ing.lower()
        if any(frag in low for frag in fragments):
            return True
    return False


def detect_signals(ingredient_names: list[str]) -> dict[str, bool]:
    """Detect technique-relevant signals from a list of raw ingredient name strings."""
    has_egg_white = _has(ingredient_names, _EGG_WHITE_FRAGMENTS)
    has_dairy     = _has(ingredient_names, _DAIRY_FRAGMENTS)
    has_acid      = _has(ingredient_names, _ACID_FRAGMENTS)
    has_carb      = _has(ingredient_names, _CARB_FRAGMENTS)
    has_herb      = _has(ingredient_names, _HERB_FRAGMENTS)

    return {
        "has_egg_white":       has_egg_white,
        "has_dairy":           has_dairy and not has_egg_white,
        "has_acid":            has_acid,
        "has_carb":            has_carb,
        "has_herb":            has_herb,
        "has_acid_and_carb":         has_acid and has_carb and not has_herb,
        "has_herb_acid_and_carb":    has_herb and has_acid and has_carb,
        "has_carb_only":             has_carb and not has_acid and not has_dairy,
        "has_herb_no_acid":          has_herb and not has_acid,
        "spirit_only": (
            not has_acid and not has_dairy and not has_carb and not has_herb
        ),
    }


# ---------------------------------------------------------------------------
# Build evidence tables
# ---------------------------------------------------------------------------

def build_evidence(tdb_data: list[dict], iba_data: list[dict]) -> dict:
    """Annotate every recipe and aggregate signal → technique frequencies."""

    # Annotated recipes (for audit trail)
    annotated: list[dict] = []
    unannotated = 0

    for d in tdb_data:
        inst = d.get("strInstructions", "")
        tech = extract_technique(inst)
        glass = extract_glass(d.get("strGlass", ""))
        if tech is None:
            unannotated += 1
            continue
        ings = [
            d.get(f"strIngredient{i}", "") or ""
            for i in range(1, 16)
        ]
        annotated.append({
            "name": d.get("strDrink", ""),
            "source": "thecocktaildb",
            "technique": tech,
            "glass": glass,
            "signals": detect_signals(ings),
        })

    for d in iba_data:
        inst = d.get("preparation", "")
        tech = extract_technique(inst)
        glass = extract_glass(d.get("glass", ""))
        if tech is None:
            unannotated += 1
            continue
        ings = [i.get("ingredient", "") for i in d.get("ingredients", [])]
        annotated.append({
            "name": d.get("name", ""),
            "source": "iba",
            "technique": tech,
            "glass": glass,
            "signals": detect_signals(ings),
        })

    # Aggregate: signal → technique → count
    signal_order = [
        "has_egg_white", "has_dairy",
        "has_herb_acid_and_carb", "has_acid_and_carb", "has_acid",
        "has_carb_only", "has_herb", "has_herb_no_acid", "spirit_only",
    ]
    freq: dict[str, Counter] = {sig: Counter() for sig in signal_order}
    glass_freq: dict[str, Counter] = {sig: Counter() for sig in signal_order}

    for rec in annotated:
        for sig in signal_order:
            if rec["signals"].get(sig):
                freq[sig][rec["technique"]] += 1
                if rec["glass"]:
                    glass_freq[sig][rec["glass"]] += 1

    return {
        "annotated": annotated,
        "unannotated": unannotated,
        "technique_frequencies": {
            sig: dict(freq[sig]) for sig in signal_order
        },
        "glass_frequencies": {
            sig: dict(glass_freq[sig]) for sig in signal_order
        },
    }


def _confidence(signal_counts: Counter, expected_tech: str) -> tuple[float, int]:
    """Return (confidence, support) for a rule given its expected technique."""
    total = sum(signal_counts.values())
    if total == 0:
        return 0.0, 0
    return round(signal_counts.get(expected_tech, 0) / total, 2), total


# ---------------------------------------------------------------------------
# Derive rules
# ---------------------------------------------------------------------------

def build_rules(freq: dict[str, Counter], glass_freq: dict[str, Counter]) -> list[dict]:
    """Produce the priority-ordered rule set, annotated with data confidence.

    Rules are bartender fundamentals — the data VALIDATES them, not derives
    them.  Priority 1 wins; the engine stops at the first matching trigger.
    """
    rules = []

    # Rule 1: Egg white → dry-shake then shake, served up
    conf, sup = _confidence(freq["has_egg_white"], "shake")
    rules.append({
        "id": "egg_white",
        "priority": 1,
        "trigger": "has_egg_white",
        "method": "shake",
        "pre_steps": ["dry_shake"],
        "service": "up",
        "glass": "coupe",
        "ice_in_glass": False,
        "rationale": (
            "Egg white requires a dry shake (no ice) first to build foam, "
            "then a second shake with ice to dilute and chill."
        ),
        "data_confidence": conf,
        "data_support": sup,
        "notes": (
            "data_confidence reflects % of egg-white recipes with 'shake' in "
            "instructions; the dry-shake phase is often omitted from written "
            "recipes but is the correct bar technique."
        ),
    })

    # Rule 2: Carbonation-only lengthener (Highball family)
    conf, sup = _confidence(freq["has_carb_only"], "build")
    rules.append({
        "id": "highball_build",
        "priority": 2,
        "trigger": "has_carb_only",
        "method": "build",
        "pre_steps": [],
        "service": "highball",
        "glass": "highball",
        "ice_in_glass": True,
        "rationale": (
            "Spirit + carbonated lengthener is built over ice — shaking destroys fizz."
        ),
        "data_confidence": conf,
        "data_support": sup,
    })

    # Rule 3: Herb + acid + carbonation (Mojito / Smash Fizz family)
    # Muddle herbs first; then build over ice; top with soda. Never shake after
    # muddling — bruises herbs and turns the drink bitter and cloudy.
    rules.append({
        "id": "mojito_muddle_build",
        "priority": 3,
        "trigger": "has_herb_acid_and_carb",
        "method": "build",
        "pre_steps": ["muddle"],
        "service": "highball",
        "glass": "highball",
        "ice_in_glass": True,
        "carbonation_note": (
            "Muddle herbs gently with citrus and sweet in the glass; "
            "add spirit; fill with ice; top with carbonation."
        ),
        "rationale": (
            "Muddled-herb carbonated builds (Mojito, Smash Fizz): gentle muddling "
            "releases essential oils without bitterness; shaking after muddling "
            "bruises the herbs and clouds the drink."
        ),
        "data_confidence": None,
        "data_support": None,
    })

    # Rule 4: Acid + carbonation, no herbs (Collins / Fizz base)
    # Shake the base; add carbonation last. Service is highball.
    rules.append({
        "id": "sour_highball",
        "priority": 4,
        "trigger": "has_acid_and_carb",
        "method": "shake",
        "pre_steps": [],
        "service": "highball",
        "glass": "highball",
        "ice_in_glass": True,
        "carbonation_note": "Shake spirit + acid + sweet; strain over fresh ice; top with carbonation.",
        "rationale": (
            "Sour-highball builds (Collins, Fizz): shake the base, then top with "
            "soda or sparkling wine — never shake after adding carbonation."
        ),
        "data_confidence": None,
        "data_support": None,
        "notes": (
            "This trigger sits above plain 'has_acid' to ensure Collins/Fizz "
            "builds get highball service rather than coupe."
        ),
    })

    # Rule 5: Dairy (no egg white) → shake, served up
    conf, sup = _confidence(freq["has_dairy"], "shake")
    rules.append({
        "id": "dairy_shake",
        "priority": 5,
        "trigger": "has_dairy",
        "method": "shake",
        "pre_steps": [],
        "service": "up",
        "glass": "coupe",
        "ice_in_glass": False,
        "rationale": "Cream and dairy require vigorous shaking to emulsify.",
        "data_confidence": conf,
        "data_support": sup,
        "notes": (
            "data_confidence is lower than expected because the corpus includes "
            "layered cream drinks (Irish Coffee floats, Pousse-Café) and hot "
            "drinks where cream is a topping — these are not shaken."
        ),
    })

    # Rule 6: Acid (no carbonation) → shake, served up
    conf, sup = _confidence(freq["has_acid"], "shake")
    rules.append({
        "id": "acid_shake",
        "priority": 6,
        "trigger": "has_acid",
        "method": "shake",
        "pre_steps": [],
        "service": "up",
        "glass": "coupe",
        "ice_in_glass": False,
        "rationale": "Citrus juice requires shaking to integrate, aerate, and dilute.",
        "data_confidence": conf,
        "data_support": sup,
        "notes": (
            "data_confidence includes shots, hot drinks, and punches in the "
            "denominator — purely cocktail data would score higher."
        ),
    })

    # Rule 7: Fresh herb, no acid → muddle then build (Smash family)
    conf, sup = _confidence(freq["has_herb_no_acid"], "muddle_build")
    rules.append({
        "id": "herb_muddle_build",
        "priority": 7,
        "trigger": "has_herb_no_acid",
        "method": "build",
        "pre_steps": ["muddle"],
        "service": "rocks",
        "glass": "rocks",
        "ice_in_glass": True,
        "rationale": (
            "Fresh herbs are muddled gently to release essential oils; "
            "the drink is then built over crushed or cubed ice."
        ),
        "data_confidence": conf,
        "data_support": sup,
    })

    # Rule 8: Spirit-only → stir, serve on rocks (or up for spirit+vermouth)
    conf, sup = _confidence(freq["spirit_only"], "stir")
    rules.append({
        "id": "spirit_only_stir",
        "priority": 8,
        "trigger": "spirit_only",
        "method": "stir",
        "pre_steps": [],
        "service": "rocks",
        "glass": "rocks",
        "ice_in_glass": True,
        "rationale": (
            "Spirit-forward builds (Old Fashioned, Negroni, Manhattan) are stirred "
            "for clarity and gentle, controlled dilution — no acid to emulsify."
        ),
        "data_confidence": conf,
        "data_support": sup,
        "notes": (
            "Service is rocks by default. The host may suggest 'up' (coupe) for "
            "spirit+vermouth builds in the Martini/Manhattan family — the template "
            "context (Spirit+Vermouth vs Spirit-Forward) informs that call."
        ),
    })

    # Rule 9: Default fallback
    rules.append({
        "id": "default",
        "priority": 9,
        "trigger": "default",
        "method": "build",
        "pre_steps": [],
        "service": "rocks",
        "glass": "rocks",
        "ice_in_glass": True,
        "rationale": "Build over ice when no specific technique signal is present.",
        "data_confidence": None,
        "data_support": None,
    })

    return rules


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Mine technique associations.")
    parser.add_argument("--no-annotated", action="store_true",
                        help="Omit per-recipe annotations from output (smaller file).")
    args = parser.parse_args()

    with COCKTAILDB_PATH.open(encoding="utf-8") as fh:
        tdb_data = json.load(fh)
    with IBA_PATH.open(encoding="utf-8") as fh:
        iba_data = json.load(fh)

    print(f"TheCocktailDB: {len(tdb_data)} recipes")
    print(f"IBA:           {len(iba_data)} recipes")

    evidence = build_evidence(tdb_data, iba_data)
    annotated = evidence["annotated"]
    unannotated = evidence["unannotated"]
    freq = {sig: Counter(v) for sig, v in evidence["technique_frequencies"].items()}
    glass_freq = {sig: Counter(v) for sig, v in evidence["glass_frequencies"].items()}

    print(f"Annotated: {len(annotated)}, unannotated (no parseable technique): {unannotated}")

    # Print evidence summary
    print("\n=== Technique frequencies by ingredient signal ===")
    for sig, counts in freq.items():
        total = sum(counts.values())
        print(f"\n  {sig} (n={total}):")
        for tech, c in Counter(counts).most_common():
            pct = c / total * 100 if total else 0
            print(f"    {tech:28s} {c:3d}  ({pct:.0f}%)")

    rules = build_rules(freq, glass_freq)

    print("\n=== Rules derived ===")
    for r in rules:
        conf_str = f"  conf={r['data_confidence']:.0%}" if r["data_confidence"] is not None else ""
        pre = f"  pre_steps={r['pre_steps']}" if r["pre_steps"] else ""
        print(f"  [{r['priority']}] {r['id']:22s} → {r['method']:10s} svc={r['service']:8s}{pre}{conf_str}")

    output: dict = {
        "generated": "2026-06-12",
        "sources": {
            "thecocktaildb": len(tdb_data),
            "iba": len(iba_data),
        },
        "annotated": len(annotated),
        "unannotated": unannotated,
        "notes": (
            "Rules are bartender fundamentals validated (not derived) from data. "
            "data_confidence is the fraction of signal-matching recipes that "
            "followed the expected technique; low values reflect corpus noise "
            "(shots, hot drinks, punches share signals but differ in technique). "
            "PROVISIONAL — Ari to review rule priorities and rationale text."
        ),
        "technique_frequencies": evidence["technique_frequencies"],
        "glass_frequencies": evidence["glass_frequencies"],
        "rules": rules,
    }

    if not args.no_annotated:
        # Lightweight audit trail: name + source + technique + glass per recipe
        output["recipe_annotations"] = [
            {
                "name": rec["name"],
                "source": rec["source"],
                "technique": rec["technique"],
                "glass": rec["glass"],
            }
            for rec in annotated
        ]

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print(f"\nWrote {len(rules)} rules + {len(annotated)} annotations → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
