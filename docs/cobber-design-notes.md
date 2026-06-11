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
- **Taste axes** — sweet / sour / bitter / salty / umami / fat / funk. *V2.* Captures
  taste/structure that aroma can't (e.g. umami from miso/shio koji).
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
