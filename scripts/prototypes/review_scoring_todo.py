"""PROTOTYPE (2026-10-23): evidence for the review in docs/todo-scoring-upgrade.md; delete once step 1 is built.

Reproduces every number the review cites, from the committed data:
  1. the approved to-do's target scores, and what actually drives them;
  2. what the proposed hard "block" rules would do to real drinks;
  3. the data behind the duplicate problem (single-botanical composites, the 0.9 gap);
  4. the refined rules (structure items not scored, per-compound diminishing
     returns, same-voice merge) against the to-do's own goals and the IBA list;
  5. source counts for the "too bright" / target-note notice;
  6. the strength arithmetic for Olivia B.

Run from the repo root: python3 scripts/prototypes/review_scoring_todo.py
"""
import importlib.util
import json
import math
from collections import Counter
from itertools import combinations
from pathlib import Path

from cobber import engine as e

ROOT = Path(__file__).resolve().parents[2]
P = e.PANTRY
_spec = importlib.util.spec_from_file_location("loop2", ROOT / "scripts" / "prototypes" / "olivia_loop2.py")
loop2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(loop2)

RECIPES = json.load(open(ROOT / "data" / "recipes_components.json", encoding="utf-8"))
CANON = {"craft", "iba", "diffords", "mrboston", "thecocktaildb"}
IBA = [d for d in RECIPES if d["source"] == "iba"]

# House gin as the prototype modelled it (gin + lemon + orange) until the real bill is approved.
HOUSE_GIN = e.profile("gin") | e.profile("lemon") | e.profile("orange")


def entry(i):
    return P.get("gin" if i == "house_gin" else i)


def prof(i):
    return HOUSE_GIN if i == "house_gin" else e.profile(i)


def jac(pa, pb):
    return len(pa & pb) / len(pa | pb) if pa and pb else 0.0


def known(ids):
    return [i for i in dict.fromkeys(ids) if entry(i)]


def current(ids):
    """Today's engine: mean pairwise Jaccard over every pair, structure items included."""
    return e._score_combination(["gin" if i == "house_gin" else i for i in ids])["harmony"]


OLIVIA = {
    "restaurant, as the to-do lists it (with dry vermouth)": ["house_gin", "dry_vermouth", "amaretto", "honey", "lemon", "olive"],
    "restaurant, as on the menu (no vermouth)": ["house_gin", "amaretto", "honey", "lemon", "olive"],
    "M1 (vermouth + maraschino)": ["house_gin", "dry_vermouth", "amaretto", "maraschino", "lemon", "olive"],
    "M2 (maraschino + vanilla)": ["house_gin", "amaretto", "maraschino", "vanilla", "lemon", "olive"],
    "P (peche + vanilla)": ["house_gin", "amaretto", "peach_schnapps", "vanilla", "lemon", "olive"],
    "B (Benedictine + vanilla)": ["house_gin", "amaretto", "benedictine", "vanilla", "lemon", "olive"],
}

# --- The refined rules (step 1 of the refined to-do) ---------------------------------
SAME_VOICE_J = 0.9  # near-identical profiles count as one voice
DECAY = 0.5  # each extra carrier of a shared compound counts half as much as the last
AROMA_ROLES = {"aromatic", "herb", "bitter"}  # botanicals added for their smell, not structure


def same_voice(a, b):
    if jac(prof(a), prof(b)) >= SAME_VOICE_J:
        return True
    # An aroma botanical already on a composite's bill repeats that composite (coriander in gin);
    # juices, fruit and syrups on a bill still bridge (lemon with gin).
    return (b in entry(a).botanicals and entry(b).role in AROMA_ROLES) or (
        a in entry(b).botanicals and entry(a).role in AROMA_ROLES
    )


def voices(ids):
    out = []
    for i in known(ids):
        if not prof(i):
            continue  # structure only (sugar, salt, soda, egg white, vodka): not scored for aroma
        for v in out:
            if any(same_voice(i, j) for j in v["ids"]):
                v["ids"].append(i)
                v["p"] |= prof(i)
                break
        else:
            out.append({"ids": [i], "p": set(prof(i))})
    return out


def refined(ids):
    vs = voices(ids)
    if len(vs) < 2:
        return 0.0
    carriers = Counter(c for v in vs for c in v["p"])

    def weight(c):  # a compound's credit, spread over the pairs that share it
        k = carriers[c]
        return sum(DECAY**j for j in range(k - 1)) / math.comb(k, 2)

    vals = [sum(weight(c) for c in a["p"] & b["p"]) / len(a["p"] | b["p"]) for a, b in combinations(vs, 2)]
    return sum(vals) / len(vals)


def adds_a_voice(core, y):
    return len(voices(core + [y])) > len(voices(core))


W2F = P.descriptor_word_to_family


def families(i):
    return {W2F[d] for d in entry(i).descriptors if d in W2F}


def sources(ids, family):
    return [i for i in known(ids) if family in families(i)]


def spearman(xs, ys):
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0] * len(v)
        for pos, i in enumerate(order):
            r[i] = pos
        return r

    rx, ry, n = ranks(xs), ranks(ys), len(xs)
    return 1 - 6 * sum((a - b) ** 2 for a, b in zip(rx, ry)) / (n * (n * n - 1))


def header(title):
    print(f"\n=== {title} ===")


if __name__ == "__main__":
    header("1. The approved to-do's target scores (prototype rules: citrus fully masked)")
    for name, s in OLIVIA.items():
        print(f"  {name:55s} prototype {loop2.H(set('gin' if i == 'house_gin' else i for i in s)):.3f}")
    b = sorted(["gin", "amaretto", "benedictine", "vanilla", "lemon", "olive"])
    vals = [v for x, y in combinations(b, 2) if (v := loop2.pair(x, y)) is not None]
    print(f"  B without its benedictine+vanilla pair (Jaccard {jac(prof('benedictine'), prof('vanilla')):.3f}):"
          f" {(sum(vals) - 1.0) / (len(vals) - 1):.3f}")
    print(f"  can the prototype's own search add benedictine next to vanilla? "
          f"{loop2.allowed_add('benedictine', {'gin', 'amaretto', 'vanilla', 'lemon', 'olive'})}")
    _, shared = e.harmony("olive", "amaretto")
    print(f"  olive~amaretto {e.harmony('olive', 'amaretto')[0]:.3f}, shared only {sorted(shared)};"
          f" olive provisional={P.get('olive').provisional}, benedictine provisional={P.get('benedictine').provisional}")

    header("2. The to-do's three rules as hard blocks, on real drinks")
    def blocked_by(ids):
        ids = known(ids)
        hits = set()
        for x, y in combinations(ids, 2):
            if y in entry(x).botanicals or x in entry(y).botanicals:
                hits.add("botanical inside a composite")
            if jac(prof(x), prof(y)) >= 0.8:
                hits.add("overlap >= 80%")
        for y in ids:
            have = set().union(*(prof(x) for x in ids if x != y)) if len(ids) > 1 else set()
            if prof(y) and len(prof(y) - have) / len(prof(y)) < 0.2:
                hits.add("< 20% new compounds")
        return hits
    for label, drinks in (("IBA", IBA), ("all canon", [d for d in RECIPES if d["source"] in CANON])):
        per_rule = Counter(r for d in drinks for r in blocked_by(d["literal"]))
        any_hit = sum(1 for d in drinks if blocked_by(d["literal"]))
        print(f"  {label}: {any_hit}/{len(drinks)} ({any_hit / len(drinks):.0%}) blocked; by rule: {dict(per_rule)}")
    print("  IBA casualties include:", ", ".join(d["drink"] for d in IBA if blocked_by(d["literal"]) and d["drink"] in {
        "Negroni", "Dry Martini", "Aviation", "Clover Club", "French 75", "White Lady", "Espresso Martini", "Tommy's Margarita"}))

    header("3. Where duplicates come from")
    single = sorted(i for i, ing in P.ingredients.items() if len(ing.botanicals) == 1)
    vanillas = [i for i in single if P.get(i).botanicals == ("vanilla",)]
    print(f"  {len(single)} composites are a single botanical; modelled as [vanilla]: {', '.join(vanillas)}")
    pairs = sorted(((jac(prof(x), prof(y)), x, y) for x, y in combinations([i for i in P.all_ids() if prof(i)], 2)), reverse=True)
    near = [(round(j, 3), x, y) for j, x, y in pairs if 0.8 <= j < 1.0]
    print(f"  pairs between 0.8 and 1.0 (the gap sits between 0.909 and 0.867): {near}")
    df = Counter(c for i in P.all_ids() for c in e.profile(i))
    print(f"  most widespread compounds, of {sum(1 for i in P.all_ids() if e.profile(i))} profiled ingredients: {df.most_common(6)}")

    header("4. Refined rules against the to-do's own goals")
    for s in (["gin", "lemon"], ["lemon", "lime"], ["house_gin", "lemon"], ["house_gin", "lemon", "limoncello"],
              ["gin", "lemon", "lime"], ["gin", "coriander_seed"], ["amaretto", "almond"], ["benedictine", "vanilla"]):
        print(f"  {'+'.join(s):30s} current {current(s):.3f}  refined {refined(s):.3f}  voices {[v['ids'] for v in voices(s)]}")
    core = ["house_gin", "amaretto", "lemon", "olive"]
    cands = ["limoncello", "honey", "maraschino", "peach_schnapps", "vanilla", "benedictine", "dry_vermouth", "orgeat",
             "almond", "sherry", "yellow_chartreuse", "st_germain", "apricot_brandy", "coffee_liqueur", "brandy"]
    print("  one addition to the Olivia core, current: " + " > ".join(sorted(cands, key=lambda c: -current(core + [c]))))
    print("  refined, before the suggestion rule:     " + " > ".join(sorted(cands, key=lambda c: -refined(core + [c]))))
    offered = [c for c in cands if adds_a_voice(core, c)]
    print("  refined, only additions that add a voice: " + " > ".join(sorted(offered, key=lambda c: -refined(core + [c]))))
    print(f"  not offered (they only repeat what is there): {[c for c in cands if c not in offered]}")
    for name, s in OLIVIA.items():
        print(f"  {name:55s} current {current(s):.3f}  refined {refined(s):.3f}")
    cur_iba, ref_iba = [current(d["literal"]) for d in IBA], [refined(d["literal"]) for d in IBA]
    print(f"  IBA rank correlation, current vs refined: {spearman(cur_iba, ref_iba):.2f} over {len(IBA)} drinks; none blocked")
    moves = sorted(zip([r - c for c, r in zip(cur_iba, ref_iba)], [d["drink"] for d in IBA], cur_iba, ref_iba))
    print("  biggest falls: " + "; ".join(f"{n} {c:.2f}->{r:.2f}" for _, n, c, r in moves[:4]))
    print("  biggest rises: " + "; ".join(f"{n} {c:.2f}->{r:.2f}" for _, n, c, r in moves[-4:]))

    header("5. Source counts for the 'too bright' and target-note notice (curated descriptors)")
    for i in ("amaretto", "benedictine", "maraschino"):
        print(f"  {i}: compound wheel says {e.flavor_wheel(i)['dominant']!r}; curated descriptors say {sorted(families(i))}")
    for name, s in OLIVIA.items():
        print(f"  {name:55s} citrus sources {sources(s, 'citrus')}, nutty sources {sources(s, 'roasted_nutty')}")
    bright = [d["drink"] for d in IBA if len(sources(d["literal"], "citrus")) >= 3]
    print(f"  IBA drinks with 3+ citrus sources: {len(bright)}/{len(IBA)}: {bright}")

    header("6. Olivia B strength (35 gin / 10 amaretto / 7.5 Benedictine / 2.5 vanilla syrup / 7.5 brine / 17.5 lemon / 5 oil)")
    volume = 35 + 10 + 7.5 + 2.5 + 7.5 + 17.5 + 5
    for gin_abv in (0.40, 0.38):
        ethanol = 35 * gin_abv + 10 * 0.28 + 7.5 * 0.40  # amaretto 28%, Benedictine 40%
        print(f"  gin {gin_abv:.0%}: {ethanol * 0.789 / 10:.2f} standard drinks (10 g), {ethanol / volume:.1%} ABV before ice")
    ethanol = 35 * 0.40 + 10 * 0.28 + 7.5 * 0.40
    print("  ABV in the glass by dilution: " + ", ".join(f"{d:.0%} -> {ethanol / (volume * (1 + d)):.1%}" for d in (0.25, 0.30, 0.40, 0.50)))
    a = ethanol / volume
    print(f"  stirred-drink dilution as quoted from Liquid Intelligence (-1.21a^2 + 1.26a + 0.145): {-1.21 * a * a + 1.26 * a + 0.145:.0%}")
    # House-spec hand maths, with typical label strengths (gin 40, dry vermouth 18, amaretto 28,
    # maraschino 32, creme de peche 18): the real labels replace these in step 3.
    specs = {"M1": {"dry vermouth": (15, 0.18), "amaretto": (15, 0.28), "maraschino": (7.5, 0.32)},
             "M2": {"amaretto": (15, 0.28), "maraschino": (7.5, 0.32)},
             "P": {"amaretto": (15, 0.28), "creme de peche": (10, 0.18)}}
    for name, rest in specs.items():
        for gin_ml in (30, 45):
            ethanol = gin_ml * 0.40 + sum(ml * abv for ml, abv in rest.values())
            print(f"  {name} with {gin_ml} ml gin: {ethanol * 0.789 / 10:.2f} standard drinks")
