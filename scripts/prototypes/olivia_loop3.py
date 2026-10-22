"""PROTOTYPE (2026-10-22): reference for the engine rules in docs/todo-scoring-upgrade.md; delete once built.

Olivia loop 3: full stock + buyable list, corrected scoring, identity guards.

Scoring = loop2 rules (citrus not a bridge, no duplicates / botanicals already
inside a composite, >=20% new compounds). Rule 3 (stay Olivia) is now explicit:
gin is the only base spirit, no dark modifiers (colour), max 8 aroma ingredients.
"""
import importlib.util
from itertools import combinations
spec = importlib.util.spec_from_file_location("l2", __file__.replace("loop3", "loop2"))
l2 = importlib.util.module_from_spec(spec); spec.loader.exec_module(l2)
H, allowed_add, prof = l2.H, l2.allowed_add, l2.prof

ANCHORS = {"gin", "olive", "lemon", "amaretto"}
ON_BAR = {  # Aperitif Co menu + house specs
 "dry_vermouth":"bar", "sherry":"bar (Manzanilla) / Summer Hill", "maraschino":"bar", "peach_schnapps":"bar (crème de pêche)",
 "honey":"bar", "orgeat":"bar", "yellow_chartreuse":"bar", "green_chartreuse":"bar", "st_germain":"bar",
 "gentian":"bar (Salers, proxy)", "cynar":"bar (artichoke vermouth, proxy)", "apricot_brandy":"bar",
 "absinthe":"bar", "vanilla":"bar", "cinnamon":"bar", "rosemary":"bar", "mint":"bar", "basil":"bar",
 "angostura_bitters":"bar", "sloe_gin":"bar", "limoncello":"bar", "orange_bitters":"bar", "peach":"bar (Monin)",
 "apricot":"bar (canned)", "black_pepper":"bar", "tomato":"bar (sun-dried tomato gin, proxy)",
}
BUY = ["celery_bitters", "celery", "cardamom", "thyme", "sage", "pink_peppercorn", "wattleseed", "anise",
       "star_anise", "nutmeg", "clove", "allspice", "elderflower", "lavender", "benedictine", "galliano",
       "amaro_montenegro", "falernum", "ginger", "pear", "apple", "grape", "cherry", "cherry_liqueur", "drambuie"]
# Identity guards: no second base spirit, nothing that turns the drink dark.
BLOCKED = {"brandy", "mezcal", "tequila", "white_rum", "dark_rum", "bourbon", "rye_whiskey", "scotch", "pisco",
           "vodka", "cachaca", "calvados", "irish_whiskey", "spiced_rum", "coffee_liqueur", "averna",
           "sweet_vermouth", "fernet", "port", "creme_de_cassis", "raspberry_liqueur", "campari", "red_wine"}
POOL = [p for p in list(ON_BAR) + BUY if p not in BLOCKED and prof(p)]
MAX_ITEMS = 8

def source(x): return ON_BAR.get(x, "buy")

if __name__ == "__main__":
    cur = {"gin", "dry_vermouth", "amaretto", "maraschino", "peach_schnapps", "lemon", "olive"}  # v6
    h = H(cur); print(f"start v6 H*={h:.3f} {sorted(cur)}")
    seen = {frozenset(cur)}
    for i in range(1, 41):
        moves = [(H(cur - {x}), f"remove {x}", cur - {x}) for x in cur - ANCHORS]
        for y in POOL:
            if y in cur: continue
            if len(cur) < MAX_ITEMS and allowed_add(y, cur):
                moves.append((H(cur | {y}), f"add {y} [{source(y)}]", cur | {y}))
            for x in cur - ANCHORS:
                if allowed_add(y, cur - {x}):
                    moves.append((H((cur - {x}) | {y}), f"swap {x} -> {y} [{source(y)}]", (cur - {x}) | {y}))
        moves = [m for m in moves if frozenset(m[2]) not in seen]
        best = max(moves, key=lambda m: m[0])
        if best[0] <= h + 0.003:
            print(f"loop {i}: WALL. Best remaining move {best[1]} -> {best[0]:.3f} (current {h:.3f})")
            break
        h, cur = best[0], best[2]; seen.add(frozenset(cur))
        print(f"loop {i}: {best[1]:48s} H*={h:.3f}")
    print("final:", sorted(cur))
    # Global check: best set of anchors + up to 4 from the pool (exhaustive).
    pool = [p for p in POOL if p not in ANCHORS]
    best = (0, None)
    for k in range(0, 5):
        for c in combinations(pool, k):
            s = ANCHORS | set(c)
            ok = all(allowed_add(y, s - {y}) for y in c)
            if ok and (v := H(s)) > best[0]:
                best = (v, sorted(s))
    print(f"exhaustive best (anchors + up to 4): H*={best[0]:.3f} {best[1]}")
