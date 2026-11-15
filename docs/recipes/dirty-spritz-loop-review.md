# Dirty Martini Spritz: adversarial review of the 20-loop optimiser

Date: 2026-11-15. Scope: `scripts/prototypes/dirty_spritz_loop.py` and
`docs/recipes/dirty-spritz-research.md`. Not committed.

Evidence labels: **CHECKED** = recomputed here or run here. **ASSUMPTION** =
a number someone chose. **EXCERPT** = from the research file, never verified
against a page. Nothing about taste in this review is evidence. The index D is
a hand-built proxy.

## Verdict in five lines

1. The arithmetic (volumes, standard drinks, salt %) is right. The printed ABV
   was wrong for adjunct specs (fixed). Nothing else numeric was broken.
2. The headline "0.792 vs 0.689" is an artefact. The entire gain is the
   `harmony` term (weight 0.10) scoring generic sherry as if it were
   manzanilla, with no dependence on dose. The same spec without manzanilla
   scores 0.686.
3. The winners are a highball (42-46% of the bubbles are sparkling), built by
   swapping sparkling wine for soda so gin can rise under the standard-drink
   cap. They are not a spritz.
4. Under an honest objective the answer moves to about 20 gin / 22.5 vermouth
   / 17.5 brine / 50 sparkling / 20 soda. This is still a proxy. Its one
   robust output is a formula, not a spec: **brine ml = target salt % x final
   volume / brine salinity**. Salinity is unknown, so the spec cannot be
   settled by any optimiser.
5. Measure the brine first (a scale and a 100 ml jigger). Then bench.

## 1. Independent recompute (CHECKED)

Separate script (no cobber or optimiser imports), 0.8 ml bitters counted as
volume, 20 ml ice melt, ABV gin 40 / vermouth 17 / sparkling 11.5 / manzanilla
15 (all ASSUMPTIONS inherited from the prototype). Final volume = liquids + 20.

| Spec (ml) | Liquids | Final | ABV (final) | Std drinks | Salt % S=3/5/7 | Brine % liquids | Sparkling share of bubbles |
|---|---|---|---|---|---|---|---|
| Current 15/25/20/60/20 | 140.8 | 160.8 | 10.67% | 1.353 | 0.37 / 0.62 / 0.87 | 14.2 | 75% |
| W1 22.5/17.5/20/42.5/50 + manz 5 | 158.3 | 178.3 | 9.88% | 1.390 | 0.34 / 0.56 / 0.79 | 12.6 | 46% |
| W2 22.5/17.5/20/40/52.5 + manz 5 | 158.3 | 178.3 | 9.72% | 1.367 | same | 12.6 | 43% |
| W3 22.5/17.5/20/42.5/52.5 + manz 2.5 | 158.3 | 178.3 | 9.67% | 1.360 | same | 12.6 | 45% |
| Printed loop best 25/15/20/40/55 + manz 2.5 | 158.3 | 178.3 | 9.83% | 1.383 | same | 12.6 | 42% |
| No-adjunct exhaustive 25/17.5/17.5/40/30 | 130.8 | 150.8 | 11.65% | 1.387 | 0.35 / 0.58 / 0.81 | 13.4 | 57% |

Discrepancies against the optimiser:

- **ABV printed by `line()` omitted adjunct alcohol** (it summed the five
  base ingredients only). It showed 9.5 / 9.3 / 9.5 / 9.6 for W1 / W2 / W3 /
  loop best against the true 9.88 / 9.72 / 9.67 / 9.83. Standard drinks,
  salt % and brine share match exactly. Fixed in the script (`abv_pct`).
- **Bitters are counted as volume but not as alcohol.** If orange bitters are
  about 40% ABV (ASSUMPTION; no figure in the repo), 0.8 ml adds 0.025 std
  drinks. W1 then reads 1.415 and the loop best 1.408, both over the 1.40 cap.
  The "cap is respected" claim therefore holds only by about 0.01 to 0.03, which
  is below the uncertainty of the ABV inputs. Treat 1.34-1.39 as "at the cap",
  not "under" it.
- Ice melt is a flat 20 ml whatever the drink. A 10% ABV drink with 50 ml soda
  over ice would melt differently from a 150 ml one. ASSUMPTION, not tested.

## 2. Code audit

Fine (CHECKED):

- Units: ABV in percent, divided by 100 once; 0.789 g/ml; `std = g / 10`.
- Steps of 2.5 ml: every move is a multiple of 2.5 and the exhaustive grid is
  `range(0, 72) * 2.5`. Floats are exact in binary (2.5 = 5/2), so the `1e-9`
  batch test is sound.
- Batch = 60: `shift` moves are only allowed within a group (gin / vermouth /
  brine, or sparkling / soda), so the batch sum is invariant. Exhaustive sets
  `brine = 60 - gin - vermouth`. Both are correct. Note this also means the
  loop can never trade batch volume against topping volume except through the
  separate `grow`/`shrink` moves on sparkling and soda.
- Visited set: `nb` excludes visited states, and a perturbation target is also
  checked against `visited`. `best` is the max over all visited states, so
  perturbation downhill cannot lose the best. Sound.
- The loop did reach the exhaustive optimum (gap 0.000) in both the original
  and the honest runs. It is a hill-climb on a 6,500 to 60,000 state grid that
  an exhaustive search covers in seconds, so the loop adds nothing except that
  it demonstrates the climb.

Weak or misleading:

- **Min-over-S term is inactive at every winner.** The objective is
  `mean - 1.0 x max(0, 0.6 - min)`. The winners have Dmin 0.671 > 0.6, so the
  penalty is zero and the objective equals Dmean. It is a gate at an arbitrary
  0.6, not a robustness incentive. The only spec in the original run that
  triggers it is the no-adjunct best (Dmin 0.597, penalty 0.003).
- **Mean over S = {3, 5, 7} is a hidden centring on S = 5.** Salt % scales
  linearly in S, so the best a mean can do is put S = 5 on the triangle peak.
  S = 5 is just the middle of an assumed range. The winners' salt % is 0.34 /
  0.56 / 0.79 across S, which scores 0.67 / 0.98 / 0.73. The "0.98" is a
  statement about an S the research file does not support (its only
  retail-label figure is about 4%).
- **PERTURB wanders on plateaus.** When no unvisited neighbour improves, it
  takes the best two-move state, which may be equal or lower. Twelve of 20
  iterations in the original run are perturbations, and the objective is flat
  (0.792) from iteration 14. Ties break by lexicographic move text, which is
  arbitrary. The "20 iterations" are mostly random-walk on a plateau, so the
  top-5 list is five tied states, not five alternatives with evidence.
- **`exhaustive_unguarded()` ran with adjuncts off**, so it never tested the
  manzanilla winner unguarded, yet it is printed as a comparison to the
  adjunct winner. It was relabelled in the docstring and given an `adjuncts`
  argument; the default is unchanged.
- **Exhaustive best "with adjuncts" 0.792 vs "no adjuncts" 0.687 mixes
  effects.** See 3(a).
- Adjunct salt: `saline` is modelled as 20% NaCl independent of S. That makes
  it look robust across S for free. It is an assumption about a product the
  bar does not stock. The original rightly did not pick it.

## 3. The four exploitation points

**(a) Harmony proxy: confirmed, and it is the whole gain.** CHECKED:

- W1's spec with the manzanilla removed scores 0.686, equal to the no-adjunct
  optimum (0.687). Adding 5 ml manzanilla gives 0.792; adding 2.5 ml gives
  0.787. The step is +0.09 from `0.10 x min(1, 0.27/0.30)` and about +0.015
  from the extra 5 ml of volume nudging salt % onto the triangle peak.
- The score does not depend on dose (2.5 and 5 ml give the same harmony
  credit). A flat credit for any amount cannot be read as flavour.
- It uses the generic `sherry` profile, whose Jaccard with `olive` is 0.27
  (presence/absence of compounds, no concentrations). Manzanilla is not in the
  data and olive BRINE is not either; olive FRUIT stands in for brine. Two
  proxies stacked.
- With the harmony weight set to 0 (`--ablation`), adjuncts ON and OFF give the
  same best spec: no adjunct ever wins on the remaining terms.
- Sensitivity runs (weights x0.5 / x1.5) all keep manzanilla because they
  rescale a term that is always positive for it.

**(b) Edge-sitting: confirmed.** The winners sit just past each saturation
edge: brine share 12.6% against the 12% "full" ramp point; gin / (gin +
vermouth) 0.56 against the 0.55 "full" point; salt 0.56 against the 0.55 peak;
sparkling at its 40 ml floor; strength at its cap. On the honest variant,
moving the edges moves the winner (section 4). Edge positions are not
measurable facts.

**(c) Soda inflation: confirmed, and the mechanism is the strength cap, not
salt tuning alone.** Under a 1.40 cap, sparkling wine (11.5%) costs alcohol
that gin could use. The botanical term rewards gin share to 0.55, so the
optimiser swaps sparkling for soda and uses the alcohol on gin. The result is
9.3-9.9% ABV with 40-45 ml of sparkling against 50-55 ml of soda. That is a
highball by volume. A wine bar selling a "spritz" would be selling the wrong
drink. Soda also dilutes salt back down from 0.62%, so brine can stay at 20 ml
and keep a full brine score.

**(d) Strength capped, not scored: confirmed.** The objective never sees
strength. The previous drink had 10.7% ABV; the winners are 9.7-9.9% and the
printed figures understate that. An ABV floor of 9% would not even bind here.
The more useful lens is that every winner is pinned to the 1.40 cap, so the
spec is a function of a regulatory-style number, not of flavour.

## 4. Second objective ("honest" variant)

Added to the prototype; default behaviour unchanged (CHECKED: original output
identical apart from the ABV display fix). Run with `--honest`.

Changes: harmony weight 0; sparkling at least 50 ml and at least soda; soda at
most 30 ml; final ABV at least 9%; adjuncts off for the primary run; weights
salt 0.55 / brine 0.35 / botanical 0.10; objective = min over S of D (maximin),
not a mean. Everything else (steps, batch = 60, cap 1.40, cost, liquids 160)
is unchanged.

Results (20-loop and exhaustive agree, gap 0.000; 3,623 feasible specs
without adjuncts, 33,523 with):

| Spec (ml) | min D | Std drinks | ABV | Salt % S=3/5/7 | Brine % liquids |
|---|---|---|---|---|---|
| **20 gin / 22.5 vermouth / 17.5 brine / 50 sparkling / 20 soda** | 0.607 | 1.39 | 11.7% | 0.35 / 0.58 / 0.81 | 13.4 |
| 20 / 22.5 / 17.5 / 50 / 17.5 | 0.598 | 1.39 | 11.9% | 0.35 / 0.59 / 0.83 | 13.6 |
| 17.5 / 22.5 / 20 / 60 / 30 | 0.597 | 1.40 | 10.4% | 0.35 / 0.59 / 0.82 | 13.3 |
| 20 / 22.5 / 17.5 / 50 / 22.5 | 0.597 | 1.39 | 11.5% | 0.34 / 0.57 / 0.80 | 13.1 |

With adjuncts allowed the winner is the same (manzanilla only shows up in
lower-ranked states). Observations:

- The ABV floor does not bind (11.7%). Binding constraints are the sparkling
  floor (50 ml), the strength cap (1.39 of 1.40) and the S range.
- The winner moves when edge positions move (salt peak 0.45 gives soda 30 and
  ABV 10.9%; peak 0.65 gives 20/20/20/52.5/30; moving the salt window gives
  17.5/27.5/15/50/20, brine share 11.5%). Brine in the batch ranges 15-20 ml
  and soda 17.5-30 ml across these edge shifts. Only sparkling = 50 (its floor)
  and gin 17.5-20 never move. **The specific numbers are not robust; the
  region (brine 15-20 ml per 60 ml batch, soda 17.5-30, sparkling at the floor)
  is.**
- Min D is only 0.607 because the spread of S (3-7 g/100 ml) puts salt % at
  0.35-0.81 and no single spec sits on the peak across all three. Maximin
  cannot fix an unknown input; it can only hedge.
- This variant is a proxy too. Weights and edges are my choices, not evidence.

## 5. Sanity check against the research benchmarks

Salt % in glass computed for the research table (CHECKED arithmetic on
EXCERPT inputs; melt only where stated):

| Build | Brine ml / total ml | Brine share | Salt % S=3/5/7 |
|---|---|---|---|
| Difford's dirty martini, no dilution | 15 / 97 | 15.5% | 0.46 / 0.77 / 1.08 |
| Same, +25% stirring dilution (rule of thumb, unverified) | 15 / 121 | 12.4% | 0.37 / 0.62 / 0.87 |
| Dan Murphy's Dirty Spritz | 15 / 150 | 10.0% | 0.30 / 0.50 / 0.70 |
| Badger Liquor / Aisle Prompt | 15 / 165 | 9.1% | 0.27 / 0.45 / 0.64 |
| Atsu's Dirty Martini Hi, before soda | 20 / 113 | 17.7% | 0.53 / 0.88 / 1.24 |
| Current spec (20 melt) | 20 / 161 | 12.4% | 0.37 / 0.62 / 0.87 |
| Honest winner (20 melt) | 17.5 / 151 | 11.6% (13.4% pre-melt) | 0.35 / 0.58 / 0.81 |

- A brine share of 12-14% of liquid is **above the published long builds
  (8-10%) and below the classics (15-17%)**. That matches where the brief
  places it. It does not prove it tastes dirty. Note two definitional hazards:
  the optimiser's share excludes ice melt (so 13.4% becomes 11.6% with melt)
  and the research file quotes classics before stirring dilution (so 15.5%
  becomes about 12.4%). Compared like for like, the spec is about the same
  salt as a stirred classic and 20-40% above the long builds.
- A salt level of 0.55% w/v: **there is no evidence in the repo that it is
  right.** The research file says plainly that no sensory range for dirty
  martinis, Bloody Mary, gose or tomato juice was found (section 4 of the
  file). The only evidence points are a cream-soup detection threshold of
  about 0.04-0.06% (irrelevant to preference, and a different matrix) and the
  derived 0.5% for a classic that assumes a 4% brine and a 25% dilution rule,
  both unverified. 0.55% is simply what a classic works out to under those two
  assumptions. It is a plausible target, not a known one.
- What is evidence: the benchmark builds (EXCERPT), the arithmetic above
  (CHECKED), and the Fee Brothers label figure (DERIVED about 4.1% if all
  sodium is NaCl). What is assumption: brine salinity in the real house brine
  (3-7 in the loop; the research file offers 4 and "9-10 for the processing
  brine"), the 0.55% target, the triangle width, the 20 ml melt, all weights.
- A caution the optimiser hides: salinity of 9-10% w/v (the processing figure
  in the research notes) gives 1.4% salt in the current spec. That is outside
  S = 3-7 and outside the loop entirely.

## 6. Conclusions

Robust (does not depend on made-up weights):

- Arithmetic: volumes, standard drinks, salt % per S (CHECKED).
- Salt % in the glass is linear in brine ml and S: **brine ml = target % x
  final ml / S**. At a 0.55% target and about 170 ml final, that is about 31 ml
  of brine at S = 3, 19 ml at S = 5, 13 ml at S = 7. The 3-7 range is a 2.3x
  swing in brine needed. This dominates every other choice.
- The cap of 1.40 standard drinks, the need to put sparkling wine's alcohol
  somewhere, and 60 ml pours force the trade: more gin means less sparkling.
- The current spec sits at about the same salt as a stirred classic and 20-40%
  above published long builds, if the brine is about 4-5%.

Artefacts (do not act on them):

- 0.792 vs 0.689 and the manzanilla winner (harmony proxy, dose-blind).
- 50-55 ml soda with 40-45 ml sparkling.
- The exact edges: brine 20 ml, gin 22.5, "12.6% of liquid", S = 5 centring.
- The `0.6` worst-case gate and "loop gap 0.000" (a 60,000-state grid).
- Plateau of tied top-5 specs from PERTURB.

## 7. Bench test (a scale, a jigger, a tasting spoon)

1. **Measure the brine.** Weigh 100 ml of the house Green Queen brine. Then
   check salinity with a brine hydrometer or a lab sodium test (the research
   file says a hydrometer reads salt as % by weight, and density overestimates
   NaCl because of acid and sugars). If neither is available, dissolve a known
   mass of salt in water to make 3%, 5% and 7% reference solutions and taste
   them next to the brine at 1:4 dilution, in the glass, with the same ice.
   The test settles S, which is the open input.
2. **Then run one salt ladder, not a flavour contest.** Make the same drink
   with brine at 12.5 / 15 / 17.5 / 20 / 22.5 ml, same everything else, batch
   topped up with gin and vermouth to keep 60 ml. Taste blind, serve over the
   house ice, and ask only: "does it taste dirty, and is it too salty?".
   Choose the lowest brine that tastes dirty. That gives the target salt %
   and tests the 0.55% guess directly.

Do the salinity measurement first. If S is near 3%, the answer is 30 ml of
brine and none of the specs here apply. If S is near 7%, the answer is 13 ml.

## 8. Recommended spec to bench, with two alternatives (ml)

All three assume brine around 4-5 g/100 ml. If the measured figure differs,
rescale brine with the formula in section 6 and top up the 60 ml batch with
vermouth.

- **Recommended: 20 gin / 22.5 vermouth / 17.5 brine** (batch 60), **50
  sparkling, 20 soda**, 1 dash orange bitters. 1.39 std drinks, about 11.7%
  ABV (assuming 20 ml melt), brine 13.4% of liquid, salt about 0.58% at S = 5.
  Sparkling is 71% of the bubbles. Still a spritz.
- **Alternative A (lighter, closer to current): 17.5 gin / 22.5 vermouth /
  20 brine, 60 sparkling, 30 soda.** 1.40 std drinks, about 10.4% ABV, salt
  about 0.59% at S = 5. This is the 3rd-ranked honest spec; it keeps more
  sparkle and more brine and is at the cap.
- **Alternative B (if the brine tests salty, S of 6-7 or above): 17.5 gin /
  27.5 vermouth / 15 brine, 50 sparkling, 20 soda.** Not run by the optimiser;
  same family with brine cut to 25% of the batch. Recomputed by hand: 1.375
  std drinks, about 11.6% ABV, salt 0.30 / 0.50 / 0.70% at S = 3 / 5 / 7,
  brine 11.5% of liquid. (An earlier draft of this alternative used 20 gin /
  25 vermouth and would have been 1.42 std drinks, over the cap; it was
  dropped.)

Not tested anywhere: bitters, ice melt, carbonation effects on perceived salt
(Cowart, direction not in the excerpt), glass and ice size, and olive garnish.
