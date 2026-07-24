# Cobber the Mixologist

A small, local MCP server that gives a host Claude a grounded "sense of taste"
for inventing cocktails. Deterministic flavour-chemistry maths over flat JSON
files — no LLM calls, no network, no database at runtime.

**Read these before non-trivial work:**
- `docs/cobber-design-notes.md` — the project's thinking and decision log.
- `docs/handoff.md` — current state, session-by-session, and the next task.

## Core principles (do not violate)

- The server is deterministic and dumb; reasoning lives in the host Claude.
- All data-building is build-time, offline, and human-approved — never inside
  the running server.
- Never silently coerce an ingredient name to a wrong id. Unconfident matches
  go to `data/unmatched_ingredients.txt` for Ari's (bartender) review.
- Uncertain data is flagged, not hidden: provisional entries say so in
  `notes`; tradition rows carry `count` + `confidence`.

## Layout

- `src/cobber/data.py` — loads + validates the JSON into a `Pantry`.
- `src/cobber/engine.py` — pure scoring: harmony (shared-compound Jaccard),
  tradition (lookup), novelty = harmony × (1 − tradition), balance (roles +
  taste axes: structure reading, split-risk/savoury hazards, curated `taste`
  with flagged role-prior fallback).
- `src/cobber/server.py` — FastMCP stdio tools wrapping the engine.
- `data/ingredients.json` / `data/composites.json` — the ingredient world.
  Composites derive their compound profile as the union of their `botanicals`.
  Optional `flavor_forward`: components implied into recipes at normalize time
  (citron vodka → vodka + lemon). Optional `imply_min_oz`: per-entry dose-gate
  override (0.0 = always imply, used for flavour-dense syrups like orgeat).
- `data/tradition.json` — pair scores. `tradition` is **log-scaled prevalence**
  (`log1p(count)/log1p(max_count)`), NOT raw NPMI (NPMI zeroes out ubiquitous
  classics like gin+lime; raw `npmi` is kept per row for transparency).
- `data/recipes_components.json` — per-drink literal/implied/muted components
  (audit trail for the decomposition).
- `data/flavor_communities.json` — diagnostic flavour-family clusters.
- `data/compound_descriptors.json` — compound → odour descriptor words (curated
  from Flavornet, cited per CAS) + taste class for non-volatile tastants
  (acids, sugars, bitter principles, umami, salt — ChemTastesDB). Provisional
  entries flagged. Built by `scripts/fetch_descriptors.py`.
- Ingredients carry an optional `tastants` field (the taste "why" layer): the
  non-volatile compound ids that CAUSE their taste axes (citric_acid → sour,
  sucrose → sweet, quinine → bitter). Kept SEPARATE from aroma `compounds` so
  tastants never enter the harmony Jaccard. Linked by `scripts/link_tastants.py`;
  read by `engine.taste_provenance`.
- `data/flavor_families.json` — the approved 10-family bucket map (every
  descriptor word → exactly one family) + bitter/pungent taste overlay. Read by
  `engine.flavor_wheel`.
- `data/descriptor_harmony.json` — flavour-family co-occurrence ("harmonious
  notes") mined from the recipe corpus with the tradition NPMI machinery. Built
  by `scripts/compute_descriptor_harmony.py`; read by `engine.harmonious_notes`.
- `data/flavor_wheel.html` — self-contained (no network) wheel + harmonious-notes
  visualiser. Built by `scripts/render_flavor_wheel.py`.
- `data/frontier_evidence.json` — pairings from the frontier corpus (craft
  bartenders, competitions) with attribution. Deliberately NOT in tradition:
  validated-novel evidence, not canon.
- `data/raw/craft_recipes.json` — hand-curated recipes (append by hand).

## Build pipeline (offline; outputs are committed)

```
python3 scripts/fetch_recipes.py      # TheCocktailDB -> data/raw/thecocktaildb.json
python3 scripts/fetch_iba.py          # IBA official  -> data/raw/iba.json
python3 scripts/fetch_boston.py       # Mr. Boston    -> data/raw/boston_cocktails.csv
python3 scripts/fetch_hotaling.py     # Hotaling craft -> data/raw/hotaling_cocktails.csv (frontier)
python3 scripts/fetch_cocktailapp.py  # Difford's+Kindred (cocktailApp/CRAN) -> data/raw/cocktailapp_recipes.json
python3 scripts/normalize.py          # -> recipes_normalized/components, aliases, unmatched
python3 scripts/compute_npmi.py       # -> tradition_npmi.json
python3 scripts/write_tradition.py    # -> tradition.json
python3 scripts/flavor_communities.py # -> flavor_communities.json (diagnostic)
python3 scripts/render_graph.py       # -> flavor_graph.html (interactive picture)
```

Sensory-descriptor layer (offline; outputs committed):

```
python3 scripts/fetch_descriptors.py          # -> compound_descriptors.json (Flavornet/ChemTastesDB, cited)
python3 scripts/compute_descriptor_harmony.py # -> descriptor_harmony.json (family co-occurrence, NPMI)
python3 scripts/link_tastants.py              # -> tastants field on ingredients (taste "why" layer)
python3 scripts/render_flavor_wheel.py        # -> flavor_wheel.html (self-contained visualiser)
```

Profile enrichment (optional; FlavorDB2 is CC BY-NC-SA 3.0 — non-commercial use
accepted for this project; run from an unblocked network):

```
python3 scripts/fetch_flavordb.py       # -> data/raw/flavordb_entities.json (entity->molecules + flavor_profile)
python3 scripts/enrich_from_flavordb.py # -> data/profile_enrichment.json (REVIEW proposal; apply by hand)
```

The enrichment proposal is human-approved before touching `ingredients.json`;
unmatched entities and unmappable molecule names are surfaced for review, never
coerced onto an id.

The flavour-family bucket map (`data/flavor_families.json`) is human-approved and
edited by hand; `fetch_descriptors.py` cannot live-scrape in a blocked network,
so it emits a curated, per-compound Flavornet-cited table (refresh path documented
in the script for an unblocked environment).

Canon dedupe priority: hand-curated craft > IBA > Difford's > Mr. Boston > TheCocktailDB.
Frontier corpora (Hotaling, Kindred) feed data/frontier_evidence.json, not tradition.

## Commit discipline

Commit after each discrete sub-task — never batch the whole session into one
end-of-session commit. One logical unit of work = one commit. Examples:

- Research findings documented → commit immediately
- Data file changed (ingredients, composites, tradition) → commit immediately
- New script written → commit immediately
- Docs updated (handoff, design notes) → commit immediately

Tightly coupled changes (e.g. new engine function + its tests + the server tool
that calls it) can go in one commit. Everything else: commit as you go.
Push after each commit so work survives a session limit or crash.

## Working notes

- Tests: `python -m pytest tests/ -q` (needs `pip install -e . pytest`).
- The big data files cost zero tokens at Cobber's runtime (the server loads
  them into Python memory; the host Claude only sees small tool results).
  Don't add a database. When developing here, read slices of the data files
  or use scripts — don't dump whole files into context.
- Don't put the session/model id in commits, code, or docs.
