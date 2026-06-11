#!/usr/bin/env python3
"""Normalize raw cocktail ingredients into canonical Cobber ingredient ids."""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_RECIPES = ROOT / "data" / "raw" / "thecocktaildb.json"
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
COMPOSITES_PATH = ROOT / "data" / "composites.json"
ALIASES_PATH = ROOT / "data" / "ingredient_aliases.json"
UNMATCHED_PATH = ROOT / "data" / "unmatched_ingredients.txt"
NORMALIZED_RECIPES_PATH = ROOT / "data" / "recipes_normalized.json"

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
}


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _clean_text(value: str) -> str:
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


def _build_known_maps() -> tuple[set[str], dict[str, str]]:
    ingredients = _load_json(INGREDIENTS_PATH)
    composites = _load_json(COMPOSITES_PATH)

    canonical_ids: set[str] = set()
    name_to_id: dict[str, str] = {}
    for entry in [*ingredients, *composites]:
        ingredient_id = entry["id"]
        canonical_ids.add(ingredient_id)

        display_name = normalize_name(entry["display_name"])
        id_text = normalize_name(ingredient_id.replace("_", " "))
        name_to_id.setdefault(id_text, ingredient_id)
        if display_name:
            name_to_id.setdefault(display_name, ingredient_id)
    return canonical_ids, name_to_id


def _extract_raw_ingredients(drink: dict) -> list[str]:
    names: list[str] = []
    for i in range(1, 16):
        key = f"strIngredient{i}"
        value = drink.get(key)
        if isinstance(value, str):
            stripped = value.strip()
            if stripped:
                names.append(stripped)
    return names


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


def normalize_recipes() -> tuple[list[list[str]], dict[str, str], Counter[str]]:
    raw_recipes = _load_json(RAW_RECIPES)
    if not isinstance(raw_recipes, list):
        raise ValueError("data/raw/thecocktaildb.json must contain a JSON list.")

    canonical_ids, known_names = _build_known_maps()
    alias_map = _load_aliases()
    learned_aliases: dict[str, str] = {}
    unmatched = Counter()
    normalized_recipes: list[list[str]] = []

    for drink in raw_recipes:
        if not isinstance(drink, dict):
            continue
        matched_ids: set[str] = set()
        for raw_name in _extract_raw_ingredients(drink):
            normalized_raw = normalize_name(raw_name)
            if not normalized_raw:
                continue

            chosen_id = alias_map.get(normalized_raw)
            if chosen_id is None:
                chosen_id = known_names.get(normalized_raw)
            if chosen_id is None:
                chosen_id = _choose_fuzzy_match(normalized_raw, known_names)

            if chosen_id is None or chosen_id not in canonical_ids:
                unmatched[normalized_raw] += 1
                continue

            learned_aliases.setdefault(normalized_raw, chosen_id)
            matched_ids.add(chosen_id)

        if len(matched_ids) >= 2:
            normalized_recipes.append(sorted(matched_ids))

    final_aliases = {**alias_map, **learned_aliases}
    return normalized_recipes, final_aliases, unmatched


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
    parser.parse_args()

    normalized_recipes, aliases, unmatched = normalize_recipes()
    _write_json(NORMALIZED_RECIPES_PATH, normalized_recipes)
    _write_json(ALIASES_PATH, aliases)
    _write_unmatched(UNMATCHED_PATH, unmatched)

    print(f"Wrote {len(normalized_recipes)} normalized recipes to {NORMALIZED_RECIPES_PATH}")
    print(f"Wrote {len(aliases)} aliases to {ALIASES_PATH}")
    print(f"Wrote {sum(unmatched.values())} unmatched ingredient mentions to {UNMATCHED_PATH}")


if __name__ == "__main__":
    main()
