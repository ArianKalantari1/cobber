#!/usr/bin/env python3
"""Normalize raw cocktail recipes into canonical Cobber ingredient ids.

Reads every corpus under ``data/raw/`` (TheCocktailDB dump + the IBA official
list), maps raw ingredient names to Cobber ids via the alias map and
exact/fuzzy matching, and writes the normalised recipe lists the NPMI step
consumes. Three behaviours matter beyond plain name-matching:

- **Label-first matching (IBA).** IBA entries often pair a generic ingredient
  ("Syrup", "Cherry liqueur", "Vermouth") with a ``label`` carrying the real
  identity ("Grenadine", "Maraschino", "Dry vermouth"). The label is matched
  first, falling back to the generic name.
- **Flavour decomposition.** Composites with a ``flavor_forward`` bill imply
  those components into the recipe (citron vodka puts vodka *and* lemon in the
  glass — the Cosmopolitan principle).
- **Dose gating.** A small pour is a modifier, not a flavour statement: half
  of all orange-liqueur pours in the corpus are <= 0.5 oz. When a composite's
  measure is known and below the threshold, its components are NOT implied
  (recorded as ``muted`` for review). Unknown measures imply as before.

Anything that can't be confidently matched is never guessed; it lands in
``data/unmatched_ingredients.txt`` with a count, for human review.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COCKTAILDB_RECIPES = ROOT / "data" / "raw" / "thecocktaildb.json"
IBA_RECIPES = ROOT / "data" / "raw" / "iba.json"
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
COMPOSITES_PATH = ROOT / "data" / "composites.json"
ALIASES_PATH = ROOT / "data" / "ingredient_aliases.json"
UNMATCHED_PATH = ROOT / "data" / "unmatched_ingredients.txt"
NORMALIZED_RECIPES_PATH = ROOT / "data" / "recipes_normalized.json"
COMPONENTS_PATH = ROOT / "data" / "recipes_components.json"

# Below this pour (in oz), a composite is a modifier dose and its
# flavor_forward components are not implied into the recipe.
DEFAULT_IMPLY_MIN_OZ = 0.6

TRAILING_PHRASES = (
    "freshly squeezed",
    "fresh",
    "juice",
)
STOP_WORDS = {
    "of",
    "a",
    "an",
    "the",
    "dash",
    "dashes",
    "slice",
    "slices",
    "wedge",
    "wedges",
    "piece",
    "pieces",
    "sprig",
    "sprigs",
    "leaf",
    "leaves",
    "cube",
    "cubes",
}
# Leading tokens stripped (repeatedly) from IBA free-text "special" entries
# such as "2 dashes Angostura Bitters" or "6 Mint sprigs" before matching.
SPECIAL_FILLER = {
    "dash", "dashes", "drop", "drops", "splash", "splashes", "teaspoon",
    "teaspoons", "tablespoon", "tablespoons", "bar", "spoon", "spoons",
    "cube", "cubes", "sprig", "sprigs", "leaf", "leaves", "few", "fresh",
    "raw", "plain", "top", "with", "to", "or", "small", "short", "strong",
    "clear", "half", "cut", "into", "and",
}

_FRACTION = r"\d+\s+\d+/\d+|\d+/\d+|\d*\.?\d+"
_MEASURE_RE = re.compile(
    rf"({_FRACTION})\s*(oz|ounce|ounces|cl|ml|tsp|teaspoon|teaspoons|"
    rf"tblsp|tbsp|tablespoon|tablespoons|shot|shots|part|parts|jigger|cup|cups|"
    rf"dash|dashes|splash|splashes|drop|drops)\b"
)
_UNIT_TO_OZ = {
    "oz": 1.0, "ounce": 1.0, "ounces": 1.0,
    "cl": 1 / 3, "ml": 1 / 30,
    "tsp": 1 / 6, "teaspoon": 1 / 6, "teaspoons": 1 / 6,
    "tblsp": 0.5, "tbsp": 0.5, "tablespoon": 0.5, "tablespoons": 0.5,
    "shot": 1.5, "shots": 1.5, "part": 1.0, "parts": 1.0, "jigger": 1.5,
    "cup": 8.0, "cups": 8.0,
    "dash": 0.03, "dashes": 0.03, "splash": 0.25, "splashes": 0.25,
    "drop": 0.01, "drops": 0.01,
}


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _fraction_to_float(text: str) -> float:
    text = text.strip()
    if " " in text and "/" in text:
        whole, frac = text.split(None, 1)
        num, den = frac.split("/")
        return float(whole) + float(num) / float(den)
    if "/" in text:
        num, den = text.split("/")
        return float(num) / float(den)
    return float(text)


def parse_measure_oz(measure: str | None) -> float | None:
    """Best-effort conversion of a free-text measure to ounces.

    Returns ``None`` when nothing parseable is found — the caller treats an
    unknown volume as "assume it matters" rather than guessing small.
    """
    if not measure:
        return None
    total = 0.0
    found = False
    for amount, unit in _MEASURE_RE.findall(measure.lower()):
        try:
            value = _fraction_to_float(amount)
        except (ValueError, ZeroDivisionError):
            continue
        total += value * _UNIT_TO_OZ[unit]
        found = True
    return total if found else None


def _clean_text(value: str) -> str:
    # Fold accents (Créme -> Creme, Curaçao -> Curacao) before stripping
    # non-ascii, or accented characters silently corrupt the token.
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\([^)]*\)", " ", value)  # "(small egg)", "(optional)"
    value = value.lower().strip()
    value = value.replace("&", " and ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def _singularize_token(token: str) -> str:
    if len(token) <= 3:
        return token
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith(("ches", "shes", "xes", "zes", "ses", "oes")) and len(token) > 4:
        return token[:-2]
    if token.endswith("s") and not token.endswith(("ss", "us", "is")):
        return token[:-1]
    return token


def normalize_name(name: str) -> str:
    text = _clean_text(name)
    if not text:
        return ""

    for phrase in TRAILING_PHRASES:
        if text.endswith(f" {phrase}"):
            text = text[: -len(phrase)].strip()
    if text.startswith("fresh "):
        text = text[len("fresh ") :].strip()

    tokens = [token for token in text.split(" ") if token and token not in STOP_WORDS]
    tokens = [_singularize_token(token) for token in tokens]
    return " ".join(tokens).strip()


def _build_known_maps() -> tuple[set[str], dict[str, str], dict[str, list[str]]]:
    ingredients = _load_json(INGREDIENTS_PATH)
    composites = _load_json(COMPOSITES_PATH)

    canonical_ids: set[str] = set()
    name_to_id: dict[str, str] = {}
    flavor_forward: dict[str, list[str]] = {}
    for entry in [*ingredients, *composites]:
        ingredient_id = entry["id"]
        canonical_ids.add(ingredient_id)

        display_name = normalize_name(entry["display_name"])
        id_text = normalize_name(ingredient_id.replace("_", " "))
        name_to_id.setdefault(id_text, ingredient_id)
        if display_name:
            name_to_id.setdefault(display_name, ingredient_id)
        forward = entry.get("flavor_forward")
        if isinstance(forward, list) and forward:
            flavor_forward[ingredient_id] = [str(item) for item in forward]
    return canonical_ids, name_to_id, flavor_forward


def _choose_fuzzy_match(normalized_raw: str, known_names: dict[str, str], cutoff: float = 0.93) -> str | None:
    candidates = difflib.get_close_matches(normalized_raw, known_names.keys(), n=2, cutoff=cutoff)
    if not candidates:
        return None
    best = candidates[0]
    if len(candidates) == 1:
        return known_names[best]

    best_ratio = difflib.SequenceMatcher(a=normalized_raw, b=best).ratio()
    second_ratio = difflib.SequenceMatcher(a=normalized_raw, b=candidates[1]).ratio()
    if best_ratio - second_ratio < 0.04:
        return None
    return known_names[best]


def _load_aliases() -> dict[str, str]:
    if not ALIASES_PATH.exists():
        return {}
    raw_aliases = _load_json(ALIASES_PATH)
    if not isinstance(raw_aliases, dict):
        raise ValueError("data/ingredient_aliases.json must contain a JSON object.")
    aliases: dict[str, str] = {}
    for raw_name, ingredient_id in raw_aliases.items():
        normalized = normalize_name(str(raw_name))
        if normalized and isinstance(ingredient_id, str):
            aliases[normalized] = ingredient_id
    return aliases


def _special_candidates(text: str) -> list[str]:
    """Candidate ingredient strings for an IBA free-text "special" entry.

    Strips leading quantities and filler ("2 dashes ", "6 ", "Top with ")
    one token at a time, yielding each remainder, so "3 dashes Strawberry
    syrup" offers "strawberry syrup" without ever guessing at the middle.
    """
    cleaned = _clean_text(text)
    tokens = cleaned.split(" ")
    candidates = [cleaned]
    while tokens and (tokens[0].replace("/", "").isdigit() or tokens[0] in SPECIAL_FILLER):
        tokens = tokens[1:]
        if tokens:
            candidates.append(" ".join(tokens))
    return candidates


def _iter_cocktaildb() -> list[dict]:
    """Yield drink records: {name, source, items: [(candidate_names, oz)]}."""
    payload = _load_json(COCKTAILDB_RECIPES)
    if not isinstance(payload, list):
        raise ValueError("data/raw/thecocktaildb.json must contain a JSON list.")
    drinks = []
    for drink in payload:
        if not isinstance(drink, dict):
            continue
        items = []
        for i in range(1, 16):
            value = drink.get(f"strIngredient{i}")
            if not isinstance(value, str) or not value.strip():
                continue
            volume = parse_measure_oz(drink.get(f"strMeasure{i}"))
            items.append(([value.strip()], volume))
        drinks.append({"name": str(drink.get("strDrink", "")), "source": "thecocktaildb", "items": items})
    return drinks


def _iter_iba() -> list[dict]:
    """Yield IBA drink records, matching labels before generic names."""
    if not IBA_RECIPES.exists():
        return []
    payload = _load_json(IBA_RECIPES)
    if not isinstance(payload, list):
        raise ValueError("data/raw/iba.json must contain a JSON list.")
    drinks = []
    for drink in payload:
        if not isinstance(drink, dict):
            continue
        items = []
        for item in drink.get("ingredients", []):
            if not isinstance(item, dict):
                continue
            if "ingredient" in item:
                candidates = []
                label = item.get("label")
                if isinstance(label, str) and label.strip():
                    candidates.append(label.strip())
                candidates.append(str(item["ingredient"]).strip())
                volume = None
                if item.get("unit") == "cl" and isinstance(item.get("amount"), (int, float)):
                    volume = float(item["amount"]) / 3  # 3 cl to the bar ounce
                items.append((candidates, volume))
            elif "special" in item:
                items.append((_special_candidates(str(item["special"])), None))
        drinks.append({"name": str(drink.get("name", "")), "source": "iba", "items": items})
    return drinks


def _dedupe_key(drink_name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", drink_name.lower())


def normalize_recipes(
    imply_min_oz: float = DEFAULT_IMPLY_MIN_OZ,
) -> tuple[list[list[str]], list[dict], dict[str, str], Counter[str]]:
    canonical_ids, known_names, flavor_forward = _build_known_maps()
    alias_map = _load_aliases()
    learned_aliases: dict[str, str] = {}
    unmatched = Counter()
    normalized_recipes: list[list[str]] = []
    component_records: list[dict] = []

    def match_one(candidates: list[str]) -> str | None:
        for raw_name in candidates:
            normalized_raw = normalize_name(raw_name)
            if not normalized_raw:
                continue
            chosen_id = alias_map.get(normalized_raw)
            if chosen_id is None:
                chosen_id = known_names.get(normalized_raw)
            if chosen_id is None:
                chosen_id = _choose_fuzzy_match(normalized_raw, known_names)
            if chosen_id is not None and chosen_id in canonical_ids:
                learned_aliases.setdefault(normalized_raw, chosen_id)
                return chosen_id
        return None

    # IBA first: when the same drink exists in both corpora, the official
    # recipe wins and the duplicate is skipped rather than double-counted.
    seen_names: set[str] = set()
    for drink in [*_iter_iba(), *_iter_cocktaildb()]:
        key = _dedupe_key(drink["name"])
        if key and key in seen_names:
            continue
        if key:
            seen_names.add(key)

        matched: dict[str, float | None] = {}
        for candidates, volume in drink["items"]:
            chosen_id = match_one(candidates)
            if chosen_id is None:
                primary = normalize_name(candidates[-1])
                if primary:
                    unmatched[primary] += 1
                continue
            # The same id twice (e.g. two syrups): keep the larger pour.
            if chosen_id in matched:
                old = matched[chosen_id]
                if old is not None and (volume is None or volume > old):
                    matched[chosen_id] = volume
            else:
                matched[chosen_id] = volume

        # A drink qualifies on its literal matches; flavour components are then
        # implied from each composite's flavor_forward bill — unless the pour
        # is a known modifier dose (below the threshold), in which case the
        # flavour is muted rather than implied.
        if len(matched) >= 2:
            implied: set[str] = set()
            muted: set[str] = set()
            for ingredient_id, volume in matched.items():
                components = flavor_forward.get(ingredient_id)
                if not components:
                    continue
                target = muted if (volume is not None and volume < imply_min_oz) else implied
                target.update(c for c in components if c not in matched)
            implied -= set(matched)
            muted -= set(matched) | implied
            normalized_recipes.append(sorted(set(matched) | implied))
            component_records.append(
                {
                    "drink": drink["name"],
                    "source": drink["source"],
                    "literal": sorted(matched),
                    "implied": sorted(implied),
                    "muted": sorted(muted),
                }
            )

    final_aliases = {**alias_map, **learned_aliases}
    return normalized_recipes, component_records, final_aliases, unmatched


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False, sort_keys=True)
        handle.write("\n")


def _write_unmatched(path: Path, unmatched: Counter[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for ingredient, count in sorted(unmatched.items(), key=lambda item: (-item[1], item[0])):
            handle.write(f"{count}\t{ingredient}\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize raw cocktail ingredients to Cobber ids.")
    parser.add_argument(
        "--imply-min-oz",
        type=float,
        default=DEFAULT_IMPLY_MIN_OZ,
        help=f"Minimum pour (oz) for a composite to imply its flavour components "
        f"(default: {DEFAULT_IMPLY_MIN_OZ}).",
    )
    args = parser.parse_args()

    normalized_recipes, component_records, aliases, unmatched = normalize_recipes(args.imply_min_oz)
    _write_json(NORMALIZED_RECIPES_PATH, normalized_recipes)
    _write_json(COMPONENTS_PATH, component_records)
    _write_json(ALIASES_PATH, aliases)
    _write_unmatched(UNMATCHED_PATH, unmatched)

    sources = Counter(record["source"] for record in component_records)
    muted_count = sum(1 for record in component_records if record["muted"])
    print(f"Wrote {len(normalized_recipes)} normalized recipes to {NORMALIZED_RECIPES_PATH} ({dict(sources)})")
    print(f"Wrote {len(component_records)} component records to {COMPONENTS_PATH} ({muted_count} with muted doses)")
    print(f"Wrote {len(aliases)} aliases to {ALIASES_PATH}")
    print(f"Wrote {sum(unmatched.values())} unmatched ingredient mentions to {UNMATCHED_PATH}")


if __name__ == "__main__":
    main()
