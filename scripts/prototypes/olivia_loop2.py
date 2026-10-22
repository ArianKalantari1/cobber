"""PROTOTYPE (2026-10-22): reference for the engine rules in docs/todo-scoring-upgrade.md; delete once built.

Olivia loop, corrected for redundancy.

Fixes vs the first loop:
1. House gin is citrus-forward: modelled as gin + lemon + orange compounds.
2. Citrus is saturated, so citrus does not count as a bridge: pairs touching a
   citrus-family item are scored with citrus compounds masked out; pairs of two
   citrus items are skipped; no new citrus-family items may be added.
3. Near-duplicates are not "harmony": a candidate whose profile is >=80% the same
   as something already in the drink (amaretto vs almond) is not allowed.
4. Items with no aroma profile (sugar, salt, foamer) are structure, not scored.
"""
from itertools import combinations
from cobber import engine as e

base_profile = e.profile
CITRUS_COMPOUNDS = set().union(*(base_profile(c) for c in ("lemon", "lime", "orange", "grapefruit")))
HOUSE_GIN = base_profile("gin") | base_profile("lemon") | base_profile("orange")
prof = lambda i: HOUSE_GIN if i == "gin" else base_profile(i)

CITRUS = {"gin", "lemon", "lime", "orange", "grapefruit", "limoncello", "cointreau", "triple_sec",
          "citron_vodka", "lemon_rum", "lime_vodka", "bitter_orange_peel", "orange_bitters", "aperol",
          "lemon_myrtle", "finger_lime", "desert_lime", "lemon_aspen", "blue_curacao"}

def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0

def pair(a, b):
    if a in CITRUS and b in CITRUS:
        return None
    pa, pb = prof(a), prof(b)
    if a in CITRUS or b in CITRUS:
        pa, pb = pa - CITRUS_COMPOUNDS, pb - CITRUS_COMPOUNDS
    return jac(pa, pb)

def H(s):
    vals = [v for a, b in combinations(sorted(i for i in s if prof(i)), 2) if (v := pair(a, b)) is not None]
    return sum(vals) / len(vals) if vals else 0.0

ANCHORS = {"gin", "olive", "lemon", "amaretto"}
START = {"gin", "dry_vermouth", "amaretto", "limoncello", "lemon", "olive", "orange_bitters"}
PANTRY = ["dry_vermouth", "limoncello", "orange_bitters", "honey", "peach_schnapps", "absinthe", "averna",
          "coffee_liqueur", "brandy", "mezcal", "pisco", "sherry", "apricot_brandy", "peach", "basil",
          "black_pepper", "angostura_bitters", "celery_bitters", "celery", "coriander_seed", "cardamom",
          "rosemary", "thyme", "sage", "pink_peppercorn", "almond", "orgeat", "sweet_vermouth", "campari",
          "amaro_montenegro", "yellow_chartreuse", "green_chartreuse", "st_germain", "maraschino",
          "wattleseed", "cynar", "fennel" ]
PANTRY = [p for p in PANTRY if prof(p) and p not in CITRUS - START]

import json
_c = json.load(open(__import__("pathlib").Path(__file__).resolve().parents[2] / "data" / "composites.json"))
BOTANICALS = {x["id"]: set(x.get("botanicals", [])) for x in (_c if isinstance(_c, list) else list(_c.values())[0])}

def new_share(y, cur):
    """Fraction of y's compounds not already in the drink."""
    have = set().union(*(prof(x) for x in cur)) if cur else set()
    return len(prof(y) - have) / len(prof(y))

def allowed_add(y, cur):
    # 5. An addition must bring something new: not a botanical already inside a
    #    composite in the drink (coriander is in gin), and >=20% new compounds.
    inside = any(y in BOTANICALS.get(x, ()) or x in BOTANICALS.get(y, ()) for x in cur)
    return (y not in CITRUS and not inside and new_share(y, cur) >= 0.2
            and all(jac(prof(y), prof(x)) < 0.8 for x in cur if prof(x)))

if __name__ == "__main__":
    cur, h = set(START), H(START)
    print(f"start H*={h:.3f} {sorted(cur)}")
    for i in range(1, 21):
        moves = [(H(cur - {x}), f"remove {x}", cur - {x}) for x in cur - ANCHORS]
        for y in PANTRY:
            if y in cur or not allowed_add(y, cur):
                continue
            if len(cur) < 8:
                moves.append((H(cur | {y}), f"add {y}", cur | {y}))
            for x in cur - ANCHORS:
                if allowed_add(y, cur - {x}):
                    moves.append((H((cur - {x}) | {y}), f"swap {x} -> {y}", (cur - {x}) | {y}))
        best = max(moves, key=lambda m: m[0])
        if best[0] <= h + 0.005:
            print(f"loop {i}: converged; best remaining move {best[1]} -> {best[0]:.3f}")
            break
        h, cur = best[0], best[2]
        print(f"loop {i}: {best[1]:34s} H*={h:.3f}  {sorted(cur)}")
    print("\nfinal pairs:")
    for a, b in combinations(sorted(cur), 2):
        v = pair(a, b)
        print(f"  {a}+{b}: {'skip (citrus+citrus)' if v is None else round(v, 3)}")
