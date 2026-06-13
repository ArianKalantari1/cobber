# Cobber the Mixologist — design notes & decision log

*Captured 11 June 2026. Living document — update as decisions change. This is the
single place that holds the project's thinking, so future Claude Code / Fable sessions
have full context without re-deriving it.*

---

## 1. What Cobber is

A small, local MCP server that gives any Claude a grounded "sense of taste" for
inventing cocktails. A user says what they have on their shelf, nominates 2–3 ingredients
to build around, and Claude — using Cobber's tools — proposes chemically plausible,
deliberately *uncommon* drinks, with an optional Australian-native or culinary twist.
Display name: **Cobber the Mixologist**; call him **Cobber**. Technical id: `cobber`.
Repo: github.com/ArianKalantari1/cobber.

## 2. Core design principle (do not violate)

**The server is deterministic and dumb; the reasoning lives in the host Claude.** The
server does flavour-chemistry maths over flat data files — no LLM calls, no network,
no database. The host Claude interprets the brief, picks a direction, and writes the
recipe and name. This is what makes it free per drink, fast, trustworthy, and not just
a wrapper. Keep the chemistry in code; keep the creativity in the model. All research
and data-building is *build-time* and human-approved, never inside the running server.

## 3. The flavour-development process (the heart of how Cobber should reason)

Learned from Ari's bar manager — this is the *order* a real mixologist works, and
Cobber's host-Claude reasoning should follow it rather than dumping a scored list:

1. **Aroma first — the sniff test.** Do the aromas belong together? This is the gate.
   → Cobber's shared-compound harmony score *is* the sniff test, encoded.
2. **Layering.** Once the aromas agree, what's missing? Add complexity — a bitter, a
   spice, a modifier, an amaro. → composites / modifiers in the data.
3. **Texture / mouthfeel.** Refreshing (light, floral, vibrant) ↔ rich (dense, real
   mouthfeel). A deliberate target, not an accident. → the texture axis (see §4).
4. **Balance — bitterness vs tartness.** The aperitivo decision: bitter, or sour/tart?
   Chosen on purpose. → the taste axes (bitter, sour).

This sequence belongs in the server's `instructions` string so Cobber proposes drinks
the way a bartender builds them.

## 4. The dimensions Cobber models (and should)

- **Aroma harmony** — Jaccard over shared flavour compounds. *Built (V1).* The sniff
  test in code.
- **Tradition / co-occurrence** — how classic a pairing is. *V1: hand-curated table.
  V2: data-derived NPMI from real cocktail recipes (FlavorGraph's method, bar-scale).*
- **Novelty** = harmony × (1 − tradition). Chemically sound but rarely done. *The
  defensible core — the thing vanilla Claude is structurally bad at.*
- **Taste axes** — sweet / sour / bitter / salty / umami / fat / funk / **spice**. *V2.*
  Captures taste/structure that aroma can't (e.g. umami from miso/shio koji). Strictly
  these are *palate* axes, not pure gustation: `fat` is mouthfeel, `funk` is aroma-led,
  and `spice` (added 13 June 2026) is chemesthesis — the TRPV1 heat of capsaicin/gingerol,
  a burn rather than a flavour, which `balance()` flags as a hazard note but keeps OUT of
  the structure reading (heat is parallel to the sweet/sour/bitter/savoury shapes, not one
  of them). Future mouthfeel axes (body, astringency, cooling) belong in this same set —
  see §14.
- **Texture / mouthfeel** — refreshing ↔ rich; driven by carbonation, dissolved solids
  (sugar, pectin), body, dilution, temperature. *Needs first-class treatment; emerges
  from technique + interaction, not static ingredient properties.* (Shrub example: an
  acidified, carbonated base feels richer than plain soda water — dissolved solids raise
  viscosity, and acid changes how the carbonation is perceived.)
- **Register** — summery ↔ wintery dial. *Mostly set by the supporting cast + technique,
  not the hero ingredient* (same mandarin → gimlet = summer; amaro build = winter).
  Decomposes into grounded properties: bitterness, warming spice, barrel-aged spirits,
  darker sweeteners, more body / less dilution. Implement as a weighting over the taste
  + texture axes, not a vibe. Correlates with texture but is distinct.
- **Technique / preparation** — shaken/stirred/carbonated/fat-washed/clarified, dilution,
  temperature, aeration. *Biggest conceptual gap — not yet modelled. Same ingredients,
  different technique = different drink.*
- **Ratios / dilution / strength** — the grams of sugar vs acid vs alcohol vs water that
  actually make a drink balanced. *Not yet modelled; host Claude writes ratios freehand.*

## 5. Data model (V1 = curated seed, ~70–88 entries)

- `ingredients.json` — raw ingredients with their own `compounds`, `descriptors`,
  `role`, `is_native`, `season` (reserved/unused), `notes`, `source`.
- `composites.json` — spirits/liqueurs/bitters carrying a `botanicals` bill; their
  compound profile is the *union* of the botanicals'. Decomposition, not scraping.
- `tradition.json` — co-occurrence table (V1 curated → V2 NPMI-derived).
- **`confidence`** field on every entry (V2): `verified` / `approximate` / `provisional`.
  More honest than a binary flag, and surfaced to the user — "Cobber tells you when he's
  guessing." Taste axes + texture to be added to the schema.

## 6. Why Cobber over vanilla Claude (the moat — protect these, don't pitch the rest)

One line: *vanilla Claude tells you what's already been done; Cobber finds what hasn't
been done but should work, and proves why with real chemistry.*
- **Novelty (strongest).** LLMs regress to the common; Cobber is engineered for the
  uncommon-but-valid. Ari's ChatGPT test confirmed it only returns the already-done.
- **Grounded, verifiable, consistent rationale** + confidence honesty — vs fluent
  confabulation stated with even confidence whether right or guessing.
- **Curated data Claude lacks well** — vetted natives, culinary/umami crossovers, taste
  axes tuned by a real bartender.
- **NOT a differentiator:** the recipe writing/naming — that's the same host Claude in
  both cases. Don't pitch it.

## 7. Status (V1, built, pushed, connected & tested)

Full MCP server in Python (FastMCP, stdio). 88 seed entries, derived composite profiles,
pure engine (profile/harmony/tradition/novelty/balance/build_around), 5 tools
(resolve_ingredients, score_pairing, suggest_from_pantry, explain_pairing,
get_native_twist), 8 passing tests, README, verified MCP handshake. Uncertain entries
honestly flagged `TODO: verify`. **Installed locally and connected to Claude Desktop
(console-script command at `.venv/bin/cobber`), and run live for the first time on
11 June 2026.**

## 7a. First live test — what the real run revealed (11 June 2026)

First drink out of Cobber: **The Funky Cobber** — a Montenegro sour with a gin backbone,
grapefruit bridge, Peychaud's marbled across the foam, plus a lemon aspen native-twist
option. A good drink. But the run was an honest mirror, and it reorders the priorities
below what we'd guessed before connecting him. What it exposed, in order of how much it
threatens the value proposition:

- **Coverage holes silently degrade the grounding.** Amaro Montenegro wasn't in the data,
  so scores ran on Campari as a proxy — two very different amari (soft/sweet/rosy vs
  aggressively bitter). The chemistry was computed for the *wrong ingredient*, and only the
  host Claude's diligence surfaced that. Lesson: when an ingredient is missing, Cobber's
  grounding quietly becomes vanilla-Claude guessing wearing a chemistry costume. Fix =
  broaden coverage AND make Cobber itself announce substitutions, not depend on the model
  noticing.
- **Novelty is asserted, not measured (yet).** "A pairing almost nobody makes" came from
  the hand-curated tradition table, not real co-occurrence data. The moat (novelty) isn't
  truly grounded until the NPMI work lands.
- **The marketable claim rests on flagged-uncertain data.** The lemon aspen twist — the
  differentiator you'd lead a pitch with — is `TODO: verify` in the README. Verify before
  any menu/post claim.
- **The host Claude did most of the work.** The 30/30/20/10/5 ratios, the sour template,
  the egg white, the dry-then-wet shake, the balance read, the Montenegro adjustment — all
  host Claude. Cobber contributed the grapefruit bridge and the lemon aspen idea, and that's
  it. Confirms the ratios / technique / texture gaps live, and shows today Cobber is a thin
  suggestion layer with Claude carrying the load.
- **Honesty depended on the model noticing**, not on the data. A diligent host Claude caught
  the proxy and the uncertainty; a careless one wouldn't have. The confidence field must make
  this systematic.

**Test-driven priority order (supersedes the pre-connection guesses in §8):**
1. Broaden ingredient coverage to the real bar canon (Amaro Montenegro first) + make
   substitutions explicit in Cobber's output.
2. Confidence plumbing (V2) so the grounding is visibly honest and never silently degrades.
3. Verify the natives (V2 honesty pass) — before any public or menu claim.
4. NPMI co-occurrence (beyond-the-classics) — to make novelty *measured*, not asserted.

These four protect the value proposition. Ratios, technique, and texture come after — they
make the drinks better, but the four above are what stop Cobber being a wrapper around Claude.

## 8. Roadmap / queued tasks

*Task inventory below. For current priority order, see §7a (test-driven) — it supersedes
the original guesses here.*

0. **Coverage + substitution transparency** (new, surfaced by the live test) — expand the
   seed to the real bar canon starting with Amaro Montenegro; make Cobber explicitly report
   when it's substituting a proxy (e.g. "no Montenegro — scored on Campari") instead of
   leaving the host model to catch it.
1. **V2 honesty pass** — `confidence` field, verify natives (cited), honest pass on
   trade-secret composites, split spirits into category profiles (white/aged/overproof
   rum etc.). *Foundation.*
2. **Beyond the classics** — NPMI co-occurrence from IBA + TheCocktailDB (real tradition
   data); culinary/umami ingredients (shio koji, miso…) + the taste-axis layer.
3. **Register dial** — summery↔wintery weighting over taste/texture + technique.
4. **Next pile** — technique/preparation model; ratios/dilution/strength; a
   tasting-feedback loop (your verdict graduates into the data — same pattern as the
   LinkedIn Content OS); an eval harness (does Cobber rank known-great pairings above
   known-bad ones?).

## 9. Known gaps / limitations (honest)

- Technique and ratios unmodelled (biggest).
- No feedback loop — generates on theory, never learns what actually tasted good (high-
  value "next").
- Compound presence is binary — no concentration data (caps chemistry quality; same limit
  as FlavorGraph).
- The food-pairing hypothesis (shared compounds = good) is contested; some cuisines pair
  by contrast. Harmony is a useful heuristic that can be confidently wrong.
- Onboarding friction: an MCP server suits AI builders, not working bartenders. A
  bartender-friendly surface is a future concern.

## 10. Data sources & the food-graph rationale

- **FlavorDB / FlavorGraph** — build-time *reference only*, never bulk-ingested, never at
  runtime. Two legitimate uses: (a) citing per-ingredient compound profiles when verifying
  data; (b) the source for *culinary crossover ingredients* (shio koji, miso, umami,
  fermented/savoury) that cocktail datasets structurally lack — these come from the
  kitchen, and the food-chemistry world is where their profiles live. This is the real
  reason the "food-skewed" graph matters.
- **FlavorGraph methodology** (replicable for cocktails, easier at bar scale): NPMI
  co-occurrence over a recipe corpus + ingredient→compound chemistry edges + (optional,
  skipped here) graph embeddings. Cobber is already a hand-built small version of this.
- **IBA official cocktails** (102, three categories) — the canonical classic set to seed
  co-occurrence from. **TheCocktailDB** (free API) for broader corpus. **Difford's** for
  later breadth.

## 13. Ingredient → flavour → compound: the research landscape (13 June 2026)

This section records the result of a deep research pass on public datasets and methods for
computing ingredient-level taste axes (sweet/sour/bitter/salty/umami) from compound-level
data. Ari's question: "There must be some research on chemical compounds... bridging between
ingredients into flavour and then compound." Here is what exists and what it means for Cobber.

### The correct scientific framework: Dose-Over-Threshold (DoT / TAV)

Perceived taste intensity maps from compound concentrations via:

```
DoT_i = concentration_i / taste_threshold_i
```

Compounds with DoT ≥ 1 are sensorially active. The ingredient's taste axis score is built
by summing DoT values across all active compounds in a given taste class, then normalizing
(log1p-scaled to 0..1, consistent with how Cobber already handles tradition). This is called
Taste Activity Value (TAV) in the beer/wine literature. The Hofmann sensomics group at TU
Munich validated this framework via aroma-recombination and omission experiments. Key paper:
Hofmann et al. JAFC 2018 (Pot-au-Feu sensometabolome), DOI: 10.1021/acs.jafc.7b05089.

**Critical caveat (Calvino et al., Chemical Senses 2007, DOI: 10.1093/chemse/bjm008):**
different bitter compounds with identical DoT can produce markedly different suprathreshold
intensities. DoT is an ordinal signal, not a ratio-scale intensity. Cross-class summation
is an approximation.

### What public datasets exist

| Dataset | What it has | What it lacks | License | Download |
|---|---|---|---|---|
| **FooDB** (U. Alberta) | 1,000+ foods, 70K compound entries, concentrations | Only 5.3% of entries have measured concentrations; distilled spirits under-curated | CC BY-NC 4.0 | foodb.ca/downloads (~440MB CSV) |
| **ChemTastesDB v2** (Milano, 2025) | 4,075 molecular tastants → taste class (bitter 1,615, sweet 1,313, umami 220, sour 49, salty 16) | No concentrations | CC BY 4.0 | zenodo.org/records/15051366 |
| **FlavorDB2** (IIIT-Delhi) | 936 ingredients, 25,595 aroma molecules, compound-ingredient links | Presence/absence ONLY (not concentrations); "concentration" fields are FEMA additive levels, NOT natural ingredient levels | Unspecified (web access free) | Per-record only, no bulk download |
| **FlavorGraph** (Korea U., Apache 2.0) | 6,653 ingredient nodes + 1,645 compound nodes + pre-trained 300D embeddings | Compound data is AROMA compounds from FlavorDB (same as what Cobber already tracks); no taste compounds; no concentrations | Apache 2.0 | GitHub: lamypark/FlavorGraph (nodes/edges CSV) |
| **BitterDB** (Hebrew U., 2024) | ~2,400 bitter molecules with TAS2R receptor data | No bulk download; per-query SDF/SMILES | CC BY-NC (paper) | bitterdb.agri.huji.ac.il |
| **SuperSweet** (Charité Berlin) | 8,000+ sweet compounds | No bulk download documented | CC BY-NC-SA 3.0 | bioinformatics.charite.de/sweet/ |
| **Foodpairing Inspire KG** | 102 ingredients with taste/aroma/texture (includes vodka) | Only 102 ingredients; proprietary main DB (20K+ ingredients) costs | CC BY 4.0 | github.com/foodpairing/inspire_kg (Turtle RDF) |

### Critical finding: terpenes ≠ taste

**FlavorDB and FlavorGraph catalog AROMA compounds** (volatile terpenes, esters, alcohols).
These are NOT the same as taste-active compounds. Gin's flavor is dominated by linalool,
alpha-pinene, limonene — all detected by smell, not taste. Under the DoT framework these
contribute zero to bitter/sweet/sour axes. Gin's taste profile is correctly near-neutral
(bitter ~0.1 from minor botanical alkaloids; sweet ~0; sour ~0). This is why the
FlavorDB/FlavorGraph pipeline CANNOT fill in spirit taste axes — it is the wrong class of
compounds.

Taste-active compounds are non-volatile: organic acids (sour), sugars/glycerol (sweet),
bitter glycosides (gentiopicroside, amarogentin), tannins (astringency), glutamate (umami).
FooDB covers these but only 5% are quantified, and distilled spirits are under-curated.

### Why bartender expert knowledge is the right primary method

No existing public dataset can reliably compute taste axes for cocktail spirits and
proprietary liqueurs (campari's formula is secret; gin's terpenes are smell, not taste).
The existing curated values (campari: bitter 0.8, sweet 0.4) come from bartender sensory
knowledge — which is the only reliable method for this class of ingredients. The databases
confirm the WHY (gentiopicroside from gentian root → bitter class in ChemTastesDB) but they
cannot replace the VALUES (how bitter is campari in a cocktail context, calibrated 0..1).

The FoodMine study (Hooton, Barabási, 2020, DOI: 10.1038/s41598-020-73105-0) found that
even for garlic and cocoa — well-studied ingredients — FooDB was missing 48–72% of
compounds detected in the published literature. Distilled spirits would be worse.

### The full pipeline (for future Part B verification)

If Ari wants to verify taste axis values against chemistry:

1. **ChemTastesDB** (CC BY 4.0, Zenodo) → download; map our existing compound IDs to taste
   class via SMILES or name matching. Immediately flags whether each aroma compound is ALSO
   taste-active (most aren't, but some like gentiopicroside are).
2. **FooDB** (CC BY-NC, 440MB CSV) → for each ingredient, pull quantified compound
   concentrations. Filter to compounds in ChemTastesDB taste classes.
3. **DoT aggregation** → `DoT = concentration / threshold`. Sum per taste class. Log1p-
   normalize within corpus. Compare to curated values (should correlate if data is
   complete).
4. **Expert override** → where database data is thin (spirits, proprietary liqueurs), Ari's
   bartender judgment takes precedence. The databases supply provenance; the values come
   from the human.

This pipeline is worth building as `scripts/verify_taste_axes.py` when Part B starts. For
now, the bartender-calibrated values are correct.

### What was implemented (13 June 2026)

Taste axes added to 45 composites that were missing them, using bartender-calibrated values
(researched methodology confirms this is the right approach for spirits and proprietary
liqueurs). 25 composites are immediately learnable by the preference layer; 33 more will
become learnable when Ari de-provisions their PROVISIONAL notes after compound verification.
See handoff.md for the full learnable-after list.

## 11. The human / tool division

Cobber does the *science of where to look* — grounded, novel, valid directions, research
compressed from weeks to minutes. The bartender keeps the craft and the story: the final
balance and tasting, and the narrative (e.g. the Japanese kotatsu-mandarin origin of the
winter cocktail). The narrative is what makes a menu drink real, and it stays human.

## 12. Open questions / next decisions

- **Done:** connected to Claude Desktop and run live (the Funky Cobber). The mandarin-winter
  brief is still worth running as a second, tougher test of the novelty steering.
- First build action: task 0 (Montenegro + the bar canon + substitution transparency) — it
  fixes the most concrete failure the live run exposed and is cheap.
- Decide whether the tasting-feedback loop jumps ahead of the register dial — it's the only
  thing that turns the project from theory into learning.
- Day 1 post: lead with the chemistry-and-bartending hook. The Funky Cobber is real footage
  now, but hold the lemon aspen claim until that native data is verified.

## 14. Mouthfeel / body axis + the FooDB track (recommendation, 13 June 2026)

Ari's prompt: "we have the diff between brown and white sugar — but can we capture the
mouthfeel a chef describes? the thick body of kokuto, the pop of carbonation, the dry grip
of tannin?" This is the real ceiling of the current model and worth stating plainly.

**Where the current model already reaches.** Aroma (compounds) + the palate axes
(sweet/sour/bitter/salty/umami/fat/funk/spice) cover *taste and chemesthesis*. With the
13 June research pass we can now distinguish white vs demerara vs brown vs maple vs kokuto
by their cited Maillard chemistry, and `spice` captures ginger/chilli heat. Carbonation
"pop" is already handled in the right place — the technique layer (any carbonated id →
build/highball, never shake), because it is a preparation/texture concern, not a flavour.

**Where it does NOT reach: body / viscosity / astringency.** There is no axis for the
*physical* mouthfeel a chef leans on — the thick, clinging body of kokuto or molasses, the
dry pucker of tannin in a high-tannin vermouth or red wine, the coating weight of a
high-sugar syrup, the cooling of menthol. `fat` catches dairy/oil richness only. These are
real things a bartender balances against and we currently can't express them.

**Recommendation on the FooDB track (Ari asked for my call).** Do it, but as a *separate,
later, build-time* track — not now, and not the way the aroma data was built. Reasoning:

1. **FooDB is the right source for this and only this.** FlavorDB/FlavorGraph (our aroma
   spine) catalog *volatiles*. FooDB catalogs *constituents* — sugars, proteins, fibre,
   tannins, organic acids, minerals. That is exactly the body/astringency/mineral layer.
   It is the correct tool for mouthfeel and the wrong tool for aroma; keep them separate.
2. **But FooDB is sparse and NC-licensed.** ~5% of entries are quantified, distilled
   spirits are under-curated, and the license (CC BY-NC) means reference-only, never bulk
   ingest — same rule as every other source. So FooDB *informs* curated axis values; it
   does not auto-populate them. Expect bartender calibration to remain the primary method,
   with FooDB supplying the WHY (kokuto's body ← retained solids + minerals), exactly as
   ChemTastesDB supplies the WHY for taste in §13.
3. **Design the axes before fetching any data.** Proposed additions to the palate-axis set,
   all 0..1, all flagged like `taste`: **`body`** (watery → syrupy/viscous; sugar syrup
   high, soda 0), **`astringent`** (tannin grip; red wine / strong tea / unripe-fruit
   tannin), and possibly **`cooling`** (menthol/mint TRPV-M8, the inverse of `spice`).
   Each plugs into `balance()` as a note/structure input the same way `spice` did — small,
   honest, one flag at a time. `body` in particular would finally let the register dial
   (§4, summery↔wintery) weight "more body / less dilution = wintery" as designed.
4. **Sequencing.** This is a session of its own: it touches the schema (`VALID_TASTE_AXES`),
   `balance()` (new notes + maybe structure), the INSTRUCTIONS, and a fresh research pass.
   It should land AFTER the current lookup/spice/research work is settled, and it pairs
   naturally with the Part B verification pass (§13) since both are "go get the cited
   constituent data." Treat the molasses/muscovado entries (deferred this session) as part
   of it — they share the body story.

**What we deliberately did NOT do this session, and why (honesty record).** We did not invent
a sulfur compound for kokuto's koku, did not assign it an umami number, and did not add
guaiacol/cyclotene/HMF (real but cited only at class level or absent from our vocabulary, and
inert until a second ingredient shares them). Those gaps are written into the entry notes,
not hidden — the same discipline as provisional flags.

## 15. Research records — ingredient profiles (13 June 2026)

Build-time research, web-sourced with citations, every claim verified before it landed; the
host can hallucinate compounds, so uncertain items were flagged PROVISIONAL or left out for
Ari, never fabricated. Full citations live in each entry's `source` field; summary here.

- **cranberry** (HIGH) — key odorants from a GC-O/OAV study (Bult et al., *J. Agric. Food
  Chem.* 2016, 64(24):4990, DOI 10.1021/acs.jafc.6b01150) + the Vaccinium benzoic-acid route
  (Croteau 1968/1978): hexanal, beta-ionone, ethyl 2-methylbutyrate, benzaldehyde, octanal.
  beta-ionone gives a real berry bridge to raspberry. De-provisioned. cranberry_vodka
  inherits it via the composite union.
- **tonic_water** (MEDIUM) — the honest correction: quinine is the defining bitterness but is
  NON-volatile, so it lives on the bitter axis (0.8), not in `compounds`. Aroma = added citrus
  oil (limonene). Kept PROVISIONAL: limonene confirmed for Fever-Tree's disclosed bitter-orange
  oil, inferred for Schweppes ("natural flavors" proprietary). No tonic-water headspace GC-MS
  paper was findable.
- **ginger_ale / ginger_beer** — split into two `ginger`-derived composites (they were
  profile-less placeholders / a single raw). Both inherit ginger's chemistry; `spice`
  separates them (beer 0.7, ale 0.3). PROVISIONAL: mass-market ginger ale has ~no gingerol
  (Canada Dry settlements, court-confirmed), so the craft-ginger assumption is flagged.
- **dark sugars** — demerara confirmed sotolon-alone (Tokitomo 1980; the absence of heavier
  Maillard products is its signature, de-provisioned); brown_sugar gains the cited roasty
  layer (Chen 2022 *Molecules*; Food Chem 2021); maple gains vanillin + furaneol; kokuto added
  with sotolon + cited pyrazine, its sulfur/koku character documented as a known gap (the
  storage study names sulfur compounds only at class level — encoding a species or an umami
  number would be fabrication). brown/maple/kokuto PROVISIONAL pending a full-text OAV pass.
- **spice axis** — capsaicin (hot_sauce) and gingerol (ginger, ginger beer) finally have a
  home; the axis is grounded in the heat compound the ingredient is already known to carry.
- **Reviewer to-dos banked for Ari / Part B:** full-text OAV confirmation for brown sugar &
  maple; name kokuto's sulfur species (then the savoury bridge can be modelled); a dedicated
  molasses GC-MS pull; molasses + muscovado entries (deferred — see §14).
