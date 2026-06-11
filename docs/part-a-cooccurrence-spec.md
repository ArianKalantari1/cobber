# Part A — cocktail co-occurrence pipeline (spec for GitHub Copilot)

**For Copilot:** implement this **one step at a time**. Each step is a self-contained
script with explicit inputs, outputs, and acceptance criteria. Do not skip ahead. Run
everything **locally** (these scripts hit the internet; the goal is to produce committed
data files). Existing repo: `src/cobber/engine.py` has a `tradition(a, b)` function that
reads `data/tradition.json`. Valid ingredient ids live in `data/ingredients.json` and
`data/composites.json`.

Goal: replace the hand-written `data/tradition.json` with real co-occurrence data
computed from thousands of actual cocktail recipes, using NPMI.

---

## Step 1 — `scripts/fetch_recipes.py`

Fetch the cocktail corpus from TheCocktailDB free API (test key `1`).

- Enumerate all drinks by iterating the search-by-first-letter endpoint for `a`–`z` and
  `0`–`9`:
  `https://www.thecocktaildb.com/api/json/v1/1/search.php?f=<letter>`
- Each response has a `drinks` array; each drink object includes `idDrink`, `strDrink`,
  `strInstructions`, and `strIngredient1`…`strIngredient15` / `strMeasure1`…`strMeasure15`.
- Collect all drinks, **dedupe by `idDrink`**, and save the **full raw objects** (keep
  measures + instructions too — they feed later work) to `data/raw/thecocktaildb.json`.
- Be polite: small delay between requests; handle null/empty responses.

**Acceptance:** `data/raw/thecocktaildb.json` exists with several hundred unique drinks,
each retaining its ingredients, measures, and instructions.

*(Optional later: add the IBA 102 from Wikipedia and/or a Kaggle cocktail CSV into
`data/raw/`. Not required for a first pass — TheCocktailDB already covers the classics.)*

---

## Step 2 — `scripts/normalize.py`

Turn raw drinks into lists of canonical Cobber ingredient ids.

- Load valid ids from `data/ingredients.json` + `data/composites.json`.
- For each drink, pull its non-empty `strIngredientN` values, lowercase + strip whitespace.
- Map each raw name to a Cobber id via an alias map `data/ingredient_aliases.json`
  (create it). Use simple normalisation (lowercase; strip trailing "juice", "fresh",
  "freshly squeezed"; singularise obvious plurals) + exact/fuzzy match to known ids.
- **Anything you can't confidently match: do NOT guess.** Write it to
  `data/unmatched_ingredients.txt` (one per line, with a count of how often it appeared)
  for human review. Leave it out of the normalised output.
- Output `data/recipes_normalized.json`: a list where each item is the de-duplicated list
  of matched Cobber ids for one drink (drop drinks with fewer than 2 matched ids).

**Acceptance:** `recipes_normalized.json` is produced; `ingredient_aliases.json` and
`unmatched_ingredients.txt` exist for review. No raw name is silently coerced to a wrong id.

> **Human checkpoint (Ari):** review `ingredient_aliases.json` and the unmatched list
> before trusting Step 3. Bartender calls (is "simple syrup" → `sugar_syrup`? does a brand
> map to a category?) are yours.

---

## Step 3 — `scripts/compute_npmi.py`

Compute normalised pointwise mutual information per ingredient pair.

- Let `N` = number of normalised recipes. For each ingredient `x`, `count(x)` = number of
  recipes containing it. For each unordered pair, `count(x,y)` = recipes containing both.
- `P(x) = count(x)/N`, `P(x,y) = count(x,y)/N`.
- `PMI = log( P(x,y) / (P(x) * P(y)) )`
- `NPMI = PMI / ( -log( P(x,y) ) )`  → ranges roughly [-1, 1].
- Tradition score = `max(0.0, NPMI)` (negative association → 0, i.e. "not traditional").
- Skip pairs with `count(x,y) == 0`.

**Acceptance:** a known classic pair (e.g. `gin` + `lime` or `rum` + `lime`) scores clearly
positive; an implausible pair scores ~0.

---

## Step 4 — write `data/tradition.json`

Keep the existing shape the engine already reads (`{"pair": ["a","b"], "tradition": <float>}`)
and add two fields:
```json
{ "pair": ["gin", "lime"], "tradition": 0.71, "count": 34, "confidence": "solid" }
```
- `count` = `count(x,y)` (number of recipes the pair appeared in).
- `confidence`: `"solid"` if count ≥ 10, `"moderate"` if 3–9, `"sparse"` if 1–2.
- Sort by tradition descending so the file is human-skimmable.

**Acceptance:** `data/tradition.json` is regenerated from real data, low-support pairs are
flagged `sparse`, and it's valid JSON.

---

## Step 5 — wire the engine + tests (review the diff)

- Ensure `src/cobber/engine.py`'s `tradition(a, b)` reads the new file correctly (the extra
  `count`/`confidence` fields are additive — don't break the existing lookup).
- Confirm the novelty calculation still works and is now empirical (high harmony + low
  tradition = genuinely under-explored).
- Add/adjust tests: a classic pair returns a high tradition score; an unlisted pair returns
  0; the file loads and validates.

**Acceptance:** existing test suite passes; novelty now reflects real co-occurrence.

---

## Notes

- Run Steps 1–4 locally; **commit the `data/` outputs** so the rest works anywhere.
- This pipeline is offline/build-time only — none of it goes inside the running MCP server.
- The compound-profile / chemistry work (Part B) is **not** in this spec — that's a Claude
  job, because it needs web research and uncertainty-flagging Copilot can't do.
