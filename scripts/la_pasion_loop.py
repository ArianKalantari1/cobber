#!/usr/bin/env python3
"""La Pasión optimisation loop (bar R&D, not part of the build pipeline).

Written up in docs/recipes/spring-signatures-rnd.md. Run:
    python3 scripts/la_pasion_loop.py [--json out.json]

Beam search from the current spec. Each round mutates every beam member one
gene at a time, re-computes the drink maths (sugar, acid, ABV, volume, cost)
and re-scores. Maths is computed; flavour intensities per style are judgement
weights (flagged), so the output is a ranked shortlist for tasting.
"""
from __future__ import annotations

import itertools
import json
import random
import sys

# --- Ingredient data -------------------------------------------------------
# sherries: abv, sugar g/L, $ per ml at the shop's any-six price, and judgement
# weights per ml: nut, caramel, raisin, vanilla, salt, flor.
SHERRY = {
    "elegante_fino":   dict(name="Elegante Fino", abv=.15, sug=3, usd=19.99/750, nut=.35, car=0, rai=0, van=0, sal=.30, life=14),
    "tio_pepe":        dict(name="Tío Pepe Fino", abv=.15, sug=1, usd=32/750, nut=.50, car=0, rai=0, van=0, sal=.35, life=14),
    "inocente":        dict(name="Inocente Fino", abv=.15, sug=1, usd=24/375, nut=.65, car=0, rai=0, van=0, sal=.35, life=14),
    "la_guita":        dict(name="La Guita Manzanilla", abv=.15, sug=1, usd=15.99/375, nut=.30, car=0, rai=0, van=0, sal=.60, life=14),
    "apera":           dict(name="Chambers Dry Flor Apera", abv=.155, sug=3, usd=15.99/750, nut=.50, car=0, rai=0, van=0, sal=.45, life=14),
    "elegante_medium": dict(name="Elegante Medium (amontillado style)", abv=.17, sug=10, usd=19.99/750, nut=1.0, car=.35, rai=.15, van=0, sal=.10, life=45),
    "elegante_cream":  dict(name="Elegante Cream", abv=.17, sug=130, usd=19.99/750, nut=.80, car=.60, rai=.60, van=0, sal=0, life=60),
    "solera_1847":     dict(name="Solera 1847 Cream", abv=.18, sug=120, usd=32/750, nut=.55, car=.70, rai=.80, van=.5, sal=0, life=60),
    "px":              dict(name="Valdespino PX", abv=.17, sug=400, usd=30/750, nut=.25, car=.90, rai=1.6, van=0, sal=0, life=90),
    "topaque":         dict(name="Buller Fine Old Topaque (not sherry)", abv=.18, sug=210, usd=26/750, nut=.45, car=1.1, rai=.30, van=0, sal=0, life=90),
}
PISCO = dict(abv=.40, usd=50/700)
SB = dict(abv=.125, usd=15/750, acid=.0065)
# Passionfruit: one drink's worth. Canned = 1/16 of an 840 g can; purée = 1/37.5 kg.
FRUIT = {
    "canned": dict(g=52.5, ml=44.0, sug=.201, acid=.028, fruit_eq=26.7, life=18),  # ml after straining seeds
    "puree":  dict(g=26.7, ml=24.7, sug=.11,  acid=.042, fruit_eq=26.7, life=18),
}
LEMONADE_SUG, LEMONADE_ACID = .100, .0020   # g/ml, AU traditional lemonade (approx)
HIB_SUG = 500/560                            # rich hibiscus syrup, g sugar per ml
TARGET_RATIO = 14.0                          # sugar:acid of the tasted base (assumed acid)

GENES = dict(
    fruit_mult=[1.0, 1.15],
    s1=list(SHERRY), s1_ml=[10, 12.5, 15, 17.5, 20, 25],
    s2=["none"] + list(SHERRY), s2_ml=[5, 7.5, 10],
    where=["base", "batch"],                 # sherry in the passionfruit base or in a pisco batch
    loosen=["sherry", "water", "sb"],        # what loosens canned pulp for straining
    pisco=[30, 35, 40, 45],
    sweet=["white", "demerara", "hibiscus", "burnt_hibiscus", "lemonade"],
    top=["soda", "lemonade", "half"], top_ml=[40, 60, 80],
    bitters=["none", "ango_batch", "ango_float", "peychauds_batch"],
    saline=[False, True],
    cointreau=[0, 5],
)

CURRENT = dict(form="canned", fruit_mult=1.0, s1="elegante_fino", s1_ml=12.5, s2="none", s2_ml=5,
               where="batch", loosen="sb", pisco=30, sweet="burnt_hibiscus", top="soda", top_ml=40,
               bitters="ango_batch", saline=True, cointreau=0)


def evaluate(g):
    if g["s2"] == g["s1"]:
        return None  # a split needs two different bottles
    f = FRUIT[g.get("form", "canned")]; m = g["fruit_mult"]
    s1 = SHERRY[g["s1"]]; s2 = SHERRY.get(g["s2"]) if g["s2"] != "none" else None
    s2_ml = g["s2_ml"] if s2 else 0
    sherry_ml = g["s1_ml"] + s2_ml
    vol = eth = sug = acid = cost = 0.0
    # fruit
    vol += f["ml"] * m; sug += f["g"] * m * f["sug"]; acid += f["g"] * m * f["acid"]
    # loosener (canned only needs one; sherry can loosen only if it lives in the base and is >=12.5 ml)
    sb_ml = 0
    if g.get("form", "canned") == "canned":
        if g["loosen"] == "sb":
            sb_ml = 17.5
        elif g["loosen"] == "sherry" and not (g["where"] == "base" and sherry_ml >= 12.5):
            return None  # invalid combination
        elif g["loosen"] == "water":
            vol += 15
    elif g["loosen"] == "sb":
        sb_ml = 17.7  # purée version used 665 ml per kg
    vol += sb_ml; eth += sb_ml * SB["abv"]; acid += sb_ml * SB["acid"]; cost += sb_ml * SB["usd"]
    # spirits
    vol += g["pisco"]; eth += g["pisco"] * PISCO["abv"]; cost += g["pisco"] * PISCO["usd"]
    for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)):
        if s:
            vol += ml; eth += ml * s["abv"]; sug += ml * s["sug"] / 1000; acid += ml * .005; cost += ml * s["usd"]
    if g["cointreau"]:
        vol += 5; eth += 5 * .40; sug += 5 * .25; cost += 5 * 60 / 700
    bit_ml = .8 if g["bitters"] in ("ango_batch", "peychauds_batch") else (.5 if g["bitters"] == "ango_float" else 0)
    vol += bit_ml; eth += bit_ml * .447
    # top
    top_ml = g["top_ml"]
    lem_ml = top_ml if g["top"] == "lemonade" else (top_ml / 2 if g["top"] == "half" else 0)
    sug += lem_ml * LEMONADE_SUG; acid += lem_ml * LEMONADE_ACID
    # sweetener: solve added sugar for the target ratio (lemonade-only means no added sugar)
    need = max(0.0, TARGET_RATIO * acid - sug)
    added_ml = 0.0
    if g["sweet"] == "lemonade":
        if lem_ml == 0:
            return None
        added = 0.0
    elif g["sweet"] in ("hibiscus", "burnt_hibiscus"):
        added_ml = need / HIB_SUG; added = need; acid += added_ml * .004
    else:
        added = need; added_ml = need * .63  # dissolved sugar volume
    sug += added; vol += added_ml
    pre_shake = vol
    final = pre_shake * 1.20 + top_ml
    abv = eth / final; sug100 = sug / final * 100; ratio = sug / acid
    # flavour indices (judgement weights)
    nut = sum(s["nut"] * ml for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)) if s)
    car = sum(s["car"] * ml for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)) if s)
    rai = sum(s["rai"] * ml for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)) if s)
    van = sum(s["van"] * ml for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)) if s)
    salt = sum(s["sal"] * ml for s, ml in ((s1, g["s1_ml"]), (s2, s2_ml)) if s) + (3 if g["saline"] else 0)
    if g["sweet"] == "demerara": car += added * .25; nut += added * .08
    if g["sweet"] == "burnt_hibiscus": car += added * .20
    if g["cointreau"]: nut *= 1.0
    if salt >= 3 and nut > 5: nut *= 1.12            # salted-nut effect: the original brief
    if g["bitters"] in ("ango_batch", "ango_float") and nut > 5: nut *= 1.05  # sherry + Angostura canon
    nut_i = nut / final * 100
    pf = f["fruit_eq"] * m / final * 100
    pf *= 1 + sb_ml * .012                         # SB thiols amplify passionfruit
    if g["cointreau"]: pf *= 1.04                  # orange lifts passionfruit (canon t=0.42)
    if g["sweet"] == "lemonade" or g["top"] != "soda": pf *= 1.02  # lemon-lime with passionfruit (t=0.52)
    mask = (car * .5 + rai) / final * 100
    pf_i = pf - mask * .35
    if g["sweet"] in ("hibiscus", "burnt_hibiscus"): pf_i -= .4   # hibiscus tartness/floral competes
    # ingredient count: flavour ingredients and everything on the station
    flav = {"pisco", "passionfruit", g["s1"]} | ({g["s2"]} if s2 else set())
    if sb_ml: flav.add("sauvignon_blanc")
    if g["sweet"] in ("hibiscus", "burnt_hibiscus"): flav.add("hibiscus")
    if g["bitters"] != "none": flav.add(g["bitters"].split("_")[0])
    if g["saline"]: flav.add("saline")
    if g["cointreau"]: flav.add("cointreau")
    struct = set()
    if g["sweet"] != "lemonade": struct.add("demerara" if g["sweet"] == "demerara" else "sugar")
    struct.add({"soda": "soda", "lemonade": "lemonade", "half": "soda+lemonade"}[g["top"]])
    if g["top"] == "half": struct |= {"soda", "lemonade"}; struct.discard("soda+lemonade")
    preps = 1  # the passionfruit base
    if g["where"] == "batch" or g["bitters"] in ("ango_batch", "peychauds_batch") or g["saline"]:
        preps += 1  # a pisco batch bottle
    if g["sweet"] in ("hibiscus", "burnt_hibiscus"): preps += 1  # a syrup cooked separately
    life = min(f["life"], *(s["life"] for s in (s1, s2) if s)) if g["where"] == "base" else f["life"]
    if g["where"] == "batch": life = min(life, s1["life"] if not s2 else min(s1["life"], s2["life"]))
    return dict(final=final, abv=abv, sug100=sug100, ratio=ratio, sug=sug, acid=acid, added=added,
                nut_i=nut_i, pf_i=pf_i, van=van, cost=cost, flav=sorted(flav), struct=sorted(struct),
                preps=preps, life=life, sherry_ml=sherry_ml, top_lem=lem_ml)


def score(g):
    e = evaluate(g)
    if e is None:
        return -99, None
    s = 0.0
    s += 4.0 * min(e["pf_i"] / 13.0, 1.15)            # passionfruit must come out
    s += 4.0 * min(e["nut_i"] / 9.0, 1.25)            # and nutty
    s -= 1.5 * max(0, abs(e["ratio"] - TARGET_RATIO) - 1.5) / 1.5
    s -= 1.5 * max(0, abs(e["abv"] - .093) - .012) / .01
    s -= 1.0 * max(0, e["sug100"] - 12.5) + 1.0 * max(0, 8.0 - e["sug100"])
    s -= 0.75 * max(0, len(e["flav"]) - 3)             # fewer flavour ingredients
    s -= 0.30 * max(0, len(e["struct"]) - 2)
    s -= 0.50 * (e["preps"] - 1)                      # fewer prep bottles
    s -= 0.50 if e["life"] < 14 else 0
    s -= 1.0 * e["van"] / 5                           # no vanilla on this menu
    s -= 0.6 * max(0, e["cost"] - 3.2)                # liquor cost per drink (fruit excluded)
    if g["pisco"] < 2 * e["sherry_ml"] or g["pisco"] < 30:
        s -= 3.0                                      # pisco stays the hero: at least 2x the sherry
    s += 0.15 * (min(g["pisco"], 40) - 30) / 5        # small reward for more pisco, within the ABV band
    return s, e


def neighbours(g):
    for k, vals in GENES.items():
        for v in vals:
            if v != g[k]:
                n = dict(g); n[k] = v
                yield k, n


def describe(g):
    sh = f"{g['s1']} {g['s1_ml']}" + (f" + {g['s2']} {g['s2_ml']}" if g['s2'] != 'none' else '')
    return (f"pisco {g['pisco']} | {sh} in {g['where']} | loosen {g['loosen']} | {g['sweet']} | "
            f"{g['top']} {g['top_ml']} | {g['bitters']} | saline {g['saline']} | cointreau {g['cointreau']} | fruit x{g['fruit_mult']}")


def key(g):
    return tuple(g[k] for k in GENES)


FAMILY = {"elegante_medium": "oxidative", "elegante_cream": "sweet", "solera_1847": "sweet", "px": "sweet",
          "topaque": "sweet"}


def concept(g):
    fam = lambda s: FAMILY.get(s, "flor")
    sh = tuple(sorted({fam(g["s1"])} | ({fam(g["s2"])} if g["s2"] != "none" else set())))
    sweet = "lemonade" if (g["sweet"] == "lemonade") else ("hibiscus" if "hibiscus" in g["sweet"] else "sugar")
    return (sh, g["s2"] != "none", sweet, g["where"])


def structure(g):
    two = g["s2"] != "none"
    sweet = "lemonade" if g["sweet"] == "lemonade" else ("hibiscus" if "hibiscus" in g["sweet"] else "sugar")
    return (g["s1"] if not two else tuple(sorted((g["s1"], g["s2"]))), g["where"], sweet)


RNG = random.Random(21)


def pair_neighbours(g):
    ks = list(GENES)
    for a, b in itertools.combinations(ks, 2):
        for va in GENES[a]:
            for vb in GENES[b]:
                if va != g[a] and vb != g[b]:
                    n = dict(g); n[a] = va; n[b] = vb
                    yield f"{a}+{b}", n


def restart(g, genes=4):
    n = dict(g)
    for k in RNG.sample(list(GENES), genes):
        n[k] = RNG.choice(GENES[k])
    return n


def run(rounds=20, beam=14):
    s0, e0 = score(CURRENT)
    log = [dict(round=0, score=round(s0, 2), change="current spec", spec=CURRENT, eval=e0)]
    pool = {key(CURRENT): (s0, CURRENT)}
    beamset = [CURRENT]; best = (s0, CURRENT)
    for r in range(1, rounds + 1):
        cands = {}
        moves = [(g, neighbours(g)) for g in beamset]
        moves += [(g, pair_neighbours(g)) for g in beamset[:3]]
        moves += [(None, (("restart", restart(best[1])) for _ in range(150)))]
        for g, gen in moves:
            for k, n in gen:
                kk = key(n)
                if kk in pool:
                    continue
                sc, _ = score(n)
                pool[kk] = (sc, n); cands[kk] = (sc, n, k)
        ranked = sorted(pool.values(), key=lambda x: -x[0])
        # diverse beam: at most 2 per structure
        seen = {}; beamset = []
        for sc, g in ranked:
            st = structure(g)
            if seen.get(st, 0) >= 2:
                continue
            seen[st] = seen.get(st, 0) + 1; beamset.append(g)
            if len(beamset) >= beam:
                break
        top = ranked[0]
        if top[0] > best[0] + 1e-9:
            diff = [k for k in GENES if top[1][k] != best[1][k]]
            best = top
            change = ", ".join(f"{k}: {top[1][k]}" for k in diff)
        else:
            change = "no better spec"
        newbest = max(cands.values(), key=lambda x: x[0]) if cands else None
        log.append(dict(round=r, score=round(best[0], 2), change=change, explored=len(pool), new=len(cands),
                        best_new=(round(newbest[0], 2), describe(newbest[1])) if newbest else None))
    return log, pool


if __name__ == "__main__":
    log, pool = run()
    for row in log:
        print(f"round {row['round']:>2}  best {row['score']:>6}  {row['change']}  "
              f"(+{row.get('new', 1)} new, {row.get('explored', 1)} total)")
        if row.get("best_new"):
            print(f"           best new this round {row['best_new'][0]}: {row['best_new'][1]}")
    ranked = sorted(pool.values(), key=lambda x: -x[0])
    print()
    seen = set(); picks = []
    for sc, g in ranked:
        st = concept(g)
        if st in seen:
            continue
        seen.add(st); picks.append((sc, g))
        if len(picks) >= 12:
            break
    for sc, g in picks:
        e = evaluate(g)
        print(f"{sc:6.2f} | {g['form']} x{g['fruit_mult']} | pisco {g['pisco']} | {g['s1']} {g['s1_ml']}"
              f"{' + ' + g['s2'] + ' ' + str(g['s2_ml']) if g['s2'] != 'none' else ''} in {g['where']} | "
              f"loosen {g['loosen']} | sweet {g['sweet']} (+{e['added']:.1f} g) | top {g['top']} {g['top_ml']} | "
              f"{g['bitters']} | saline {g['saline']} | cointreau {g['cointreau']}")
        print(f"        ABV {e['abv']*100:.1f}%  sugar {e['sug100']:.1f} g/100ml  ratio {e['ratio']:.1f}  "
              f"final {e['final']:.0f} ml  PF {e['pf_i']:.1f}  NUT {e['nut_i']:.1f}  cost ${e['cost']:.2f}  "
              f"flav {len(e['flav'])} {e['flav']}  struct {e['struct']}  preps {e['preps']}  life {e['life']}d")
    if "--json" in sys.argv:
        json.dump(dict(log=log, picks=[dict(score=sc, spec=g, eval=evaluate(g)) for sc, g in picks]),
                  open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1, default=str)
