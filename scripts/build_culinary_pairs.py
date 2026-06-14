"""Build culinary_draft.json from The Flavor Bible network (reference-and-curate).

Downloads edges.json and nodes.json from brege/the-flavor-network at build time
(NOT committed to this repo — copyright belongs to Page & Dornenburg 2008).
Maps Cobber ingredient ids to Flavor Bible node ids via a hand-verified alias
table, extracts pairs where BOTH ingredients are known to Cobber, then writes
data/culinary_draft.json for Ari's review and approval.

NEVER run this as part of the server. It is a build-time, offline tool.
Output (culinary_draft.json) must be reviewed and approved by Ari before any
pair is promoted to culinary_pairs.json.

Usage:
    python3 scripts/build_culinary_pairs.py [--output data/culinary_draft.json]
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from datetime import date
from pathlib import Path

# ---------------------------------------------------------------------------
# Alias table: Cobber ingredient id  →  Flavor Bible node id
# Entries set to None are deliberately unmapped (ingredient absent from the
# Flavor Bible or where a safe 1:1 mapping cannot be made).
# ---------------------------------------------------------------------------
COBBER_TO_FB: dict[str, str | None] = {
    # --- Citrus ---
    "lemon": "lemon",
    "lime": "lime",
    "orange": "orange",
    "grapefruit": "grapefruit",
    "bitter_orange_peel": None,       # not a distinct FB node
    "lemongrass": "lemongrass",

    # --- Herbs ---
    "mint": "mint",
    "basil": "basil",
    "rosemary": "rosemary",
    "thyme": "thyme",
    "coriander_leaf": "cilantro",
    "sage": "sage",
    "lavender": "lavender",

    # --- Spices ---
    "cinnamon": "cinnamon",
    "cassia": None,                   # US sources treat as cinnamon; no separate FB node
    "clove": "cloves",
    "ginger": "ginger",
    "black_pepper": "pepper, black",
    "cardamom": "cardamom",
    "star_anise": "star anise",
    "anise": "anise",
    "nutmeg": "nutmeg",
    "vanilla": "vanilla",
    "allspice": "allspice",
    "caraway": "caraway",
    "juniper": "juniper berries",
    "coriander_seed": "coriander",
    "orris_root": None,               # no FB node
    "angelica_root": "angelica",
    "gentian": None,                  # no FB node
    "wormwood": None,                 # no FB node
    "pink_peppercorn": "pepper, pink",

    # --- Floral ---
    "elderflower": None,              # not in FB (food book; elderflower absent)

    # --- Nuts / Roasted ---
    "almond": "almonds",
    "coffee": "coffee",

    # --- Fruits ---
    "apple": "apples",
    "pear": "pears",
    "grape": "grapes",
    "pineapple": "pineapple",
    "strawberry": "strawberries",
    "raspberry": "raspberries",
    "peach": "peaches",
    "cherry": "cherries",
    "passionfruit": "passion fruit",
    "mango": "mango",
    "blackcurrant": "currants, black",
    "pomegranate": "pomegranate",
    "apricot": "apricots",
    "cranberry": "cranberries",

    # --- Sweeteners ---
    "sugar_syrup": "sugar",
    "honey": "honey",
    "agave": None,                    # not in FB
    "brown_sugar": "brown sugar",
    "demerara": None,                 # not in FB
    "kokuto": None,                   # Japanese; not in FB
    "maple_syrup": "maple syrup",
    "orgeat": None,                   # not in FB

    # --- Dairy / Egg ---
    "egg_white": "eggs",
    "egg_yolk": None,                 # cannot safely share "eggs" node with egg_white
    "cream": "cream",
    "milk": "milk",
    "butter": "butter",

    # --- Australian Natives (ALL absent from FB) ---
    "finger_lime": None,
    "desert_lime": None,
    "lemon_myrtle": None,
    "lemon_aspen": None,
    "anise_myrtle": None,
    "cinnamon_myrtle": None,
    "riberry": None,
    "pepperberry": None,
    "wattleseed": None,
    "davidson_plum": None,
    "quandong": None,
    "muntries": None,
    "bush_tomato": None,
    "strawberry_gum": None,
    "native_river_mint": None,

    # --- Beverages / Mixers ---
    "soda_water": None,
    "tonic_water": None,
    "cola": None,

    # --- Vegetables ---
    "tomato": "tomatoes",
    "celery": "celery",
    "olive": "olives",

    # --- Umami / Fermented ---
    "miso": "miso",
    "shio_koji": None,
    "soy_sauce": "soy sauce",
    "worcestershire": "worcestershire sauce",
    "fish_sauce": "fish sauce",
    "hot_sauce": None,

    # --- Wines / Fortified ---
    "red_wine": "dry red wine",
    "port": "port",
    "sparkling_wine": "sparkling wine",

    # --- Other ---
    "coconut": "coconut",
    "tamarind": "tamarind",
    "salt": "salt",
    "mushroom": "mushrooms",
}

# ---------------------------------------------------------------------------
FB_BASE = (
    "https://raw.githubusercontent.com/brege/the-flavor-network"
    "/main/site/static/data/flavor"
)


def fetch_json(url: str) -> object:
    print(f"  Fetching {url}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read())


def build_reverse_map(cobber_to_fb: dict[str, str | None]) -> dict[str, str]:
    """Return fb_node_id → cobber_id, skipping None-mapped entries.

    Raises if two Cobber ids map to the same FB node (would create ambiguous
    reverse-lookup and could silently lose pairs).
    """
    fb_to_cobber: dict[str, str] = {}
    for cobber_id, fb_id in cobber_to_fb.items():
        if fb_id is None:
            continue
        if fb_id in fb_to_cobber:
            raise ValueError(
                f"Two Cobber ids ({fb_to_cobber[fb_id]!r}, {cobber_id!r}) "
                f"both map to FB node {fb_id!r}. Fix the alias table."
            )
        fb_to_cobber[fb_id] = cobber_id
    return fb_to_cobber


def validate_aliases_against_nodes(
    fb_to_cobber: dict[str, str], fb_node_ids: set[str]
) -> None:
    """Warn about alias targets that don't exist in the downloaded nodes."""
    bad = [fb_id for fb_id in fb_to_cobber if fb_id not in fb_node_ids]
    if bad:
        print(
            f"\nWARNING: {len(bad)} alias target(s) not found in nodes.json "
            f"— they will match nothing:\n  " + "\n  ".join(sorted(bad))
        )


def extract_pairs(
    edges: list[dict],
    fb_to_cobber: dict[str, str],
) -> list[dict]:
    """Return draft pairs for edges where both endpoints map to Cobber ids."""
    seen: dict[frozenset, int] = {}  # frozenset(cobber pair) → max fb_weight
    for edge in edges:
        a_fb = edge.get("from", "")
        b_fb = edge.get("to", "")
        a_cobber = fb_to_cobber.get(a_fb)
        b_cobber = fb_to_cobber.get(b_fb)
        if a_cobber is None or b_cobber is None:
            continue
        if a_cobber == b_cobber:
            continue
        key = frozenset((a_cobber, b_cobber))
        weight = int(edge.get("weight", 1))
        # If the same pair appears via multiple FB alias paths, keep max weight.
        seen[key] = max(seen.get(key, 0), weight)

    pairs: list[dict] = []
    for key, weight in seen.items():
        a, b = sorted(key)
        pairs.append(
            {
                "pair": [a, b],
                "fb_weight": weight,
                "affinity_score": round(weight / 4, 4),
                "fb_nodes": [
                    COBBER_TO_FB.get(a, "?"),
                    COBBER_TO_FB.get(b, "?"),
                ],
                "source": "The Flavor Bible (Page & Dornenburg, 2008) — consulted reference",
                "ari_approved": None,
                "note": "",
            }
        )
    pairs.sort(key=lambda p: (-p["fb_weight"], p["pair"][0], p["pair"][1]))
    return pairs


def coverage_report(cobber_to_fb: dict[str, str | None]) -> dict:
    mapped = [c for c, f in cobber_to_fb.items() if f is not None]
    unmapped = [c for c, f in cobber_to_fb.items() if f is None]
    return {
        "total_cobber_ids": len(cobber_to_fb),
        "mapped_to_fb": len(mapped),
        "unmapped": unmapped,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="data/culinary_draft.json",
        help="Output path (default: data/culinary_draft.json)",
    )
    args = parser.parse_args()
    output_path = Path(args.output)

    print("Building Flavor Bible reverse alias map …")
    fb_to_cobber = build_reverse_map(COBBER_TO_FB)

    print("Downloading nodes.json …")
    nodes = fetch_json(f"{FB_BASE}/nodes.json")
    fb_node_ids = {n["id"] for n in nodes}
    validate_aliases_against_nodes(fb_to_cobber, fb_node_ids)

    print("Downloading edges.json …")
    edges = fetch_json(f"{FB_BASE}/edges.json")
    print(f"  {len(edges)} edges loaded")

    print("Extracting Cobber-covered pairs …")
    pairs = extract_pairs(edges, fb_to_cobber)
    print(f"  {len(pairs)} unique pairs found")

    cov = coverage_report(COBBER_TO_FB)
    print(
        f"  Coverage: {cov['mapped_to_fb']}/{cov['total_cobber_ids']} Cobber ids "
        f"mapped to a FB node"
    )

    by_weight = {}
    for p in pairs:
        w = p["fb_weight"]
        by_weight[w] = by_weight.get(w, 0) + 1
    print("  By FB weight:", dict(sorted(by_weight.items(), reverse=True)))

    output = {
        "meta": {
            "description": (
                "DRAFT — awaiting Ari's approval. "
                "Pairs extracted from The Flavor Bible network (brege/the-flavor-network, "
                "MIT code licence; book content © Page & Dornenburg 2008). "
                "DO NOT commit this file as-is. Ari must set ari_approved=true "
                "on each accepted pair; approved pairs are then promoted to "
                "culinary_pairs.json by hand."
            ),
            "source_reference": "The Flavor Bible, Karen Page & Andrew Dornenburg (2008)",
            "extraction_credit": "brege/the-flavor-network (MIT, © 2023 Wyatt Brege)",
            "fb_weight_semantics": {
                "1": "standard mention (normal type)",
                "2": "recommended (bold)",
                "3": "highly recommended (BOLD CAPS)",
                "4": "holy grail pairing (starred)",
            },
            "affinity_score_formula": "fb_weight / 4  →  [0.25, 0.50, 0.75, 1.00]",
            "generated": str(date.today()),
            "pair_count": len(pairs),
            "coverage": cov,
        },
        "pairs": pairs,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n")
    print(f"\nWrote {output_path}  ({len(pairs)} draft pairs)")
    print(
        "\nNext step: open data/culinary_draft.json, review each pair,\n"
        'set ari_approved=true on accepted pairs, then copy accepted rows\n'
        "into data/culinary_pairs.json with any adjusted notes."
    )


if __name__ == "__main__":
    main()
