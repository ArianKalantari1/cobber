# Handoff — current state of the co-occurrence work

*Updated 11 June 2026 (evening session, branch `claude/gallant-tesla-n1ad47`).
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
- **Tests:** 18 passing (`python -m pytest tests/ -q`).
- **Flavour families:** 22 diagnostic clusters in `data/flavor_communities.json`
  that read like a bar menu (daiquiri/mojito family, martini family,
  after-dinner cream-coffee family, tiki, mulled-wine spices…).

## Decisions made this session (and why)

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
- Dose thresholds are in absolute oz and US-normed. When ratio/strength
  modelling lands, switch to proportion-of-drink (pour-culture independent —
  Ari notes AU bars cap ~60 ml spirit per drink, US guides pour bigger).
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

## Next candidates (Ari to choose)

1. **Verification / citation pass (Part B)** — the provisional compound
   profiles (all flagged in `notes`) verified against FlavorDB/literature
   with citations; includes the native ingredients before any public claim.
2. **Live test** — branch is ready for Claude Desktop (mandarin-winter brief
   + a savoury brief); the run report drives the next reprioritisation.
3. **Ratios/proportions** — the cocktailApp extract carries per-drink
   proportions (unused so far); proportion-based dose gating (pour-culture
   independent) and a first strength/dilution model.
4. **Register dial** (summery↔wintery) per design notes §4.
