# Handoff — current state of the co-occurrence work

*Updated 14 June 2026 (evening) — bar-session work: peated Scotch + mezcal smoke
chemistry, body/texture warning, Four Pillars/Frangelico/Licor 43/El Toro/
hazelnut composites, 25 core taste profiles confirmed by Ari. 96 tests.*
*Earlier 14 June 2026 (culinary affinities layer added — Ahn 2011 food-pairing tool).*
*Previously updated 13 June 2026 (proportion templates + technique mining + preference layer + taste backfill + nearest_by_profile/substitution lookup + spice axis + cited-research data fills — all merged to main).
Supersedes the original Copilot handoff. Read `docs/cobber-design-notes.md`
first for the project's thinking; this file is "where we are and what's next".*

## THIS SESSION (14 June 2026, evening bar session) — DONE

Work driven by Ari testing Cobber live behind a real bar:

- **Body/texture warning in `balance()`** — live finding: a bourbon+coffee+
  cherry drink drank "too flat." Added `_BODY_CONTRIBUTORS` (fat emulsion /
  protein foam / dissolved-solids viscosity) and a `taste_notes` warning when
  fat < 0.3 and no contributor present. 5 tests.
- **Peated Scotch** — `peat_smoke` raw (guaiacol, 4-ethyl/4-vinylguaiacol,
  p-cresol, phenol; cited to Islay GC-MS) + `peated_scotch` composite. Distinct
  from generic `scotch`; bridges to bourbon/rye via barrel vanillin (the
  Penicillin-float join).
- **Mezcal smoke** — `wood_smoke` raw (hardwood pit-roast phenols incl.
  syringol + 4-methylguaiacol, the hardwood-lignin markers peat lacks) folded
  into `mezcal`. mezcal+peated_scotch harmony 0.33 (shared guaiacol family);
  mezcal+tequila drops to 0.17. 3 tests. Espadín is the agave variety; smoke is
  a production-style (pit-roast) variable, not a varietal trait — modelled as
  the category smoky baseline.
- **Bar composites** — `four_pillars_gin` (8 botanicals incl. 4 AU natives),
  `frangelico` (+ `hazelnut` raw: filbertone/benzaldehyde/pyrazine), `licor_43`
  (vanilla-citrus-cinnamon), `el_toro_cafe_tequila` (agave+coffee+vanilla).
  Build-time brand aliases added.
- **Taste profiles confirmed (Ari sign-off)** — the 25 immediately-learnable
  core profiles reviewed behind the bar; 24 kept, amaretto bitter 0.25→0.15.
  Now bartender-verified, not estimates. The 33 provisional profiles are laid
  out for tick-through in `docs/ari-approval-sheet.md`.
- **Pisco deep-dive** — extensive pisco pairing work (chemistry: beta-
  damascenone + methyl-anthranilate). Honey substitutes surfaced (drambuie =
  chemically identical, H=1.0; agave/maple via furaneol; cassis/grenadine via
  beta-damascenone). Six winter pisco specs dialled in — pending Ari's approval
  to add to the craft corpus (approval-sheet §E).
- **`docs/ari-approval-sheet.md`** — single tick-through doc for all pending
  Ari decisions (33 taste values, 12 template names, 10 technique rules,
  culinary draft, winter recipes).

**Note on runtime brand resolution:** build-time aliases (Laphroaig→peated_scotch
etc.) do NOT feed the runtime resolver (`_resolve_one` uses id/display-name/
fuzzy only). Typing "Laphroaig" at runtime still returns unknown. Wiring the
alias file into the resolver is a banked task awaiting Ari's sign-off (touches
the resolve seam).

## Culinary affinities layer: DONE (14 June 2026)

- **Data:** `data/culinary_pairs.json` — 105 PROVISIONAL pairs (model-estimate
  scores, honest labelling: `"status": "PROVISIONAL — UNVERIFIED ESTIMATES"`).
  The underlying source evaluation confirmed these estimates have real errors
  (strawberry+basil and peach+almond overscored vs. Flavor Bible expert data).
  **Not yet promoted to curated status — awaiting the reference-and-curate pipeline.**
- **Architecture decision (14 June 2026 — Ari):** exposed as an MCP tool, NOT
  silent background data, so the host Claude can reason about whether a food
  pairing translates to a cocktail. Transparency wins over token efficiency.
- **Engine:** `engine.culinary_affinities(ingredient_id, n)` — looks up the
  culinary table and enriches each hit with `shared_compounds` + `harmony`
  when a compound bridge exists in Cobber's aroma DB. When absent, the pairing
  is purely chef-empirical. This distinction is surfaced explicitly.
- **Tool:** `get_culinary_affinities(ingredient_id, n=10)` — MCP tool. Returns
  affinities sorted by score. Honest empty list (+ note) when unmapped.
- **Tests:** 88 total. Data validator: 6 tests (malformed pair, unknown id,
  out-of-range score, self-pair, clean row, real-file clean-and-unique).
  Server: 8 tests. Data integrity hardened: duplicate-collapse bug fixed;
  conflicting-score detection; dead-reference validation.
- **Distinct from tradition.json and frontier_evidence.json:** tradition =
  cocktail history; frontier = craft bartenders; culinary = food chefs.

### Source evaluation: brege/the-flavor-network (Flavor Bible extraction)

- Hands-on evaluation done 14 June 2026. `docs/culinary-source-evaluation.md`
  is the full report. Key findings:
  - 25,684 edges (not ~2,700 as WebFetch claimed — WebFetch summary was 10×
    wrong; Python processing of the downloaded file was used instead).
  - Weight semantics validated: 4 tiers match Flavor Bible typographic emphasis
    (weight 4 = starred Holy Grail pairing; spot-checks confirmed).
  - Coverage: 65/96 Cobber ids map to a FB node (hand-verified alias table).
    ALL 15 Australian natives are absent (Flavor Bible is a US food book).
  - Copyright blocker: book content © Page & Dornenburg 2008; MIT license covers
    code only; bulk-committing the edge matrix would be legally infringing.
  - Ari's decision: **reference-and-curate** — use FB network privately at
    build time; Ari approves every promoted pair; no book matrix committed.

### Reference-and-curate pipeline: DONE (14 June 2026)

- **Script:** `scripts/build_culinary_pairs.py` — downloads nodes.json +
  edges.json from `brege/the-flavor-network` at build time, maps Cobber ids
  to FB nodes via the alias table, extracts pairs where both endpoints are
  Cobber-known, writes `data/culinary_draft.json` for Ari's approval.
- **Draft results:** 584 unique pairs — 2 holy-grail (weight 4), 32 highly
  recommended (weight 3), 140 recommended (weight 2), 409 standard (weight 1).
- **`data/culinary_draft.json`** is gitignored (Flavor Bible derivative; must
  not be committed). Each pair has `fb_weight`, `affinity_score = weight/4`,
  `fb_nodes` (traceability), `source`, and `ari_approved: null`.

### Next step for culinary data

1. **Ari reviews `data/culinary_draft.json`** (generated by running
   `python3 scripts/build_culinary_pairs.py`). For each pair: set
   `ari_approved: true` and add a `note` if desired; skip/delete unwanted pairs.
2. **Promote accepted pairs** into `data/culinary_pairs.json` by hand,
   replacing the current provisional model-estimate entries.
3. **Australian natives:** separate task — source pairings from CSIRO,
   Orana Foundation, or named native-food practitioners. Queue explicitly;
   no placeholder data.

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
- **Technique rules:** 10 priority-ordered rules in
  `data/technique_associations.json` (PROVISIONAL — Ari to review).
- **Preference layer:** per-install local taste profile
  (`src/cobber/preferences.py` → `~/.cobber/preferences.json`); learns only
  through verified taste-curated ingredients (25 learnable now after taste
  backfill; 33 more once Ari de-provisions composites.json).
- **Tests:** 96 passing (`python -m pytest tests/ -q`). *(was 74 at the 13 June
  snapshot; +22 across culinary layer, body warning, peat/mezcal smoke.)*
- **Spice axis (13 June 2026):** 8th palate axis added — chemesthetic heat
  (capsaicin/gingerol), grounded in the heat compound the entry already carries.
  `balance()` flags it as a hazard note; kept OUT of the structure reading. On
  ginger 0.8, hot_sauce 0.9, ginger_beer 0.7, ginger_ale 0.3, black_pepper 0.5.
- **Cited-research data fills (13 June 2026):** cranberry (de-provisioned, GC-O
  study), tonic_water (limonene + quinine-is-taste-not-aroma correction),
  ginger_ale/ginger_beer split into ginger-derived composites, dark sugars
  differentiated (demerara sotolon-alone confirmed; brown/maple gain cited
  layers; kokuto added with its koku gap documented). Web-researched with
  citations in each entry's `source`; see design-notes §15.
- **Flavour families:** 22 diagnostic clusters in `data/flavor_communities.json`
  that read like a bar menu (daiquiri/mojito family, martini family,
  after-dinner cream-coffee family, tiki, mulled-wine spices…).
- **Taste-axis backfill (13 June 2026):** 45 composites added PROVISIONAL taste
  profiles in `data/composites.json`. 25 composites are immediately learnable by
  the preference layer; 33 more learnable after Ari de-provisions PROVISIONAL notes.

## Per-install taste-preference layer: DONE (13 June 2026)

- **Ari's rulings that shaped it:** (1) NO public knowledge pooling — spam /
  poisoning risk, deliberately rejected; (2) instead, each MCP install keeps
  its own local preference document and Cobber learns THAT user's palate;
  (3) Cobber must proactively ask for feedback after handing over a recipe
  ("make it and tell me what you liked / what could be better").
- **Storage:** `~/.cobber/preferences.json` (env-override `COBBER_PREFS_PATH`).
  This is the ONLY thing the server ever writes; the shared scoring data
  (ingredients/tradition/templates/technique) stays strictly read-only at
  runtime, preserving the build-time/human-approved principle. The raw
  feedback log is the source of truth; the derived profile is recomputed from
  it on every write (order-independent, picks up data-file improvements).
- **The quarantine rule (clean-data guard):** a verdict only teaches the
  profile through ingredients that are BOTH non-provisional AND taste-curated.
  Everything else is recorded but quarantined ("unattributed") — dirty data is
  inert, not corrosive. This is what lets the preference layer ship before the
  full Part B clean: bad data *can't* poison a palate model that refuses to
  learn from it. Only 15 ingredients are learnable today — taste backfill on
  high-frequency entries (gin 2,147 recipes, no curated taste!) is the
  highest-leverage cleanup and a pending proposal for Ari.
- **Matching:** `personal_fit` = 0.5 + 0.35·cosine(palate vector, drink taste
  vector) + 0.15·direct ingredient affinity, clipped to [0,1]. Cosine (not
  dot product) so a one-note drink can't max a single liked axis and outrank
  a drink matching the user's whole balance — caught by test: sugar syrup was
  outranking a Negroni for a Negroni lover under the dot product.
- **Cold start honesty:** < 3 verdicts → `personal_fit` returns None; fully
  uncurated combinations → None. No fake numbers.
- **Tools:** `record_tasting_feedback` (free-text ingredients resolved via
  the same resolver; unresolved names stored, never coerced) and
  `get_taste_profile`. `suggest_from_pantry` attaches `personal_fit` per
  suggestion once 3+ verdicts exist. INSTRUCTIONS step 7 teaches the
  ask-for-feedback loop and the two honesty rules (announce quarantined
  ingredients; never claim to know a palate from a handful of verdicts).

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
- **RESOLVED — cream-without-acid ambiguity (deliberately NOT over-engineered).**
  The corpus splits this family almost evenly: shake 31% / build 28% / blend 15%
  / layer 15% / stir 11% — i.e. no signal. Two real sub-families share the same
  ingredient signature: built sippers (White Russian, Sombrero → build/rocks)
  and shaken dessert cocktails (Brandy Alexander, Grasshopper → shake/up).
  Decision (Ari): the `dairy_build` rule defaults to build/rocks (Ari's White
  Russian call) and carries an `ambiguous: true` flag + `ambiguity_note` that
  tells the host to shake-and-serve-up for dessert cocktails. We deliberately did
  NOT build a coffee-vs-crème-liqueur heuristic — when the data has no signal,
  inventing a deterministic rule fakes confidence the data doesn't support (same
  failure mode as a fabricated recipe). The host already knows the difference;
  the flag just makes the engine honest about it. One flag, not a taxonomy.
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

1. **"Cobber should look things up." — DONE (13 June 2026, the deterministic
   half).** Ari's decision: build the deterministic `nearest_by_profile` now;
   defer brand-level data (Four Pillars etc.) to a future research-agent pass —
   it's a data-gathering job, not architecture. Built:
   - `engine.nearest_by_profile(id, n, candidates)` — closest known ingredients
     by shared-compound Jaccard; honest `[]` for unknown/profile-less ids (no
     fabricated neighbour). MCP tool `nearest_by_profile`.
   - `engine.suggest_substitution(id, pantry, n)` — role-faithful pantry
     stand-ins (a spirit for a spirit), ranked by chemistry; lime_vodka (harmony
     1.0 with lime, but a spirit) is correctly NOT offered for lime. MCP tool
     `suggest_substitution`. INSTRUCTIONS step 1 wires both into the resolve flow.
   - `build_around` now carries `flavour_blanks` per suggestion: ingredients
     with no aroma AND no taste (vodka, soda, tonic) whose zero harmony is a
     blank canvas, not a clash. Data-driven (`not compounds and not taste`), so
     sugar syrup is not flagged. INSTRUCTIONS step 3 relays it.
   The no-network/no-LLM-at-runtime principle held — pure compound maths.
   **Still open:** the build-time research loop for real brand/native profiles
   (host Claude + Ari, or a research agent) — the lookup tools degrade gracefully
   in the meantime instead of dead-ending. (Original reconciliation options were:
   (a) build-time research loop; (b) `nearest_by_profile`; (c) keep network out
   of the server — we shipped (b)+(c), banked (a).)
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

## Taste-axis backfill: DONE (13 June 2026)

**The gap:** 15 learnable ingredients in the preference layer → can't learn from gin
(2,147 recipes), bourbon, tequila, most liqueurs.

**Research findings (deep compound-database investigation):**
- FlavorDB / FlavorGraph catalog AROMA compounds only (terpenes, esters). These are NOT
  taste-active → cannot fill sweet/sour/bitter axes for spirits. Gin's distinctive flavor
  is linalool/pinene — aroma, not taste.
- FooDB (CC BY-NC) has concentrations but only ~5.3% of entries are quantified; distilled
  spirits are under-curated. Getting "gin has compound X at Y mg/L" for taste compounds
  is not feasible from FooDB alone.
- ChemTastesDB (CC BY 4.0, Zenodo) maps 4,075 compounds → taste class (bitter 1,615,
  sweet 1,313, umami 220, sour 49, salty 16). Download at zenodo.org/records/15051366.
- The correct scientific method is Dose-Over-Threshold: DoT = concentration/threshold;
  compounds with DoT ≥ 1 are taste-active; sum DoT per taste class; log1p-normalize.
- **Critical conclusion:** for cocktail spirits and proprietary liqueurs, bartender expert
  knowledge IS the right primary method. Compound databases can confirm WHY (gentian →
  gentiopicroside → bitter class in ChemTastesDB) but cannot replace the calibrated
  0..1 value. See `docs/cobber-design-notes.md §13` for the full research record.

**What was built:**
- 45 composites in `data/composites.json` got PROVISIONAL taste profiles calibrated
  from bartender knowledge (the same methodology already used for campari, vermouth, etc.)
- **Immediately learnable** (no PROVISIONAL in notes — 25 composites):
  gin, white_rum, dark_rum, tequila, mezcal, bourbon, rye_whiskey, brandy, triple_sec,
  cointreau, sweet_vermouth, dry_vermouth, campari, aperol, st_germain, maraschino,
  amaretto, coffee_liqueur, green_chartreuse, limoncello, angostura_bitters,
  peychauds_bitters, orange_bitters, grenadine, whole_egg
- **Learnable after Ari de-provisions** (remove "PROVISIONAL" from notes field — 33 more):
  scotch, irish_whiskey, cachaca, irish_cream, peach_schnapps, apricot_brandy, sambuca,
  absinthe, benedictine, galliano, blue_curacao, creme_de_cacao, creme_de_cassis,
  coconut_liqueur, raspberry_liqueur, amaro_montenegro, creme_de_menthe, cherry_liqueur,
  pisco, drambuie, calvados, sherry, anisette, cynar, fernet, averna, falernum,
  ginger_liqueur, allspice_dram, celery_bitters, yellow_chartreuse, sloe_gin, spiced_rum
- Vodka and flavored spirits intentionally skipped: vodka is neutral; flavored variants
  decompose to base + flavor_forward, so their taste comes from implied components.
- **Ari's action:** review the 25 immediately-learnable values and the 33 provisional ones;
  adjust values where your palate disagrees; remove "PROVISIONAL" from notes for entries
  you're satisfied with (the learner picks them up automatically on next feedback).

**Future pipeline** (when Part B starts):
  `scripts/verify_taste_axes.py` → download ChemTastesDB + optionally FooDB → DoT
  aggregation → compare computed vs curated → flag discrepancies for Ari review.

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
2. **Technique mining — DONE.** 10 priority-ordered rules in
   `data/technique_associations.json` from 486 annotated TheCocktailDB+IBA
   recipes. `suggest_technique()` in engine.py, exposed as MCP tool, included
   in every `build_around` suggestion. **OPEN:** Ari to review rule priorities
   and rationale text.
3. **Tasting-feedback loop — DONE as the per-install preference layer**
   (see section above). Ari ruled OUT public knowledge pooling; the layer is
   personal per install. **Remaining (Ari-side):** the curated global
   `data/tasting_log.json` — Ari's own verdicts (The Broth Decision, Myrcene
   Season pending) promoted by hand to adjust *pairing confidence* in the
   shared data. That stays a build-time, human-approved file, separate from
   the per-user layer. **Bottleneck:** taste-axis backfill (only 15
   ingredients are learnable; gin appears in 2,147 recipes with no curated
   taste) — top-15 proposal drafted, awaiting Ari's values.
4. **Part B verification/citation pass** — parallel track for
   research-flavoured sessions; REQUIRED before any public claim. Includes
   the natives and the taste-provenance idea (bitterness from amarogentin,
   not just "bitter 0.8"). **Candidate public sources for the taste gap**
   (from model memory, 13 June 2026 — VERIFY existence + license before any
   ingest; per project principle, reference-only, never bulk-ingested):
   ChemTastesDB (~2,900 molecules with taste classes; best for provenance),
   BitterDB (bitter compounds + receptors), FooDB (food constituents WITH
   concentrations — closest to ingredient-level), FlavorDB2 (already noted in
   design docs as reference-only), Good Scents Company (per-compound
   organoleptic notes; licensing murky — cite-only), VCF (authoritative but
   paid — out). Structural catch: these are compound-level; our `taste` axes
   are ingredient-level palate intensities, so numbers come from Ari's
   bartender judgment spot-checked against the DBs, and the DBs supply the
   WHY (provenance) at Part B.
5. **Register dial** (summery↔wintery) — after 1+2, since it weights taste +
   texture + technique.
6. **Agent-loop refinement search (far future — Ari's idea, banked).**
   Inspired by a hackathon-winning protein-compound architecture: an agent
   loop that iterates candidate combinations with minimal differences,
   re-scoring each pass, until it converges on something genuinely new
   rather than stopping at the first plausible answer. Would sit ABOVE the
   deterministic engine (the host loops; the server stays dumb), so it does
   not violate the no-LLM-at-runtime principle. Not designed yet; revisit
   after the preference layer has real usage data.
