# Handoff — current state of the co-occurrence work

*Updated 11 June 2026 (evening session, branch `claude/gallant-tesla-n1ad47`).
Supersedes the original Copilot handoff. Read `docs/cobber-design-notes.md`
first for the project's thinking; this file is "where we are and what's next".*

## Status snapshot

- **Corpus:** 1,202 normalized recipes — 75 IBA official + 858 Mr. Boston +
  269 TheCocktailDB (cross-corpus duplicates deduped; IBA recipe wins, then
  Mr. Boston, then TheCocktailDB).
- **Pairs:** 1,672 scored pairs in `data/tradition.json`.
- **Tests:** 12 passing (`python -m pytest tests/ -q`).
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

- **Salt + tomato are tagged role `aromatic` as a placeholder** — wrong, but
  the schema has no salty/umami taste axis yet. Fixed by the next task.
- Savoury staples (Worcestershire, Tabasco) intentionally unmatched until the
  taste-axis layer exists.
- `dubonnet → sweet_vermouth`, `yellow chartreuse → green_chartreuse`,
  `sloe gin → gin`, `lillet → dry_vermouth` are pragmatic category mappings —
  acceptable for co-occurrence, worth revisiting if those ids ever get their
  own entries.
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

## NEXT TASK (Ari's call): savoury / taste-axes

Goal: model what aroma can't — sweet / sour / bitter / salty / umami / fat /
funk — and bring in the culinary crossover ingredients (tomato, Worcestershire,
miso, shio koji…) whose profiles live in food-flavour references (FlavorDB /
FlavorGraph), per design-notes §10: **reference, not bulk-ingest; hand-picked;
cited; confidence-flagged.**

Sketch agreed so far:
- Add a taste-axis structure to the ingredient schema (and fix salt/tomato's
  placeholder roles).
- Hand-curate ~10–15 savoury crossover ingredients with cited compound
  profiles + taste axes.
- Engine: decide how taste axes interact with harmony/balance (likely a
  separate complement/contrast signal feeding `balance`, not a change to
  compound Jaccard).
- These ingredients will be tradition-`sparse` by nature; that is the point —
  high harmony + low tradition is Cobber's moat.
