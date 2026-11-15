"""PROTOTYPE: 20-iteration hill-climb for the "Dirty Martini Spritz" (Sydney wine bar).

Built in a wine glass over cubed ice: a pre-mixed batch (gin + dry vermouth + Green Queen
olive brine, ONE jigger) + 1 dash orange bitters, topped with French sparkling and soda.
Goal: maximise how strongly it READS as a dirty martini although it is a long spritz.

HONESTY: every weight, salt target, triangle edge, brine salinity, dilution figure, cost
and adjunct property below is a DESIGN ASSUMPTION, not science. The "dirty index" D is a
hand-built proxy for a bartender's intent. It does not predict taste. The loop only finds
the spec that maximises this proxy; a human must taste it. Aroma data are presence/absence
compound sets from cobber (no concentrations). Olive BRINE is not in the data: the olive
profile is used as its proxy.

Run: python3 scripts/prototypes/dirty_spritz_loop.py   (needs `pip install -e .`)
"""
from itertools import combinations, product
from cobber import engine as e

# ---------------------------------------------------------------- assumptions (all named)
ICE_MELT_ML = 20.0                 # assumed dilution from cubed ice
BITTERS_ML = 0.8                   # 1 dash orange bitters; ABV ignored
SALINITIES = (3.0, 5.0, 7.0)       # UNKNOWN brine salinity, g NaCl / 100 ml
ABV = {"gin": 40.0, "vermouth": 17.0, "sparkling": 11.5, "brine": 0.0, "soda": 0.0}
ETHANOL_G_PER_ML = 0.789           # Australian standard drink = 10 g alcohol
SUGAR_G_100 = {"vermouth": 4.0, "sparkling": 0.9}   # report only
COST_PER_ML = {"gin": 0.0429, "vermouth": 0.0303, "sparkling": 0.0182, "soda": 0.0015,
               "bitters": 0.1364, "brine": 0.01}
PRICE = 23.0                       # incl GST (report only)
SD_MIN, SD_MAX = 1.2, 1.40
STEP = 2.5
BATCH_ML = 60.0                    # fallback 50 / 70 tried only if no 60 ml spec scores
BUBBLES_MIN, SPARKLING_MIN = 60.0, 40.0
LIQUIDS_MAX, COST_MAX, MAX_COMPONENTS = 160.0, 3.60, 7
BASE_COMPONENTS = 6                # gin, vermouth, brine, sparkling, soda, bitters
# My additions (not in the brief): stop the optimiser deleting an anchor "in spirit".
MIN_GIN_ML, MIN_VERMOUTH_ML, MIN_BRINE_ML = 10.0, 10.0, 10.0
ADJ_MAX_ML = 5.0
ADJ_AMOUNTS = (2.5, 5.0)
START = dict(gin=15.0, vermouth=25.0, brine=20.0, sparkling=60.0, soda=20.0, adj=None, adj_ml=0.0)

# --- Review additions (see docs/recipes/dirty-spritz-loop-review.md). Default = ORIGINAL behaviour.
# VARIANT "honest" is a SECOND objective: no proxy-harmony term, sparkling >= 50 ml and >= soda,
# soda <= 30 ml, final ABV >= 9 %, "dirty" scored on salt % in the glass (maximin over S) + brine share.
# Select with `--honest`. Every number in it is still a design assumption, not science.
VARIANT = "original"
ADJ_ON = True                      # honest variant also runs with adjuncts switched off
H_SPARKLING_MIN, H_SODA_MAX, H_ABV_MIN = 50.0, 30.0, 9.0
W_HONEST = {"salt": 0.55, "brine": 0.35, "botanical": 0.10, "harmony": 0.0}

# Objective weights and shapes (named; sensitivity-tested later)
W = {"salt": 0.45, "brine": 0.25, "botanical": 0.20, "harmony": 0.10}
SALT_PEAK, SALT_LO, SALT_HI = 0.55, 0.25, 0.95        # % salt in glass, triangular
BRINE_FULL, BRINE_ZERO = 0.12, 0.03                   # brine share of liquids
BOT_FULL, BOT_ZERO = 0.55, 0.20                       # gin / (gin + vermouth)
HARMONY_FULL_J = 0.30              # Jaccard with olive that scores 1.0 (arbitrary scale)
WORST_TARGET, WORST_PENALTY = 0.6, 1.0                # climbing objective = mean - pen*max(0, 0.6-min)
REDUNDANT_J, MIN_NEW_SHARE = 0.80, 0.20               # olivia_loop2 rules

# Adjuncts: salinity as a multiple of S (brines) or absolute g/100ml; cost/ml and ABV are ASSUMED.
# profile_id: cobber id used for aroma (None = no aroma data). proxy flags noted.
ADJUNCTS = {
    "caperberry_brine": dict(salt_x_S=1.0, salt_abs=0, abv=0, cost=0.010, prof=None,
        why="second briny/vinegary voice that is not olive; salt/acid effect only"),
    "guindilla_brine": dict(salt_x_S=1.0, salt_abs=0, abv=0, cost=0.020, prof=None,
        why="Basque pickled-pepper tang adds savoury lift; salt/acid effect only"),
    "manzanilla": dict(salt_x_S=0, salt_abs=0, abv=15.0, cost=0.030, prof="sherry",
        why="saline, nutty fino-style note common in dirty martini riffs; aroma = generic sherry PROXY"),
    "pastis": dict(salt_x_S=0, salt_abs=0, abv=45.0, cost=0.060, prof=None,
        why="anise rinse-style lift; adds alcohol; no pastis profile in data"),
    "celery_bitters": dict(salt_x_S=0, salt_abs=0, abv=0, cost=0.1364, prof="celery_bitters",
        why="savoury celery note as in a Bloody-Mary-style martini"),
    "saline": dict(salt_x_S=0, salt_abs=20.0, abv=0, cost=0.001, prof=None,
        why="adds salt without volume (20% NaCl, 5 ml = 1 g); no aroma"),
    "lemon_oil_spray": dict(salt_x_S=0, salt_abs=0, abv=0, cost=0.0, prof="lemon", zero_ml=True,
        why="expressed lemon oil at the glass; 0 ml"),
}
DRINK_PROFILE_IDS = ["gin", "dry_vermouth", "orange_bitters", "sparkling_wine", "lemon", "olive"]
PROFILE_PROXY_NOTE = "olive brine -> olive; French sparkling -> sparkling_wine; manzanilla -> sherry"

OLIVE = e.profile("olive")
IN_DRINK = set().union(*(e.profile(i) for i in DRINK_PROFILE_IDS))


def jac(a, b):
    return len(a & b) / len(a | b) if a and b else 0.0


def adj_info(name):
    a = ADJUNCTS[name]
    p = e.profile(a["prof"]) if a["prof"] else set()
    j = jac(p, OLIVE) if p else 0.0
    dup = max((jac(p, e.profile(i)) for i in DRINK_PROFILE_IDS), default=0.0) if p else 0.0
    new = len(p - IN_DRINK) / len(p) if p else None
    blocked = bool(p) and (dup >= REDUNDANT_J or new < MIN_NEW_SHARE)
    return dict(has_data=bool(p), jac_olive=j, max_dup=dup, new_share=new, blocked=blocked)


ADJ_INFO = {n: adj_info(n) for n in ADJUNCTS}


# ---------------------------------------------------------------- model
def volumes(s):
    adj_ml = 0.0 if (s["adj"] is None or ADJUNCTS[s["adj"]].get("zero_ml")) else s["adj_ml"]
    liquids = s["gin"] + s["vermouth"] + s["brine"] + s["sparkling"] + s["soda"] + BITTERS_ML + adj_ml
    return liquids, liquids + ICE_MELT_ML, adj_ml


def ethanol_g(s):
    _, _, adj_ml = volumes(s)
    alc = sum(s[k] * ABV[k] / 100 for k in ("gin", "vermouth", "sparkling", "brine", "soda"))
    if s["adj"]:
        alc += adj_ml * ADJUNCTS[s["adj"]]["abv"] / 100
    return alc * ETHANOL_G_PER_ML  # grams of ethanol


def std(s):
    return ethanol_g(s) / 10.0


def abv_pct(s):
    """Final ABV % v/v INCLUDING adjunct alcohol (original line() omitted it). Bitters ABV ignored."""
    alc = sum(s[k] * ABV[k] / 100 for k in ABV if k in s)
    if s["adj"]:
        alc += volumes(s)[2] * ADJUNCTS[s["adj"]]["abv"] / 100
    return 100 * alc / volumes(s)[1]


def salt_pct(s, S):
    _, final, adj_ml = volumes(s)
    g = s["brine"] * S / 100
    if s["adj"]:
        a = ADJUNCTS[s["adj"]]
        g += adj_ml * (a["salt_x_S"] * S + a["salt_abs"]) / 100
    return 100 * g / final


def cost(s):
    _, _, adj_ml = volumes(s)
    c = (s["gin"] * COST_PER_ML["gin"] + s["vermouth"] * COST_PER_ML["vermouth"]
         + s["brine"] * COST_PER_ML["brine"] + s["sparkling"] * COST_PER_ML["sparkling"]
         + s["soda"] * COST_PER_ML["soda"] + BITTERS_ML * COST_PER_ML["bitters"])
    if s["adj"]:
        c += adj_ml * ADJUNCTS[s["adj"]]["cost"]
    return c


def sugar_g(s):
    _, final, _ = volumes(s)
    return (s["vermouth"] * SUGAR_G_100["vermouth"] + s["sparkling"] * SUGAR_G_100["sparkling"]) / 100


def tri(x, lo, peak, hi):
    if x <= lo or x >= hi:
        return 0.0
    return (x - lo) / (peak - lo) if x <= peak else (hi - x) / (hi - peak)


def ramp(x, zero, full):
    return max(0.0, min(1.0, (x - zero) / (full - zero)))


def D(s, S, w=None):
    w = w or W
    liquids, _, _ = volumes(s)
    sc_salt = tri(salt_pct(s, S), SALT_LO, SALT_PEAK, SALT_HI)
    sc_brine = ramp(s["brine"] / liquids, BRINE_ZERO, BRINE_FULL)
    sc_bot = ramp(s["gin"] / (s["gin"] + s["vermouth"]), BOT_ZERO, BOT_FULL)
    sc_h = 0.0
    if s["adj"] and ADJ_INFO[s["adj"]]["has_data"]:
        sc_h = min(1.0, ADJ_INFO[s["adj"]]["jac_olive"] / HARMONY_FULL_J)
    return (w["salt"] * sc_salt + w["brine"] * sc_brine + w["botanical"] * sc_bot + w["harmony"] * sc_h)


def metrics(s, w=None):
    ds = [D(s, S, w) for S in SALINITIES]
    return dict(mean=sum(ds) / 3, min=min(ds), ds=ds)


def objective_honest(s, w=None):
    """Maximin over S of the dirty index (harmony weight 0): robust to unknown brine salinity."""
    return metrics(s, w or W_HONEST)["min"]


def objective(s, w=None):
    if VARIANT == "honest":
        return objective_honest(s, w)
    m = metrics(s, w)
    return m["mean"] - WORST_PENALTY * max(0.0, WORST_TARGET - m["min"])


def feasible(s, batch=BATCH_ML):
    if VARIANT == "honest":
        if not ADJ_ON and s["adj"]:
            return False
        if s["sparkling"] < H_SPARKLING_MIN or s["sparkling"] < s["soda"] or s["soda"] > H_SODA_MAX:
            return False
        if abv_pct(s) < H_ABV_MIN - 1e-9:
            return False
    if abs(s["gin"] + s["vermouth"] + s["brine"] - batch) > 1e-9:
        return False
    if s["gin"] < MIN_GIN_ML or s["vermouth"] < MIN_VERMOUTH_ML or s["brine"] < MIN_BRINE_ML:
        return False
    if s["sparkling"] < SPARKLING_MIN or s["sparkling"] + s["soda"] < BUBBLES_MIN or s["soda"] < 0:
        return False
    if not (SD_MIN - 1e-9 <= std(s) <= SD_MAX + 1e-9):
        return False
    if volumes(s)[0] > LIQUIDS_MAX + 1e-9 or cost(s) > COST_MAX + 1e-9:
        return False
    if BASE_COMPONENTS + (1 if s["adj"] else 0) > MAX_COMPONENTS:
        return False
    if s["adj"]:
        if s["adj_ml"] > ADJ_MAX_ML or ADJ_INFO[s["adj"]]["blocked"]:
            return False
    return True


def key(s):
    return (s["gin"], s["vermouth"], s["brine"], s["sparkling"], s["soda"], s["adj"], s["adj_ml"] if s["adj"] else 0.0)


def desc(s):
    a = f" +{s['adj']} {s['adj_ml']:g}" if s["adj"] else ""
    return f"g{s['gin']:g}/v{s['vermouth']:g}/b{s['brine']:g}/sp{s['sparkling']:g}/so{s['soda']:g}{a}"


# ---------------------------------------------------------------- moves
PARTS = ("gin", "vermouth", "brine", "sparkling", "soda")
GROUP = {"gin": "batch", "vermouth": "batch", "brine": "batch", "sparkling": "bub", "soda": "bub"}


def neighbours(s):
    out = []
    for a, b in product(PARTS, PARTS):          # shift STEP ml from a to b (same group keeps batch=60)
        if a != b and GROUP[a] == GROUP[b] and s[a] >= STEP:
            t = dict(s); t[a] -= STEP; t[b] += STEP
            out.append((f"shift {STEP:g}ml {a}->{b}", t))
    for p in ("sparkling", "soda"):             # grow / shrink the topping volume
        t = dict(s); t[p] += STEP; out.append((f"grow {p} +{STEP:g}", t))
        if s[p] >= STEP:
            t = dict(s); t[p] -= STEP; out.append((f"shrink {p} -{STEP:g}", t))
    if s["adj"] is None:
        for n in ADJUNCTS:
            for amt in ADJ_AMOUNTS:
                t = dict(s); t["adj"], t["adj_ml"] = n, (0.0 if ADJUNCTS[n].get("zero_ml") else amt)
                out.append((f"add {n} {t['adj_ml']:g}ml", t))
                if ADJUNCTS[n].get("zero_ml"):
                    break
    else:
        t = dict(s); t["adj"], t["adj_ml"] = None, 0.0; out.append((f"remove {s['adj']}", t))
        for n in ADJUNCTS:
            if n != s["adj"]:
                t = dict(s); t["adj"] = n; t["adj_ml"] = 0.0 if ADJUNCTS[n].get("zero_ml") else s["adj_ml"] or 2.5
                out.append((f"swap {s['adj']}->{n}", t))
        if not ADJUNCTS[s["adj"]].get("zero_ml"):
            t = dict(s); t["adj_ml"] = 5.0 if s["adj_ml"] == 2.5 else 2.5
            out.append((f"resize {s['adj']} to {t['adj_ml']:g}ml", t))
    return [(m, t) for m, t in out if feasible(t)]


def run_loop(w=None, verbose=False, batch_start=None):
    s = dict(START)
    if not feasible(s):
        raise SystemExit("start spec infeasible")
    visited = {key(s): (s, objective(s, w))}
    cur, cur_o, log = s, objective(s, w), []
    for it in range(1, 21):
        nb = [(m, t) for m, t in neighbours(cur) if key(t) not in visited]
        scored = sorted(((objective(t, w), m, t) for m, t in nb), key=lambda x: (-x[0], x[1]))
        tag = ""
        if scored and scored[0][0] > cur_o + 1e-9:
            o, m, t = scored[0]
        else:
            # STALL: documented perturbation = best unvisited state reachable by TWO moves
            # (a larger move), chosen deterministically; may lower the objective.
            two = {}
            for m1, t1 in nb:
                for m2, t2 in neighbours(t1):
                    if key(t2) not in visited and key(t2) != key(cur):
                        two.setdefault(key(t2), (objective(t2, w), f"{m1} + {m2}", t2))
            if not two:
                raise SystemExit(f"iteration {it}: nothing left to visit")
            o, m, t = max(two.values(), key=lambda x: (x[0], x[1]))
            tag = " [PERTURB]"
        cur, cur_o = t, o
        visited[key(t)] = (t, o)
        mm = metrics(t, w)
        log.append((it, m + tag, t, mm))
        if verbose:
            print(f"{it:2d} {m + tag:52s} Dmean={mm['mean']:.3f} Dmin={mm['min']:.3f} "
                  f"SD={std(t):.2f} salt5={salt_pct(t, 5):.2f}% ${cost(t):.2f}  {desc(t)}")
    best = max(visited.values(), key=lambda x: (x[1], str(key(x[0]))))
    return best, visited, log


def exhaustive(batch=BATCH_ML, adjuncts=False, w=None):
    best = None
    grid = [x * STEP for x in range(0, int(180 / STEP))]
    adjs = [(None, 0.0)]
    if adjuncts:
        for n in ADJUNCTS:
            adjs += [(n, 0.0)] if ADJUNCTS[n].get("zero_ml") else [(n, a) for a in ADJ_AMOUNTS]
    n_feas = 0
    for g in grid:
        for v in grid:
            b = batch - g - v
            if b < 0:
                continue
            for sp in grid:
                if sp < SPARKLING_MIN:
                    continue
                for so in grid:
                    for a, am in adjs:
                        s = dict(gin=g, vermouth=v, brine=b, sparkling=sp, soda=so, adj=a, adj_ml=am)
                        if feasible(s, batch):
                            n_feas += 1
                            o = objective(s, w)
                            if best is None or (o, str(key(s))) > (best[0], str(key(best[1]))):
                                best = (o, s)
    return best, n_feas


def exhaustive_all(batch=BATCH_ML, adjuncts=False, w=None):
    """Every feasible grid spec with its objective, best first (for plateau / tie inspection)."""
    out = []
    grid = [x * STEP for x in range(0, int(180 / STEP))]
    adjs = [(None, 0.0)]
    if adjuncts:
        for n in ADJUNCTS:
            adjs += [(n, 0.0)] if ADJUNCTS[n].get("zero_ml") else [(n, a) for a in ADJ_AMOUNTS]
    for g in grid:
        for v in grid:
            b = batch - g - v
            if b < 0:
                continue
            for sp in grid:
                for so in grid:
                    for a, am in adjs:
                        s = dict(gin=g, vermouth=v, brine=b, sparkling=sp, soda=so, adj=a, adj_ml=am)
                        if feasible(s, batch):
                            out.append((objective(s, w), s))
    out.sort(key=lambda x: (-x[0], str(key(x[1]))))
    return out


def exhaustive_unguarded(adjuncts=False):
    """Same grid, but anchor minimums relaxed to 2.5 ml: shows what the objective WANTS.
    NOTE: original ran with adjuncts=False only, so it did not test the adjunct winner unguarded."""
    global MIN_GIN_ML, MIN_VERMOUTH_ML, MIN_BRINE_ML
    old = (MIN_GIN_ML, MIN_VERMOUTH_ML, MIN_BRINE_ML)
    MIN_GIN_ML = MIN_VERMOUTH_ML = MIN_BRINE_ML = 2.5
    try:
        return exhaustive(adjuncts=adjuncts)
    finally:
        MIN_GIN_ML, MIN_VERMOUTH_ML, MIN_BRINE_ML = old


def line(s, w=None):
    m = metrics(s, w)
    return (f"{desc(s)} | Dmean={m['mean']:.3f} Dmin={m['min']:.3f} (S3/5/7 {m['ds'][0]:.2f}/{m['ds'][1]:.2f}/{m['ds'][2]:.2f}) "
            f"SD={std(s):.2f} ABV={abv_pct(s):.1f}% "
            f"salt%(3/5/7)={salt_pct(s, 3):.2f}/{salt_pct(s, 5):.2f}/{salt_pct(s, 7):.2f} "
            f"brine%liq={100 * s['brine'] / volumes(s)[0]:.1f} gin/(g+v)={s['gin'] / (s['gin'] + s['vermouth']):.2f} "
            f"cost=${cost(s):.2f} sugar={sugar_g(s):.1f}g")


def main():
    print("ASSUMPTIONS: ice melt %g ml; bitters %g ml; S in %s; proxies: %s" % (
        ICE_MELT_ML, BITTERS_ML, SALINITIES, PROFILE_PROXY_NOTE))
    print("Weights", W, "| salt triangle", (SALT_LO, SALT_PEAK, SALT_HI), "| worst-case penalty", WORST_PENALTY)
    print("\nADJUNCT SCREEN (Jaccard with olive proxy; redundancy rules from olivia_loop2):")
    for n, i in ADJ_INFO.items():
        flag = "BLOCKED" if i["blocked"] else ("no aroma data (salt/acid only)" if not i["has_data"] else "ok")
        print(f"  {n:18s} J_olive={i['jac_olive']:.2f} maxdup={i['max_dup']:.2f} "
              f"new={'-' if i['new_share'] is None else format(i['new_share'], '.2f')} {flag} | {ADJUNCTS[n]['why']}")
    print(f"\nSTART: {line(START)}\n")
    best, visited, log = run_loop(verbose=True)
    print(f"\nLOOP BEST (batch 60): {line(best[0])}")
    print("\nTOP 5 DISTINCT SPECS visited (objective order; worst-case>=0.6 preferred by the objective):")
    top = sorted(visited.values(), key=lambda x: -x[1])[:5]
    for i, (s, o) in enumerate(top, 1):
        print(f" {i}. obj={o:.3f} {line(s)}")
        if s["adj"]:
            print(f"      adjunct: {ADJUNCTS[s['adj']]['why']}")

    print("\nSENSITIVITY (each weight x0.5 / x1.5, renormalised to sum 1; loop rerun):")
    for k in W:
        for f in (0.5, 1.5):
            w = dict(W); w[k] *= f
            tot = sum(w.values()); w = {a: b / tot for a, b in w.items()}
            b2, _, _ = run_loop(w)
            same = key(b2[0]) == key(best[0])
            print(f"  {k:9s} x{f}: {'SAME winner' if same else 'CHANGED -> ' + desc(b2[0])}"
                  f"  (Dmean={metrics(b2[0], w)['mean']:.3f} Dmin={metrics(b2[0], w)['min']:.3f})")

    print("\nEXHAUSTIVE (amounts grid, batch 60):")
    ex, n = exhaustive()
    print(f"  no adjuncts ({n} feasible): obj={ex[0]:.3f} {line(ex[1])}")
    exa, na = exhaustive(adjuncts=True)
    print(f"  with adjuncts ({na} feasible): obj={exa[0]:.3f} {line(exa[1])}")
    print(f"  loop best obj={best[1]:.3f} -> gap to exhaustive(adj) = {exa[0] - best[1]:+.3f}; "
          f"to exhaustive(no adj) = {ex[0] - best[1]:+.3f}")
    for bt in (50.0, 70.0):
        eb, nb_ = exhaustive(batch=bt)
        print(f"  batch {bt:g} (info only, {nb_} feasible): " + (f"obj={eb[0]:.3f} {line(eb[1])}" if eb else "none feasible"))
    ug, nu = exhaustive_unguarded()
    print(f"  UNGUARDED anchors (min 2.5 ml; {nu} feasible): obj={ug[0]:.3f} {line(ug[1])}")


def main_honest():
    """Second objective (review fix). Prints loop, exhaustive plateau, edge sensitivity, ablations."""
    global VARIANT, ADJ_ON, SALT_PEAK, SALT_LO, SALT_HI, BRINE_FULL, BRINE_ZERO, BOT_FULL, BOT_ZERO
    VARIANT = "honest"
    print("HONEST VARIANT: harmony weight 0; sparkling>=%g and >=soda; soda<=%g; final ABV>=%g%%; objective = "
          "min over S of D (weights %s). Adjuncts have no scored benefit except salt." % (
              H_SPARKLING_MIN, H_SODA_MAX, H_ABV_MIN, W_HONEST))
    for adj_on in (False, True):
        ADJ_ON = adj_on
        print(f"\n=== adjuncts {'ON' if adj_on else 'OFF'} ===")
        best, visited, log = run_loop(verbose=True)
        print(f"LOOP BEST: obj={best[1]:.3f} {line(best[0], W_HONEST)}")
        allr = exhaustive_all(adjuncts=adj_on)
        top = allr[0][0]
        near = [(o, s) for o, s in allr if o >= top - 0.01]
        print(f"EXHAUSTIVE: {len(allr)} feasible; best obj={top:.3f}; {len(near)} specs within 0.01. Top 6:")
        for o, s in allr[:6]:
            print(f"  obj={o:.3f} {line(s, W_HONEST)}")
        rng = lambda k: (min(s[k] for _, s in near), max(s[k] for _, s in near))
        print("  near-optimal ranges:", {k: rng(k) for k in ("gin", "vermouth", "brine", "sparkling", "soda")})
        print(f"  loop gap to exhaustive: {top - best[1]:+.3f}")
    ADJ_ON = False
    print("\nEDGE SENSITIVITY (adjuncts off; shape edges moved, exhaustive winner + top-ties count):")
    base = (SALT_LO, SALT_PEAK, SALT_HI, BRINE_ZERO, BRINE_FULL, BOT_ZERO, BOT_FULL)
    cases = {"base": {}, "salt peak 0.45": dict(SALT_PEAK=0.45), "salt peak 0.65": dict(SALT_PEAK=0.65),
             "salt lo/hi 0.15/0.85": dict(SALT_LO=0.15, SALT_HI=0.85, SALT_PEAK=0.5),
             "brine full 0.10": dict(BRINE_FULL=0.10), "brine full 0.14": dict(BRINE_FULL=0.14),
             "botanical full 0.45": dict(BOT_FULL=0.45), "botanical full 0.65": dict(BOT_FULL=0.65)}
    g = globals()
    for name, ch in cases.items():
        for k, v in ch.items():
            g[k] = v
        r = exhaustive_all()
        near = [x for x in r if x[0] >= r[0][0] - 0.01]
        print(f"  {name:22s} best obj={r[0][0]:.3f} {desc(r[0][1])} ABV={abv_pct(r[0][1]):.1f}% brine%liq={100*r[0][1]['brine']/volumes(r[0][1])[0]:.1f} (n_near={len(near)})")
        (g["SALT_LO"], g["SALT_PEAK"], g["SALT_HI"], g["BRINE_ZERO"], g["BRINE_FULL"], g["BOT_ZERO"], g["BOT_FULL"]) = base
    VARIANT = "original"


def main_ablation():
    """ORIGINAL objective with the harmony term removed: how much of the adjunct gain was harmony?"""
    global W
    old = dict(W)
    W = {"salt": 0.45, "brine": 0.25, "botanical": 0.20, "harmony": 0.0}
    tot = sum(W.values()); W = {k: v / tot for k, v in W.items()}
    print("ABLATION: original constraints/objective, harmony weight 0 (renormalised)")
    for adj in (False, True):
        r = exhaustive_all(adjuncts=adj)
        print(f" adjuncts {'ON ' if adj else 'OFF'}: best obj={r[0][0]:.3f} {line(r[0][1])}")
    W = old


if __name__ == "__main__":
    import sys
    if "--honest" in sys.argv:
        main_honest()
    elif "--ablation" in sys.argv:
        main_ablation()
    else:
        main()
