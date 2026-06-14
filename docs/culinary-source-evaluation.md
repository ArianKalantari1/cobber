# Culinary-source evaluation — `the-flavor-network` (Flavor Bible extraction)

*14 June 2026. A real, hands-on evaluation of a candidate source for the
culinary-affinity layer — NOT a summary-read. Files were downloaded and
processed locally, not skimmed.*

## Why this evaluation exists

Ari's standard (correctly) rejected bulk-ingesting UGC recipe corpora
(RecipeNLG/Recipe1M/food.com Kaggle): co-occurrence frequency measures what is
*common*, not what is *good*, and those corpora are amateur-dominated, copy-
amplified, and culturally skewed. The agreed direction is a **smaller, curated,
expert-attributed** source. This evaluates one concrete candidate against that bar.

## Correction to an earlier claim

I previously told Ari "the sandbox network is blocked." That was over-broad.
**`raw.githubusercontent.com` is reachable** (HTTP 200, verified by downloading a
1.9 MB file). Only general hosts (Kaggle, UCI, FlavorDB2) are blocked. So GitHub-
hosted datasets *can* be pulled and processed locally with real tooling.

## What the dataset actually is (verified, not summarized)

Repo: `brege/the-flavor-network` (powers flavorpair.me). MIT-licensed *code*,
© 2023 Wyatt Brege. The pairing network is **constructed by treating *The Flavor
Bible* (Karen Page & Andrew Dornenburg, 2008) as a dataset** (confirmed in the
repo README). A *separate* recipe-search module uses food.com/Kaggle UGC — we do
NOT want that part; the **pairing network is the Flavor Bible part.**

Files (downloaded to /tmp, inspected with Python — not WebFetch, which undercounted
the edges by 10× and self-contradicted on membership):

| file | real size | contents |
|------|-----------|----------|
| `nodes.json` | 1,375 entries | `{id, influence, label}`; influence = degree (garlic 403, apples 257) |
| `edges.json` | **25,684 edges** | `{from, to, weight}`; weight 0–4 |
| `similarity.json` | 9.7 MB | compound-similarity matrix (Ahn-style chemistry — not needed; harmony already does this) |
| `abundance.json` | 12 KB | small auxiliary |

### Weight semantics — VALIDATED against the book's emphasis tiers

Real distribution: weight 1 → 21,814 · weight 2 → 3,242 · weight 3 → 549 ·
weight 4 → 45 (+34 weight-0). This pyramid matches *The Flavor Bible*'s four
typographic emphasis levels (normal → **bold** → **BOLD CAPS** → **starred
"Holy Grail"**). Spot-checks confirm the mapping is real and meaningful:

- `apples + cinnamon` = **4** (a known starred Holy Grail pairing) ✓
- `cherries + almonds` = 3 ✓
- `lemon + thyme` = 2, `pears + ginger` = 2, `coffee + cardamom` = 2 ✓
- `peaches + almonds` = 1 (present, but only standard emphasis — lower than folk intuition)

So `affinity_score = weight / 4` is an **honest ordinal mapping of expert
emphasis** — fundamentally different from (and arguably better than) UGC
co-occurrence frequency. It must be labelled as "expert-emphasis tier," never
conflated with co-occurrence/NPMI.

## Coverage vs Cobber's pantry (165 ids)

73/165 auto-matched on a crude plural alias; more recoverable with manual
aliasing (`passion fruit`, `black currant`, `cilantro`→coriander_leaf, etc.).
The misses break into three honest buckets:

1. **Spirits/liqueurs/bitters** (gin, campari, cynar, triple_sec, …): mostly
   absent — it's a *food* book. (Some do appear: amaretto, armagnac, apricot
   brandy.) Expected; not what this source is for.
2. **Australian natives** (wattleseed, davidson_plum, lemon_myrtle, finger_lime,
   quandong, …): **ALL absent.** The native differentiator gets **zero** from
   this source and needs separate, properly-attributed sourcing
   (CSIRO / Orana / native-food practitioners). Real, unavoidable gap.
3. **Naming/extraction**: recoverable with aliasing, plus some genuine gaps.

## Honest problems (do not gloss)

1. **LICENSING — the blocker.** The edges/nodes are a structured extraction of a
   copyrighted 2008 book. The repo's MIT licence covers Brege's *code*; it cannot
   relicense Page & Dornenburg's creative content — and the pairing matrix *is*
   essentially the book's value. Bulk-vendoring it into Cobber's repo as committed
   data is legally gray-to-infringing and against the project's legitimacy bar.
2. **Extraction is imperfect.** `tomatoes + basil` — a canonical pairing the book
   certainly contains — is **absent** from the edges. Double-space labels
   (`"shellfish  shrimp"`) and duplicate variant nodes (`apples, esp. granny
   smith`) show extraction noise. Needs cleaning.
3. **It tests my own estimates and finds some wanting.** `strawberry + basil`
   (my fabricated 0.82) is **absent** from the expert extraction; `peach +
   almond` (my 0.85) is only weight 1. Direct evidence my hand-estimates were
   overconfident — exactly Ari's concern, now demonstrated.

## Recommendation

**Do not bulk-commit this dataset.** Use it the project's own way:

- Treat the Flavor Bible network as a **build-time REFERENCE / cross-check**, used
  privately to seed and sanity-check a **small, human-approved** culinary file —
  the same pattern as `craft_recipes.json` (hand-curated, Ari-approved). Attribute
  *The Flavor Bible* as the consulted reference; commit Cobber's own curated,
  transformed pairs, not the book's matrix.
- Keep `affinity_score` defined as an **expert-emphasis tier** (weight/4-derived
  where consulted, Ari-adjusted), distinct from tradition's NPMI.
- **Natives** are out of scope for this source — queue a separate native-pairing
  curation task with proper attribution.

This keeps the layer legitimate (no copyright/poisoning exposure), small, and
human-approved — consistent with every principle the project already enforces.

## Status

Nothing from this dataset has been committed to Cobber. Files live only in /tmp
for evaluation. Awaiting Ari's decision on the licensing/curation path before any
build step.
