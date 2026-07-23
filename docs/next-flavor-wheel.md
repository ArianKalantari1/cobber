# NEXT PROJECT — the flavour-wheel / descriptor-harmony layer

*Banked 14 June 2026 (evening). This is the next build. Read
`CLAUDE.md`, `docs/handoff.md`, and `docs/cobber-design-notes.md` first.*

## The gap (why we're building this)

Cobber scores **shared aroma compounds** (the Ahn 2011 flavour-network method):
ingredient → compounds → Jaccard overlap = `harmony`. That's the *chemistry*
layer and it's solid.

What Cobber is **missing** is the **sensory-descriptor layer** — the thing that
makes sites like Flavonomics feel like a gold mine:

1. **Flavour wheels** — per ingredient, a profile across flavour families
   (Sweet, Acidic, Floral, Vegetal, Spice, Woody, Earthy, Maillard, Carnal…)
   with sub-notes (sugary, honeyed, vanillic, brambly, raisiny, tomatoey…).
2. **"Harmonious notes"** — which *descriptor notes* complement each other
   (sugary↔vanillic, berry↔milky, raisiny↔limonene). This is the
   **complementary** layer, distinct from Cobber's **shared-compound** layer.

Both are **reproducible from free data** — Flavonomics is a *refinery* built on
the same open sources, not a unique dataset. Do NOT scrape Flavonomics /
Difford's / any commercial site (ToS + copyright + it contradicts the
project's own reference-and-curate rule). Go upstream.

## The method (how a wheel is actually made)

> **ingredient → its compounds → each compound's descriptors → bucket into
> flavour families.**

Cobber already has arrow 1 (ingredient→compounds). The missing arrow is
**compound → descriptor** (vanillin→"vanilla/sweet/creamy";
furaneol→"caramel/strawberry"; beta-damascenone→"rose/berry/apple/honey").
That lookup table is free.

Once you have it you get both deliverables for free:
- **Wheel** = aggregate an ingredient's compound-descriptors into families.
- **Harmonious notes** = (a) shared-descriptor scoring (same logic as harmony
  but at descriptor level), and/or (b) descriptor-level NPMI over Cobber's own
  recipe corpus (`tradition.json` machinery, run on descriptors).

## Free, verified-or-verify sources (NO payment / NO approval for the core)

- **Flavornet** (flavornet.org) — compound→odour descriptors. Small (~700) but
  it's exactly the descriptor data. **Base layer.**
- **FooDB** (foodb.ca) — bulk food→constituents dumps, free. Enriches compound
  profiles → richer wheels. (License noted CC BY-NC in design notes — VERIFY.)
- **FlavorDB / FlavorDB2** (cosylab.iiitd.edu.in) — 25k+ molecules aggregating
  FooDB/Flavornet/BitterDB/SuperSweet, incl. descriptors. **VERIFY access/terms.**
- **ChemTastesDB** (Zenodo, CC BY 4.0) — taste classes (sweet/sour/bitter axes).
- **FlavorGraph** (Nature Sci Reports 2020, GitHub) — food-chemical graph +
  pairing recs; closest open analogue to Flavonomics.
- **Ahn 2011 flavour network** — the shared-compound method Cobber already is.
- Good Scents = free-to-view but licensing murky → **cite-only, no bulk scrape**.
  VCF = the only genuinely paid one → skip.

**Per project rule: verify each license before ingest; cite in every entry;
human-approved before promotion (same as the Flavor Bible reference-and-curate
pipeline in `scripts/build_culinary_pairs.py`).**

## Deliverables for the next build

1. `scripts/fetch_descriptors.py` — pull compound→descriptor (Flavornet base,
   supplement where licensing allows), mirroring the existing fetch/normalize
   pattern. Cache raw; write a curated `data/compound_descriptors.json`.
2. **Enrich compound profiles** from FooDB/FlavorDB so ingredients carry more
   than the current 3–5 hand-entered compounds → richer, truer wheels.
3. `engine.flavor_wheel(ingredient_id)` — aggregates its compounds' descriptors
   into the ~10 flavour families; returns family scores + top sub-notes.
   Honest empty/partial when compounds/descriptors are unknown (no fabrication).
4. **Descriptor-level harmony** — extend harmony/NPMI to descriptors →
   a "harmonious notes" table generated from Cobber's OWN recipe corpus.
5. **Local HTML visualisation** — a self-contained page (runs on a local
   machine, no server) rendering the wheels + the pairing/harmony view for any
   ingredient. Read slices of the data files; don't dump whole files.
6. Tests + cited sources throughout. Update `docs/handoff.md`.

## Flavour-family bucket list (starting point — Ari to eyeball)

Sweet · Acidic/Sour · Floral · Fruity(Berry/Stone/Citrus/Tropical) · Green/Vegetal
· Herbal · Spice · Woody · Earthy/Fungal · Maillard/Roasted · Dairy/Lactic ·
Nutty · Umami/Savoury · Smoky. (Flavonomics used ~10; we can pick our own set —
map each descriptor to exactly one family.)

---

## Also banked this session (bar-side R&D, operational — not core engine)

A pisco + strawberry program for a French/European restaurant (using up a
6-bottle pisco over-order). Not committed as engine data; captured here so it
isn't lost:

- **Honey-thyme pisco** (infusion): per 700 ml — 75 g honey (50 subtle / 100
  bold), 8–10 thyme sprigs. Warm to ~50 °C to dissolve honey (never >55), cool,
  cold-steep thyme 1–2 hr (tastes bitter if over-steeped), fine-strain. Honeycomb
  variant adds a beeswax fat-wash silk. Infused honey = aroma + the pisco↔fruit
  bridge, NOT much sweetness/body — confit does the sweetening.
- **Balsamic roasted-strawberry confit**: roast strawberries + pinch salt + a
  little (brown) sugar + a few drops balsamic, 180 °C 25–30 min. For batching,
  let down / strain to a syrup; keeps ~2–3 wk fridge (jam form keeps longer).
  **20 ml is the minimum for the strawberry to read.** The balsamic adds acid →
  **reduce the lemon** in builds (two-part acid: citric + acetic).
- **Strawberry milk-punch CORDIAL** (the standout idea — solves flavour +
  no-foam texture + easy service at once): warm whole milk + honey + thyme;
  combine with roasted-and-blended strawberry purée + lemon + pinch salt; the
  acid curdles the milk; rest, strain through the curds → clarified, silky,
  concentrated cordial. Dose into full-strength pisco → loud strawberry + silky
  body, **no egg/foam needed**. Roast (don't blend fresh) to concentrate; a
  splash of fresh berry at the end keeps a bright top note.
- **No-foam coupe trio** (Ari dislikes aquafaba texture): Strawberry-Amaretto,
  Strawberry-Frangelico, Strawberry-Oloroso — each pisco 45–50 · confit 20 ·
  modifier 12 · lemon 12–15. Nut pairings are complementary (not shared-compound).
- **Easy-serve batched**: Strawberry El Capitán (pisco + sweet vermouth/Lillet +
  confit + Peychaud's; all shelf-stable → batch indefinitely, pour over ice, twist).
- Others: shake-and-dump strawberry mojito; prosecco-topped spritz; cobbler;
  stirred low-ABV aperitivo; highball.
- **Peychaud's** is the chemically-matched bitters (shares beta-damascenone with
  both pisco and strawberry); Angostura/orange work by contrast.

Full Bopp & Tone spring menu (different venue) is in
`docs/menus/ember-and-after.html`.
