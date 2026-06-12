# Handoff — current state of the co-occurrence work

*Updated 12 June 2026 (session, branch `claude/gallant-tesla-n1ad47`, PR #4).
Supersedes the original Copilot handoff. Read `docs/cobber-design-notes.md`
first for the project's thinking; this file is "where we are and what's next".*

## Status snapshot

- **Canon corpus:** 4,582 recipes — Difford's 3,539 + Mr. Boston 733 +
  TheCocktailDB 231 + IBA 75 + hand-curated 4 (dedupe priority:
  craft > IBA > Difford's > Mr. Boston > TheCocktailDB).
- **Frontier corpus:** ~5,900 craft drinks (Kindred 5,310 + Hotaling 589) →
  3,304 attributed pairs in `data/frontier_evidence.json` (NOT in tradition).
- **Pairs:** 2,532 scored pairs in `data/tradition.json` (627 solid).
- Difford's + Kindred come from the cocktailApp CRAN package (LGPL-3,
  scraped 2017-18 by its author who disclaims copyright; we mirror it as a
  published research dataset — provenance noted in fetch_cocktailapp.py).
- **Proportion templates:** 12 templates in `data/proportion_templates.json`
  (10 k-means + 2 equal-parts overlays) from ~8,400 cocktailapp recipes.
  PROVISIONAL — Ari to name the templates.
- **Tests:** 32 passing (`python -m pytest tests/ -q`).
- **Flavour families:** 22 diagnostic clusters in `data/flavor_communities.json`
  that read like a bar menu (daiquiri/mojito family, martini family,
  after-dinner cream-coffee family, tiki, mulled-wine spices…).

## Technique mining: DONE this session (12 June 2026)

- **Source data:** 441 TheCocktailDB (strInstructions) + 77 IBA (preparation field)
  → 486 annotated recipes, 32 unparseable.
- **Script:** `scripts/mine_techniques.py` → `data/technique_associations.json`.
  Outputs per-recipe annotations (audit trail), signal→technique frequency tables,
  and 10 priority-ordered rules.
- **Rules (priority order):**
  1. `egg_white` → dry_shake + shake, coupe up (data: 80% of egg-white recipes shake)
  2. `carb_only` (spirit + soda, no acid) → build, highball (G&T, Highball)
  3. `herb+acid+carb` (Mojito) → muddle + build, highball, top w/soda
  4. `acid+carb`, no herb (Collins, Gin Fizz) → shake base, highball, top w/soda
  5. `dairy+acid` (cream sour) → shake, coupe up (data: 29% — noisy)
  6. `dairy`, no acid (White Russian) → build, rocks/big ice cube (data: 28%)
  7. `acid`, no carb (Daiquiri, Whiskey Sour) → shake, coupe up (data: 49% — noisy)
  8. `herb`, no acid (Mint Julep) → muddle + build, rocks (data: 40%)
  9. `spirit_only` (Old Fashioned, Negroni, Manhattan) → stir, rocks (data: 41%)
  10. `default` → build, rocks
- **Engine:** `suggest_technique(ingredient_ids)` in engine.py; `_detect_technique_signals()`
  maps Cobber ingredient IDs to signals (role + specific ID checks for carbonated ingredients,
  which span multiple roles: soda_water=mixer, tonic_water=bitter, ginger_ale=sweet,
  sparkling_wine=aromatic). `build_around()` now includes `technique` field alongside `template`.
- **MCP tool:** `suggest_technique` exposed as standalone tool; server INSTRUCTIONS step 5
  updated to relay technique + service + pre_steps to Cobber.
- **Spot-checked (all verified against real recipes):** Daiquiri→shake/coupe,
  Negroni→stir/rocks, Old Fashioned→stir/rocks, G&T→build/highball,
  Whiskey Sour+egg→dry_shake+shake/coupe, Tom Collins→shake+top/highball,
  Mojito→muddle+build+top/highball, White Russian→build/rocks (after the dairy split).
- **OPEN — cream-without-acid is genuinely ambiguous (needs Ari's call).** The
  corpus splits this family almost evenly: shake 31% / build 28% / blend 15% /
  layer 15% / stir 11% — no dominant technique. Two real sub-families share the
  same ingredient signature:
  - *Built sippers* — White Russian, Sombrero, Mudslide (coffee liqueur + cream,
    long on the rocks) → build/rocks.
  - *Shaken dessert cocktails* — Brandy Alexander, Grasshopper, Pink Squirrel
    (crème liqueur + cream) → shake/up.
  Current `dairy_build` rule forces build/rocks (honours Ari's explicit White
  Russian correction) but would mis-handle the Alexander/Grasshopper family.
  Decision needed: (a) accept build/rocks as the default and let the host
  override for dessert cocktails; (b) split on coffee-liqueur vs crème-liqueur;
  (c) return an explicit "ambiguous" technique that flags both paths. Flagged,
  not silently coerced.
- **Naming-accuracy pass:** removed a fabricated cream "White Lady" (the classic
  is gin + Cointreau + lemon, no cream) and an incorrect "Irish Coffee" example
  (it's a hot, cream-floated drink, not a built-over-ice one); corrected the
  no-acid herb example from "Smash" (has citrus → shaken) to "Mint Julep".
- **Tests:** 9 new technique tests; 42 total passing.
- PROVISIONAL — Ari to review rule priorities and rationale text.

## Decisions made this session (12 June 2026) — proportion templates

1. **Two role vocabularies, not one.** Cobber's 10-role balance vocabulary
   (spirit/sour/sweet/bitter/aromatic/fruit/herb/dairy/mixer/seasoning) is
   designed for balance checks, not proportion clustering. Templates use a
   separate 9-role *structural* vocabulary (spirit/liqueur/amaro/
   vermouth_fortified/acid/sweet/juice_mixer/lengthener/egg_cream) that maps
   onto cocktail-structure archetypes (Sour, Old Fashioned, Negroni, Highball,
   Flip). Bridged in engine.py via `_TEMPLATE_ROLE_BY_COBBER_ROLE` +
   per-ingredient overrides (`_TEMPLATE_ROLE_OVERRIDES`). The two vocabularies
   remain decoupled — balance uses its own, templates use theirs.
2. **K-means at k=10, plus two equal-parts overlays.** Silhouette analysis
   (k=5..14) peaked at k=5 (0.296) but that's too coarse for practical use
   (Old Fashioned and Daiquiri collapse together). k=10 (0.266) gives usable
   granularity. K-means *cannot* reliably discover equal-thirds clusters
   (Negroni, Last Word) because those drinks sit exactly on centroid boundaries
   — at k=9+ Negroni splits between "Amaro Build" and "Spirit+Vermouth". Fix:
   a post-hoc equal-parts overlay detector with specific role-family criteria:
   Negroni-style (spirit+amaro+vermouth_fortified each ≥25%, within 12%,
   sum ≥75%), Last Word-style (spirit+liqueur+amaro+acid each ≥18%, within
   12%, sum ≥75%). Result: 107 Negroni-overlay drinks, Negroni confirmed as
   benchmark; 88 Last Word-overlay drinks.
3. **Classifier bug fixed: brandies are spirits.** `cognac`, `calvados`,
   `armagnac`, `pisco`, and `grappa` were initially in the liqueur keyword
   list ("brandies often as modifiers") — wrong. They are base spirits and
   belong in `_SPIRIT_CHECK`. The bug caused the Sidecar's cognac base to be
   classified as liqueur, landing it in a "Liqueur-Forward" cluster. Fix
   verified: Sidecar now correctly lands with Cosmopolitan/Margarita in the
   Spirit+Liqueur cluster.
4. **Pre-filter for absent roles prevents semantic mismatches.** Without it,
   Old Fashioned (bourbon + bitters [excluded] + sugar = spirit 50%, sweet
   50%) was closest to the Sour template (spirit 50%, acid 21%, sweet 16%)
   because the L2 distance didn't penalise a missing acid dimension. Fix:
   before computing distance, exclude any template that requires ≥10% of a
   role absent from the combination. Old Fashioned → Spirit-Forward ✓;
   Gimlet (spirit + lime) → Sour ✓; Highball (spirit + soda) → Highball ✓.
5. **Proportions as fractions (0–1), not ml.** Pour culture is not uniform:
   AU bars cap ~60 ml spirit, US guides pour bigger. All template centroids
   are fractions of total pour volume. The host Claude scales to the session's
   pour culture (e.g. "pick 45 ml spirit, scale everything else"). This also
   makes the dose-gating proportion switch (roadmap concern) straightforward
   when it lands.
6. **All template names PROVISIONAL — Ari's bartender review required.**
   `suggested_name` values in `data/proportion_templates.json` are
   descriptive placeholders from the clustering (e.g. "Spirit-Forward Build",
   "Sour Template", "Negroni Equal-Thirds"). Ari reviews the benchmarks +
   centroids and renames before the engine treats any name as canonical.
   The server INSTRUCTIONS already tell the host to use the structural
   description ("a Sour-style build") rather than the template name when
   PROVISIONAL — so the data gap is safe to ship.

## Decisions made prior (and why)

1. **Tradition = log-scaled prevalence, not raw NPMI.** Raw NPMI structurally
   zeroes ubiquitous classics (gin+lime scored 0.0 → the engine called a
   gimlet maximally novel) and gives one-off pairs a perfect 1.0. Tradition is
   now `log1p(count)/log1p(max_count)`; raw `npmi` kept per row.
2. **Alias/vocabulary pass (Ari's bartender calls).** White + powdered sugar →
   `sugar_syrup`; brown sugar and demerara kept as their own ids (different
   flavour notes — Ari's ruling); peels → parent fruit; brands → category;
   flavoured spirits NOT collapsed to base (see 3). ~220 aliases now.
3. **Flavour decomposition (`flavor_forward`).** Composites imply their
   in-the-glass components into recipes at normalize time (citron vodka →
   vodka + lemon; Kahlua → coffee). Base spirits/vermouths/bitters deliberately
   do NOT decompose (gin's lemon botanical is background aroma — decomposing
   would flood every gin drink with phantom lemon). Composite↔own-component
   pairs are excluded from scoring (amaretto+almond co-occur by construction).
4. **Dose gating.** Pours below 0.45 oz mute the decomposition (a splash of
   triple sec is sweetener glue, not an orange statement). Flavour-dense
   syrups (orgeat, grenadine, cremes de cassis/menthe) carry
   `imply_min_oz: 0.0` so they always imply — a Mai-Tai's 1.5 cl of orgeat IS
   an almond statement (Ari's catch). Unknown measures imply by default.
   Muted components are recorded per drink in `recipes_components.json`.
5. **IBA ingestion details that matter:** label-first matching ("Syrup" +
   label "Grenadine" → grenadine; Dry Martini gets dry vermouth), free-text
   "special" entries parsed (Mojito keeps its mint), accent folding
   (Créme de Cassis survives).
6. **Mr. Boston ingestion:** TidyTuesday mirror CSV; de-branding
   ("Old Mr. Boston Dry Gin" → gin), "Juice of a Lemon" reordering. Tripled
   classic support (gin+dry vermouth 9 → 70 recipes).

## Known concerns / watch items

- Category proxies that remain merged (`dubonnet → sweet_vermouth`,
  `lillet`/`cocchi → dry_vermouth`, `bianco → sweet_vermouth`) are now surfaced
  at resolve time (see the de-proxying section below); revisit if they get
  their own entries. (yellow chartreuse / sloe gin / spiced rum already split.)
- Dose thresholds are in absolute oz and US-normed (normalize.py
  `DEFAULT_IMPLY_MIN_OZ = 0.45`). Proportion templates now store fractions,
  so the switch to proportion-of-drink is straightforward once Ari confirms
  the templates — update normalize.py and remove this watch item then.
- Many new entries are PROVISIONAL (flagged in `notes`) — compound profiles
  need a verification pass (Part B-style, with citations).
- Token usage at runtime is a non-issue: the MCP server loads data into
  process memory; the host Claude only ever sees small tool results.

## Adding recipes by hand (the craft corpus)

`data/raw/craft_recipes.json` is the hand-curated corpus: competition winners,
modern classics, Ari's own specs. Append an entry (name / creator / origin /
ingredients with optional oz), rerun the pipeline, done. Hand-curated recipes
win dedupe over every scraped corpus. Seeded with Penicillin, Paper Plane,
Naked & Famous.

**Canon-vs-frontier: DECIDED and implemented.** Corpora are classed in
normalize.py (`SOURCE_CLASS`): canon (IBA, Mr. Boston, TheCocktailDB, the
hand-curated craft file) feeds tradition; frontier (Hotaling & Co craft
dataset, 552 normalized drinks with bartender attribution) feeds
`data/frontier_evidence.json` — pair-level evidence with named examples
("gin + honey, x12, e.g. 'Happiness' by Danny Louie"). The engine does not
read it yet; a future tool should surface it as "rarely done, but..."
support. Frontier unmatched names (house syrups, brands) dominate the
unmatched list now — mine it for aliases gradually, no need to clear it.

## Savoury / taste-axes: DONE (this session)

- Schema: optional `taste` object per entry — axes sweet/sour/bitter/salty/
  umami/fat/funk, 0..1, validated in data.py. New `seasoning` role; salt and
  olive moved to it.
- Engine: `taste_profile(id)` (curated data verbatim, else a conservative
  role-derived prior, flagged `derived`); `balance()` now also returns
  `taste_axes`, a `structure` reading (sour-balanced / bittersweet / savoury /
  ...), `taste_notes` hazards (dairy+acid split risk; savoury with no
  counterweight; salt-accent effect) and `taste_derived_for`. Original keys
  unchanged — additive.
- Data: 10 savoury crossover raws (miso, shio koji, soy sauce, worcestershire,
  fish sauce, celery, butter, mushroom, tamarind, hot sauce) with signature
  compounds (sotolon, methional, pyrazine, sedanolide, capsaicin...) — all
  flagged TODO-verify; celery_bitters composite; taste backfill on ~28 core
  entries (citrus, sugars, amari, dairy).
- Proof it bites: miso+demerara harmony 0.33 via sotolon (novelty 0.33 — the
  moat in action); a Bloody Mary build reads `structure: savoury`; the
  frontier corpus already shows cynar+salt x21, celery_bitters+gin x12.
- 18 tests passing.

## MCP tool exposure: DONE (this session)

- `Pantry.frontier` loads `frontier_evidence.json`; `engine.frontier_support(a,b)`.
- New `frontier_support` MCP tool; `score_pairing` includes frontier evidence
  and provisional flags; `explain_pairing` cites frontier support both for
  novel bridges AND for no-shared-compound contrast pairs (gin+honey: "no
  bridge — but craft bartenders have done it 62x, e.g. 'Happiness' by Danny
  Louie"), and appends a provisional-data caveat.
- Confidence honesty is now systematic: `Ingredient.provisional` (parsed from
  notes), surfaced by resolve/score/suggest/explain — Cobber announces when
  he's guessing instead of relying on the host model to notice (fixes the
  first live test's biggest structural worry).
- INSTRUCTIONS teach the bartender's order (aroma -> layering -> balance),
  relay of taste_notes hazards, and the frontier-support cite-or-say-untried
  step. 21 tests passing.

## Ari's tick-list rulings (this session) + de-proxying

- **Given their own ids** (Ari: genuinely different, not proxies):
  `yellow_chartreuse` (≠ green: milder/sweeter/honeyed), `sloe_gin` (a berry
  liqueur, not gin), `spiced_rum` (lighter than dark + baking spice). Profiles
  are minimal + PROVISIONAL — real aroma data is a research-queue item.
- **Kept as conscious proxies, now surfaced** via `data/proxy_substitutions.json`
  + `resolve_ingredients.substitutions`: Dubonnet→sweet vermouth, Lillet/Cocchi
  →dry vermouth. Cobber announces the swap ("no exact Dubonnet — scoring as
  sweet vermouth"); still merged for co-occurrence. Bianco→sweet vermouth kept.
- Confirmed: cinnamon/ginger/raspberry syrup → their flavour; 151→dark rum;
  garnishes excluded from co-occurrence (Ari: garnish is perfume/enhancement,
  already-muddled mint is a real ingredient); 0.45 oz dose gate is right (a
  5-10 ml splash adds a layer, not flavour). Taste 0-1 values approved.

## OPEN IDEAS Ari raised (design decisions, not yet built)

1. **"Cobber should look things up."** When an ingredient is unknown or only a
   proxy, Ari wants Cobber to find what it is / nearest profile. This collides
   with the core principle (deterministic, no network/LLM at runtime). Proposed
   reconciliation, NOT yet built: (a) build-time research loop (host Claude +
   Ari research a real profile → human-approved entry — the existing pattern);
   (b) a deterministic `nearest_by_profile(id)` tool that returns the closest
   known ingredients by shared compounds, so even a thin/proxy entry can say
   "closest profiles are X, Y"; (c) keep live network/LLM OUT of the server.
   Decide before building.
2. **Chemistry-grounded taste provenance.** Taste axis *numbers* are fine, but
   Ari wants the WHY: bitterness from gentiopicroside/amarogentin (gentian),
   sourness from citric/malic acid, etc. Note a real gap — our compound
   vocabulary is aroma-only; non-volatile taste actives (acids, sugars,
   bitter glycosides) aren't in it. This is the sophisticated form of the
   taste layer and belongs with the Part B verification pass.
3. **Aroma floats.** A 10 ml peated-scotch/absinthe float is low-volume but
   high-aroma. Currently fine — a small *literal* pour still counts the
   ingredient as present; the dose gate only mutes *implied decomposition*.
   If we later model aroma intensity, floats may warrant an override.

## Live test findings (two runs, this session)

- **Run 1 (mezcal+miso, "The Broth Decision"):** chemistry claims all faithful
  to the engine; frontier honesty correct; the savoury/no-acid trap was caught
  by the taste layer and lime pulled in. MISS: provisional flags returned by
  tools but dropped from the final write-up → instructions step 6 now makes
  the data-confidence note a mandatory part of any recipe (patched).
- **Run 2 (grapefruit+pink peppercorn, "Myrcene Season"):** all compound
  claims verified true, including the sharp one (gin carries beta-phellandrene
  as a pink-peppercorn bridge; tequila/mezcal genuinely share nothing).
  Data-confidence note appeared IN the recipe — the step-6 patch works.
  BUG found+fixed: runtime resolver silently coerced "rose water" →
  soda_water at fuzzy cutoff 0.7; cutoff now 0.84 and any fuzzy match is
  disclosed via `fuzzy_matched` (regression-tested in tests/test_server.py).
  Minor fidelity slip: host quoted slightly-off taste-axis numbers and called
  the structure "Negroni-adjacent" where the engine read sour-balanced —
  watch, not yet worth machinery.
- Both drinks await Ari's tasting verdict — first entries for the future
  tasting-feedback loop.

## Roadmap: "what makes Cobber a real mixologist" (agreed direction)

Priority order set with Ari after the two live runs:

1. **Ratios / proportion templates — DONE, pending Ari's naming review.**
   12 templates in `data/proportion_templates.json` (10 k-means + 2 equal-
   parts overlays) from 8,416 cocktailapp recipes. `suggest_template()` in
   engine.py matches any ingredient combination to the nearest template and
   returns per-ingredient fractions; `build_around()` now includes a `template`
   field in every suggestion. Server INSTRUCTIONS updated for step 5. 7 new
   tests, 32 total. **OPEN:** Ari to review benchmark drinks + centroids and
   name each template; until then all names are PROVISIONAL and the host uses
   structural descriptions. Dose-gating-to-proportions deferred (roadmap
   concern) — remove the absolute-oz watch item above once templates are
   confirmed.
2. **Technique mining — DONE.** 9 priority-ordered rules in
   `data/technique_associations.json` from 486 annotated TheCocktailDB+IBA
   recipes. `suggest_technique()` in engine.py, exposed as MCP tool, included
   in every `build_around` suggestion. **OPEN:** Ari to review rule priorities;
   White Russian edge case noted above (dairy→coupe vs rocks).
3. **Tasting-feedback loop.** Started informally: Ari's verdicts on The
   Broth Decision and Myrcene Season are the first entries. Formalize as
   data/tasting_log.json once a few verdicts exist; verdicts should be able
   to adjust pairing confidence. Long-term this is the most defensible asset
   (a model tuned by a working bartender's palate).
4. **Part B verification/citation pass** — parallel track for
   research-flavoured sessions; REQUIRED before any public claim. Includes
   the natives and the taste-provenance idea (bitterness from amarogentin,
   not just "bitter 0.8").
5. **Register dial** (summery↔wintery) — after 1+2, since it weights taste +
   texture + technique.
