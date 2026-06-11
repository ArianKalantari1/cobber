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
  tradition (lookup), novelty = harmony × (1 − tradition), balance.
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

Canon dedupe priority: hand-curated craft > IBA > Difford's > Mr. Boston > TheCocktailDB.
Frontier corpora (Hotaling, Kindred) feed data/frontier_evidence.json, not tradition.

## Working notes

- Tests: `python -m pytest tests/ -q` (needs `pip install -e . pytest`).
- The big data files cost zero tokens at Cobber's runtime (the server loads
  them into Python memory; the host Claude only sees small tool results).
  Don't add a database. When developing here, read slices of the data files
  or use scripts — don't dump whole files into context.
- Don't put the session/model id in commits, code, or docs.
