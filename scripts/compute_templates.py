#!/usr/bin/env python3
"""Discover proportion templates from the cocktailapp recipe corpus.

Clusters the ~9,800 cocktailapp recipes by their functional-role proportion
structure to learn canonical template shapes: Sour, Old Fashioned, Negroni
(equal-thirds), Highball, Flip, etc.  Build-time script — output is committed
to data/proportion_templates.json for Ari's naming/approval before it is
wired into the engine.

Algorithm
---------
1. Classify each ingredient into one of nine functional roles (spirit, liqueur,
   amaro, vermouth_fortified, acid, sweet, juice_mixer, lengthener, egg_cream).
   Bitters are tracked but excluded from the clustering vector because their
   sub-5% volumes distort centroid distances without adding template signal.
2. Sum ingredient proportions by role → a 9-dimensional vector per drink.
3. Discard drinks where > 30% of proportioned volume is unclassified.
4. K-means clustering (k=5..15); pick k with the highest silhouette score,
   printing the elbow data for inspection.
5. For each cluster: compute centroid, collect representative examples, suggest
   a provisional template name.

Output: data/proportion_templates.json  (PROVISIONAL — naming/judgment is Ari's).
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[1]
COCKTAILAPP_PATH = ROOT / "data" / "raw" / "cocktailapp_recipes.json"
OUTPUT_PATH = ROOT / "data" / "proportion_templates.json"

# Nine functional roles that define a drink's structural shape.
# "bitter" and "other" are tracked separately but not in the clustering vector.
ROLES = [
    "spirit",
    "liqueur",
    "amaro",
    "vermouth_fortified",
    "acid",
    "sweet",
    "juice_mixer",
    "lengthener",
    "egg_cream",
]


# ---------------------------------------------------------------------------
# Role classifier
# Each entry is (role, [substring, ...]).  Checks are lowercase; the first
# matching rule wins.  Order matters — more specific patterns come first.
# ---------------------------------------------------------------------------

def _make_checker(fragments: list[str]):
    """Return a function that tests whether any fragment is in a lowercase string."""
    return lambda s: any(f in s for f in fragments)


_EGG_CREAM_CHECK = _make_checker([
    "egg white", "egg yolk", "whole egg", "pasteurised egg", "eggs",
    "single cream", "heavy cream", "double cream", "whipping cream",
    "half-and-half", "ice-cream", "ice cream", "buttermilk", "yogurt",
    "butter ", "cream cheese",
])

_EGG_CREAM_MILK_CHECK = _make_checker([" milk", "soy milk", "almond milk", "oat milk"])

_BITTER_CHECK = _make_checker(["bitters", " bitter"])

_LENGTHENER_CHECK = _make_checker([
    "soda water", "club soda", "soda from siphon",
    "tonic water", "tonic",
    "ginger beer", "ginger ale",
    "champagne", "prosecco", "cava", "crémant", "cremant",
    "sparkling wine", "sparkling",
    "cola", "lemonade", "iced tea", "kombucha",
])

# Plain "water" but not flower water, rose water, coconut water (those go to juice_mixer)
_WATER_CHECK = re.compile(r"\bwater\b(?! of|\s+of|\s*kefir)")

_ACID_CHECK = _make_checker([
    "lime juice", "lemon juice",
    "citric acid", "lemon acid", "lime acid",
    "citrus juice",
])

_SWEET_CHECK = _make_checker([
    "sugar syrup", "simple syrup", "sirop de gomme", "gomme syrup",
    "honey syrup", "honey water", "runny honey", "clear honey",
    "agave syrup", "agave nectar", "agave",
    "demerara syrup", "demerara",
    "grenadine", "gomme", "cordial",
    "raspberry syrup", "passion fruit syrup",
    "mint syrup", "vanilla syrup", "lavender syrup",
    "cinnamon syrup", "ginger syrup", "pineapple syrup",
    "lemon syrup", "lime syrup", "citrus syrup",
    " syrup",          # generic catch-all after specifics
    "sugar", "honey", "maple", "molasses", "treacle",
    "caster sugar", "powdered sugar", "icing sugar",
    "orgeat",          # almond sweetener — sweet role for template purposes
])

_AMARO_CHECK = _make_checker([
    "campari", "aperol", "cynar", "fernet",
    " amaro", "amaro ", "cardamaro",
    "chartreuse", "byrrh", "punt e mes", "suze",
    "bonal ", "luxardo bitter", "torani amer",
    "picon", "amer picon", "averna", "ramazzotti",
    "braulio", "becherovka", "unicum", "zwack",
    "nardini", "meletti", "nonino", "montenegro",
    "sfumato", "select aperitivo",
    "abano", "bitterzoet", "jagermeister",
])

_VERMOUTH_CHECK = _make_checker([
    "vermouth", "sherry", "port ", "madeira",
    "dubonnet", "lillet", "cocchi",
    "aromatized wine", "quinquina",
    "pineau des charentes", "muscat",
])

_LIQUEUR_CHECK = _make_checker([
    "liqueur",
    "triple sec", "grand marnier", "cointreau",
    "maraschino",
    "falernum", "velvet falernum",
    "creme de", "crème de",
    "curacao",
    "elderflower",
    "chambord", "benedictine",
    "allspice dram",
    "schnapps", "schnaps",
    "disaronno", "kahlua", "kahlu",
    "baileys", "amaretto",
    "frangelico", "limoncello", "midori",
    "pimm", "sloe gin",
    "drambuie", "strega",
    "absinthe", "pastis", "pernod",
])

_JUICE_MIXER_CHECK = _make_checker([
    "juice", "nectar",
    "coconut water",
    " tea", "earl grey", "green tea", "black tea",
    "cold brew", "coffee", "espresso",
    "tomato", "cucumber", "carrot", "celery",
    "flower water", "rose water",
])

_SPIRIT_CHECK = _make_checker([
    "rum", "gin", "vodka",
    "whiskey", "whisky", "bourbon", "rye", "scotch",
    "tequila", "mezcal",
    "brandy", "cognac", "calvados", "armagnac",
    "pisco", "grappa",
    "sake", "shochu", "aquavit", "baijiu", "arak", "ouzo", "jenever",
    "overproof",
])


def classify_role(name: str) -> str:
    """Map a raw ingredient name to one of ROLES, 'bitter', or 'other'."""
    s = name.lower().strip()

    # Dairy / egg — check before cream-liqueur patterns
    if _EGG_CREAM_CHECK(s):
        # Exclude cream liqueurs: "baileys irish cream", "cream liqueur"
        if "liqueur" not in s and "irish cream" not in s and "advocaat" not in s:
            return "egg_cream"
    if _EGG_CREAM_MILK_CHECK(s):
        if "coconut milk" not in s and "almond milk" not in s and "oat milk" not in s:
            return "egg_cream"

    # Bitters (small aromatic doses — tracked but not in vector)
    if _BITTER_CHECK(s):
        # Must not be amaro-class
        if not any(x in s for x in ["campari", "aperol", "fernet", "amaro", "cynar"]):
            return "bitter"

    # Lengtheners / carbonated
    if _LENGTHENER_CHECK(s):
        return "lengthener"
    if _WATER_CHECK.search(s) and "rose water" not in s and "flower water" not in s:
        return "lengthener"

    # Structural acid (lime/lemon juice specifically)
    if _ACID_CHECK(s):
        return "acid"

    # Sweeteners — before liqueur so syrups/honey don't misfire
    if _SWEET_CHECK(s):
        # Exclude anything that's clearly a spirit-class bottle
        if not any(x in s for x in ["liqueur", "brandy", "rum", "whisky", "whiskey"]):
            return "sweet"

    # Amaro / bitter-sweet modifiers (Campari, Aperol, Cynar, Chartreuse, ...)
    if _AMARO_CHECK(s):
        return "amaro"

    # Fortified wine / aromatized wine
    if _VERMOUTH_CHECK(s):
        return "vermouth_fortified"

    # Liqueur / sweetened spirit modifiers
    if _LIQUEUR_CHECK(s):
        return "liqueur"

    # Non-acid fruit juices and other liquid mixers
    if _JUICE_MIXER_CHECK(s):
        return "juice_mixer"

    # Base spirits
    if _SPIRIT_CHECK(s):
        return "spirit"

    return "other"


# ---------------------------------------------------------------------------
# Build role-proportion vectors
# ---------------------------------------------------------------------------

def build_vectors(
    data: list[dict],
    max_other_frac: float = 0.30,
) -> tuple[np.ndarray, list[dict]]:
    """Return (matrix, metadata) for drinks with classifiable proportions.

    Rows are 9-dim normalised role vectors (bitters and 'other' excluded).
    metadata[i] carries the drink name, proportions, and role breakdown.
    """
    vectors: list[np.ndarray] = []
    metadata: list[dict] = []

    for drink in data:
        ings = drink["ingredients"]
        role_sum: dict[str, float] = defaultdict(float)
        bitter_sum = 0.0
        prop_total = 0.0

        for ing in ings:
            p = ing.get("proportion")
            if p is None:
                continue
            role = classify_role(ing["name"])
            prop_total += p
            if role == "bitter":
                bitter_sum += p
            elif role == "other":
                pass  # tracked separately
            else:
                role_sum[role] += p

        # Skip drink if proportion data is absent or malformed
        if prop_total < 0.5:
            continue
        # The one duplicate-entry drink (sum=2.0)
        if prop_total > 1.1:
            continue

        # Fraction of proportioned volume that is 'other' (unclassified)
        classified = sum(role_sum.values())
        other_frac = (prop_total - classified - bitter_sum) / prop_total
        if other_frac > max_other_frac:
            continue

        # Build vector over the 9 ROLES (bitters excluded)
        vec = np.array([role_sum.get(r, 0.0) for r in ROLES], dtype=float)

        # Renormalise to sum-to-1 so absolute volume doesn't affect distance
        vsum = vec.sum()
        if vsum < 0.1:
            continue
        vec /= vsum

        vectors.append(vec)
        metadata.append({
            "name": drink["name"],
            "source": drink.get("source", ""),
            "proportions": {r: round(role_sum.get(r, 0.0), 4) for r in ROLES},
            "bitter_frac": round(bitter_sum / prop_total, 4) if prop_total else 0.0,
            "other_frac": round(other_frac, 4),
        })

    return np.array(vectors), metadata


# ---------------------------------------------------------------------------
# Ratio string helpers
# ---------------------------------------------------------------------------

def _ratio_string(centroid: dict[str, float], top_n: int = 3) -> tuple[str, str]:
    """Return (ratio_str, role_labels) for the dominant roles.

    E.g. spirit 0.57, acid 0.28, sweet 0.14  →  "2:1:½", "spirit:acid:sweet"
    """
    # Keep only roles with ≥ 3% of the vector
    significant = [(v, r) for r, v in centroid.items() if v >= 0.03]
    significant.sort(reverse=True)
    significant = significant[:top_n]

    if not significant:
        return "—", "—"

    fracs = [v for v, _ in significant]
    roles = ":".join(r for _, r in significant)

    # Scale so the smallest significant fraction becomes 1
    min_frac = min(fracs)
    scaled = [f / min_frac for f in fracs]

    # Round to nearest 0.5
    def _round_half(x: float) -> float:
        return round(x * 2) / 2

    parts = []
    for x in scaled:
        r = _round_half(x)
        if r == int(r):
            parts.append(str(int(r)))
        else:
            parts.append(f"{r:.1f}")

    return ":".join(parts), roles


# ---------------------------------------------------------------------------
# Template naming heuristics (provisional — Ari's to override)
# ---------------------------------------------------------------------------

def _suggest_name(centroid: dict[str, float]) -> str:
    spirit = centroid.get("spirit", 0)
    acid = centroid.get("acid", 0)
    sweet = centroid.get("sweet", 0)
    liqueur = centroid.get("liqueur", 0)
    amaro = centroid.get("amaro", 0)
    verm = centroid.get("vermouth_fortified", 0)
    lengthener = centroid.get("lengthener", 0)
    juice = centroid.get("juice_mixer", 0)
    egg = centroid.get("egg_cream", 0)

    # Spirit-forward
    if spirit > 0.70:
        return "Spirit-Forward"

    # Highball / long drink
    if lengthener > 0.45:
        return "Highball"

    # Flip / egg sour
    if egg > 0.08:
        if acid > 0.10:
            return "Flip / Egg Sour"
        return "Cream Build"

    # Sour: structural acid present, no lengthener
    if spirit > 0.35 and acid > 0.15 and lengthener < 0.15:
        if sweet > 0.08:
            if liqueur > 0.18:
                return "Sour + Liqueur"
            return "Sour"
        return "Sour (dry)"

    # Tropical / tiki — juice dominant
    if juice > 0.45:
        return "Tropical / Juice"

    # Juice build — juice significant but not dominant
    if juice > 0.22 and spirit > 0.30:
        return "Spirit + Juice"

    # Amaro + vermouth + spirit (Negroni family)
    if amaro > 0.18 and verm > 0.12 and spirit > 0.18:
        return "Negroni-Style"

    # Amaro-forward without vermouth (Paper Plane family, amaro sours)
    if amaro > 0.30 and spirit > 0.12:
        return "Amaro Build"

    # Spirit + vermouth (Manhattan, Martini family)
    if spirit > 0.40 and verm > 0.20:
        return "Spirit + Vermouth"

    # Vermouth-forward / wine cocktails
    if verm > 0.50:
        return "Wine / Vermouth"

    # Liqueur-forward (shots, dessert cocktails, creme builds)
    if liqueur > 0.50:
        return "Liqueur-Forward"

    # Spirit + liqueur without structural acid
    if spirit > 0.35 and liqueur > 0.20 and acid < 0.12:
        return "Spirit + Liqueur"

    return "Mixed"


# ---------------------------------------------------------------------------
# Cluster and produce templates
# ---------------------------------------------------------------------------

# Role families for the equal-parts overlay. Each entry defines a set of roles
# that should appear in near-equal proportions — a structural signature.
_EQUAL_PARTS_FAMILIES = [
    {
        "id": "negroni_style",
        "name": "Negroni-Style (equal thirds: spirit + amaro + vermouth)",
        "roles": ["spirit", "amaro", "vermouth_fortified"],
        "min_each": 0.25,
        "max_spread": 0.12,
    },
    {
        "id": "last_word_style",
        "name": "Equal-Parts (four-way: spirit + liqueur + amaro + acid)",
        "roles": ["spirit", "liqueur", "amaro", "acid"],
        "min_each": 0.18,
        "max_spread": 0.12,
    },
]


def detect_equal_parts(
    matrix: np.ndarray,
    metadata: list[dict],
    n_examples: int = 8,
) -> list[dict]:
    """Post-hoc overlay: explicitly detect role-family equal-parts patterns.

    K-means splits the equal-thirds Negroni across other clusters because it
    sits at a centroid boundary.  This detector finds specific structural
    families directly.  Returned as overlay entries in the output JSON —
    Ari decides whether to keep them as first-class templates.
    """
    role_idx = {r: i for i, r in enumerate(ROLES)}
    results = []

    for family in _EQUAL_PARTS_FAMILIES:
        fidx = [role_idx[r] for r in family["roles"] if r in role_idx]
        min_each = family["min_each"]
        max_spread = family["max_spread"]

        matching_indices: list[int] = []
        for i, vec in enumerate(matrix):
            vals = [vec[j] for j in fidx]
            # Each target role must be above the minimum
            if min(vals) < min_each:
                continue
            # Spread across target roles must be tight
            if max(vals) - min(vals) > max_spread:
                continue
            # The target roles should dominate the drink (≥ 75% of volume)
            if sum(vals) < 0.75:
                continue
            matching_indices.append(i)

        if not matching_indices:
            continue

        sub = matrix[matching_indices]
        centroid = sub.mean(axis=0)
        centroid_dict = {
            r: round(float(v), 4)
            for r, v in zip(ROLES, centroid)
            if v >= 0.005
        }

        dists = np.linalg.norm(sub - centroid, axis=1)
        sorted_idx = np.argsort(dists)
        examples = []
        seen: set[str] = set()
        for i in sorted_idx:
            m = metadata[matching_indices[i]]
            if m["name"] not in seen:
                seen.add(m["name"])
                props = {r: round(v, 3) for r, v in m["proportions"].items() if v > 0.01}
                examples.append({"name": m["name"], "props": props})
            if len(examples) >= n_examples:
                break

        matching_names = {metadata[j]["name"] for j in matching_indices}
        benchmark_in = [b for b in BENCHMARK_DRINKS if b in matching_names]
        ratio_str, role_labels = _ratio_string(centroid_dict)

        results.append({
            "id": family["id"],
            "suggested_name": family["name"],
            "source": "equal_parts_detector",
            "centroid": centroid_dict,
            "dominant_ratio": ratio_str,
            "dominant_roles": role_labels,
            "recipe_count": len(matching_indices),
            "benchmark_drinks": sorted(benchmark_in),
            "examples": examples,
            "detector_criteria": {
                "target_roles": family["roles"],
                "min_each": min_each,
                "max_spread": max_spread,
                "min_role_total": 0.75,
            },
            "notes": (
                "PROVISIONAL — post-hoc overlay (not a k-means cluster). "
                "Drinks where " + ", ".join(family["roles"]) + " are all "
                f"≥{min_each:.0%} and within {max_spread:.0%} of each other "
                "and together ≥ 75% of the drink. Ari to confirm as a "
                "first-class template."
            ),
        })

    return results


def find_best_k(matrix: np.ndarray, k_range: range) -> tuple[int, dict[int, float]]:
    scores: dict[int, float] = {}
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(matrix)
        if len(set(labels)) < 2:
            continue
        scores[k] = silhouette_score(matrix, labels)
    best_k = max(scores, key=lambda k: scores[k])
    return best_k, scores


BENCHMARK_DRINKS = [
    "Daiquiri", "Negroni", "Old Fashioned", "Whiskey Sour", "Margarita",
    "Manhattan", "Cosmopolitan", "Gimlet", "Mojito", "Moscow Mule",
    "Sidecar", "Last Word", "Paper Plane", "Aperol Spritz",
]


def build_templates(
    matrix: np.ndarray,
    metadata: list[dict],
    k: int,
    n_examples: int = 8,
) -> list[dict]:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(matrix)

    # Map benchmark drink names to their cluster label
    benchmark_map: dict[str, int] = {}
    name_to_idx: dict[str, int] = {m["name"]: i for i, m in enumerate(metadata)}
    for bname in BENCHMARK_DRINKS:
        if bname in name_to_idx:
            benchmark_map[bname] = int(labels[name_to_idx[bname]])

    templates = []
    for cluster_id in range(k):
        mask = labels == cluster_id
        indices = np.where(mask)[0]
        centroid = km.cluster_centers_[cluster_id]

        # Centroid as a dict, dropping near-zero roles
        centroid_dict = {
            r: round(float(v), 4)
            for r, v in zip(ROLES, centroid)
            if v >= 0.005
        }

        # Distance from centroid — pick examples closest to it
        dists = np.linalg.norm(matrix[mask] - centroid, axis=1)
        sorted_idx = np.argsort(dists)
        examples = []
        seen_names: set[str] = set()
        for i in sorted_idx:
            m = metadata[indices[i]]
            if m["name"] not in seen_names:
                seen_names.add(m["name"])
                props = {r: round(v, 3) for r, v in m["proportions"].items() if v > 0.01}
                examples.append({"name": m["name"], "props": props})
            if len(examples) >= n_examples:
                break

        ratio_str, role_labels = _ratio_string(centroid_dict)
        suggested_name = _suggest_name(centroid_dict)

        benchmarks_here = [b for b, cid in benchmark_map.items() if cid == cluster_id]

        templates.append({
            "id": f"cluster_{cluster_id}",  # placeholder; Ari to name
            "suggested_name": suggested_name,
            "centroid": centroid_dict,
            "dominant_ratio": ratio_str,
            "dominant_roles": role_labels,
            "recipe_count": int(mask.sum()),
            "benchmark_drinks": sorted(benchmarks_here),
            "examples": examples,
            "notes": "PROVISIONAL — name and ratio rounding subject to Ari's review",
        })

    # Sort by recipe count descending
    templates.sort(key=lambda t: -t["recipe_count"])
    return templates


# ---------------------------------------------------------------------------
# Classifier self-test (spot-check known drinks)
# ---------------------------------------------------------------------------

SPOT_CHECKS = [
    ("Daiquiri",     {"spirit": 0.571, "acid": 0.286, "sweet": 0.143}),
    ("Negroni",      {"spirit": 0.333, "amaro": 0.333, "vermouth_fortified": 0.333}),
    ("Old Fashioned", {"spirit": 0.970, "bitter_frac": 0.030}),
    ("Whiskey Sour", {"spirit": 0.571, "acid": 0.286, "sweet": 0.143}),
    ("Margarita",    {"spirit": 0.5, "acid": 0.25, "vermouth_fortified": 0.0}),
]

def run_spot_checks(data: list[dict]) -> None:
    lookup = {d["name"]: d for d in data}
    print("\n--- Classifier spot-checks ---")
    for drink_name, expected_roles in SPOT_CHECKS:
        drink = lookup.get(drink_name)
        if not drink:
            print(f"  MISSING: {drink_name}")
            continue
        classified: dict[str, float] = defaultdict(float)
        bitter_sum = 0.0
        total = 0.0
        for ing in drink["ingredients"]:
            p = ing.get("proportion")
            if p is None:
                continue
            role = classify_role(ing["name"])
            total += p
            if role == "bitter":
                bitter_sum += p
            elif role != "other":
                classified[role] += p

        print(f"\n  {drink_name}:")
        for r, v in sorted(classified.items(), key=lambda x: -x[1]):
            print(f"    {r}: {v:.3f}")
        if bitter_sum > 0.001:
            print(f"    [bitter]: {bitter_sum:.3f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Discover proportion templates.")
    parser.add_argument(
        "--k", type=int, default=10,
        help="Number of clusters (default: 10).  Use 0 to auto-select by silhouette.",
    )
    parser.add_argument(
        "--k-min", type=int, default=8,
        help="Minimum k to try when auto-selecting (default: 8).",
    )
    parser.add_argument(
        "--k-max", type=int, default=15,
        help="Maximum k to try when auto-selecting (default: 15).",
    )
    parser.add_argument(
        "--max-other", type=float, default=0.30,
        help="Max fraction of unclassified volume per drink (default: 0.30).",
    )
    parser.add_argument(
        "--n-examples", type=int, default=8,
        help="Number of example drinks per template (default: 8).",
    )
    parser.add_argument(
        "--no-overlay", action="store_true",
        help="Skip the equal-parts overlay detector.",
    )
    args = parser.parse_args()

    with COCKTAILAPP_PATH.open(encoding="utf-8") as fh:
        raw_data = json.load(fh)

    run_spot_checks(raw_data)

    print(f"\nLoaded {len(raw_data)} drinks from cocktailapp.")
    matrix, metadata = build_vectors(raw_data, max_other_frac=args.max_other)
    print(f"Usable vectors: {len(metadata)} (≥70% proportions classifiable).")

    # Role distribution across the corpus
    role_totals: dict[str, float] = defaultdict(float)
    for vec in matrix:
        for r, v in zip(ROLES, vec):
            role_totals[r] += v
    grand = sum(role_totals.values())
    print("\nRole share across corpus:")
    for r in ROLES:
        print(f"  {r:22s}  {role_totals[r]/grand*100:5.1f}%")

    if args.k == 0:
        print(f"\nAuto-selecting k = {args.k_min}..{args.k_max} …")
        best_k, sil_scores = find_best_k(matrix, range(args.k_min, args.k_max + 1))
        print("\nSilhouette scores:")
        for k in sorted(sil_scores):
            marker = " <-- selected" if k == best_k else ""
            print(f"  k={k:2d}  {sil_scores[k]:.4f}{marker}")
    else:
        best_k = args.k
        km_for_sil = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        sil = silhouette_score(matrix, km_for_sil.fit_predict(matrix))
        print(f"\nk={best_k} silhouette score: {sil:.4f}")
        sil_scores = {best_k: sil}

    print(f"\nUsing k={best_k}. Building templates …")
    templates = build_templates(matrix, metadata, best_k, args.n_examples)

    overlays: list[dict] = []
    if not args.no_overlay:
        overlays = detect_equal_parts(matrix, metadata, args.n_examples)
        if overlays:
            print(f"\nEqual-parts overlay: {len(overlays)} additional template(s) detected.")

    output = {
        "k": best_k,
        "silhouette": round(sil_scores[best_k], 4),
        "recipe_count": len(metadata),
        "roles": ROLES,
        "templates": templates + overlays,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as fh:
        json.dump(output, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    all_templates = templates + overlays
    print(f"\nWrote {len(all_templates)} templates to {OUTPUT_PATH}")
    print("\n=== Discovered templates (PROVISIONAL — Ari to name/approve) ===\n")
    for t in all_templates:
        src = " [overlay]" if t.get("source") == "equal_parts_detector" else ""
        print(f"  [{t['recipe_count']:>4d} drinks]  {t['suggested_name']!r:35s}{src}")
        print(f"             ratio {t['dominant_ratio']:12s}  ({t['dominant_roles']})")
        top_3 = sorted(t["centroid"].items(), key=lambda x: -x[1])[:3]
        print(f"             centroid: {', '.join(f'{r} {v:.2f}' for r, v in top_3)}")
        if t.get("benchmark_drinks"):
            print(f"             benchmarks: {', '.join(t['benchmark_drinks'])}")
        print(f"             e.g. {', '.join(e['name'] for e in t['examples'][:4])}")
        print()


if __name__ == "__main__":
    main()
