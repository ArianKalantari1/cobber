# To-do: Cobber scoring upgrade (reviewed and refined, 23 October 2026)

This refines the list Ari approved on 22 October (commit `3cdd239`). The goals stand: stop
rewarding redundant overlap, put amounts into the maths, and fill the back bar. What changed
is *how*. Checked against the data, several parts would not work as written. Items marked
**(changed)** or **(new)** differ from the 22 October list; Ari approved them on 23 October
(the decisions are listed at the end). Unmarked items are as originally approved.

Branch: `claude/eager-turing-giasrj` (it carries the house specs). Follow CLAUDE.md: commit
and push after each step, and Ari approves all data before it goes in. Every number about
Cobber's data and recipes in the review came from `scripts/prototypes/review_scoring_todo.py`,
which was removed once step 1 was built; check out commit `a528bce` to rerun it. Outside
facts (the gin listing, Arnold's dilution, the EU sugar minimums) are sourced where they
appear.

## What the review found
1. **Two of the three target scores don't hold.** Olivia B's 0.149 comes mostly from one
   pair, Bénédictine + vanilla, which scores 1.000 because Cobber models Bénédictine as
   vanilla alone (a provisional entry). Without that pair B scores 0.084, below M1 and M2
   (0.111). B also fails the prototype's own duplicate check, so its search could never have
   produced it. "Restaurant Olivia = 0.072" includes dry vermouth, which the restaurant
   doesn't use; the menu spec scores 0.043. All three numbers come from the full citrus
   masking that the plan itself rejects.
2. **As hard blocks, the redundancy rules break ordinary drinks.** They would forbid 31 of
   75 IBA classics (41%) and 35% of the whole canon, including the Negroni, Dry Martini,
   Aviation, Clover Club, French 75 and White Lady. Cobber's gin lists lemon as a botanical,
   so "botanical inside a composite" and "under 20% new compounds" both block lemon in every
   gin drink. The prototype only looked safe because anchors and citrus were exempt.
3. **An 80% overlap threshold calls lemon and lime the same thing** (0.818), which
   contradicts Ari's correction. The data has a natural gap between 0.909 and 0.867.
4. **The citrus problem is a general counting bug.** Averaging over pairs counts a compound
   shared by k ingredients k(k−1)/2 times. The most widespread compounds in the data are
   citrus terpenes: sabinene, β-pinene, limonene and α-pinene each appear in about a third of
   the 152 profiled ingredients.
5. **Most duplicates are a data-model problem.** 37 composites are a single botanical. Some
   are fair (limoncello = lemon, amaretto = almond). Others are wrong: white rum, Scotch,
   Irish whiskey, crème de cacao and Bénédictine are all `[vanilla]`, so to Cobber they are
   one and the same. A few fuller entries are identical by accident too: Amaro Montenegro
   has exactly Aperol's bill.
6. **The olive–amaretto bridge rests on two compounds,** cinnamaldehyde and menthone, in a
   provisional olive profile. Olive isn't on the research list, though the whole Olivia
   direction depends on it.
7. **"Nutty must come out level with citrus" can't work as written.** Weighting flavour
   families by ml is weighting aroma by amount, which the plan rules out. Family weights are
   compound counts, so gin alone (9 citrus compounds) outweighs amaretto (2 nutty ones) in
   every gin sour. The compound wheel even puts amaretto's top family as "fruity".
8. **Smaller gaps.**
   - The prototype's fourth rule was dropped: sugar, salt, soda and foamer are structure,
     not aroma. It is the biggest single fix (a Gin Fizz goes from 0.09 to 0.56).
   - The rules and the ml-weighted step need data the plan left to the research step: the
     house gin, vanilla syrup, brine, olive oil and foamer.
   - "About 18% ABV" assumes about 30% dilution, with no model stated.
   - A fresh install pulls `mcp` 2.x, where FastMCP was renamed, so the server and its test
     no longer import.

**What held up:** the three problems are real. 1.55 standard drinks is right under its
assumptions (1.56). The research counts (Licor 43: 77, yuzu: 47 and so on) are accurate. Not
weighting aroma by amount is the right call.

## 0. Before changing any scoring (new)
- [x] **Pin `mcp>=1,<2`** in `pyproject.toml`. Migrating to mcp 2's `MCPServer` is its own
  task.

  *Why:* a fresh `pip install -e .` gets mcp 2.x, and `tests/test_server.py` fails to import.
  Step 1 adds a server tool, which couldn't be tested.
- [x] **Regression panel** (`scripts/eval_scoring.py`). It covers the Olivia versions, all 75
  IBA drinks (score and rank), and a list of known pairs: duplicates such as amaretto/almond
  and limoncello/lemon, distinct pairs such as lemon/lime and gin/lemon. Commit the baseline
  output, and rerun it after each rule.

  *Why:* the rules were designed on one drink that hasn't been tasted, and every rule changes
  every score. The block rules would have broken 41% of IBA without anyone noticing. The
  design notes already ask for this ("eval harness", §8).

## 1. Fix the counting (engine)

Built on 23 October, along with step 0: see the status note under "Done when".
- [x] **Structure items aren't scored for aroma (new).** Ingredients with no aroma profile
  (sugar syrup, salt, soda, egg white, foamer, vodka) are left out of harmony. They still
  count in balance.

  *Why:* today each one adds pairs that score 0 and drag the average down, so a Gin Fizz
  scores 0.09 instead of 0.56. It was rule 4 in the prototype and got lost in the to-do.
- [x] **Diminishing returns per compound, not a citrus list (changed).** Inside a drink, the
  first pair that shares a compound counts in full. Each further ingredient carrying the same
  compound adds half as much as the one before. Pair scores don't change.

  *Why:* this is Ari's rule (first citrus link in full, further sources halved), applied to
  what actually repeats: the molecules. Lemon, lime and grapefruit keep their differences,
  because their own compounds still count. No hand-kept citrus list is needed (yuzu,
  Italicus or the house gin would make one stale). It also stops vanilla-on-vanilla and
  almond-on-almond stacks. Checked: gin + lemon stays at 0.556, gin + lemon + lime falls from
  0.62 to 0.32, and the IBA ordering mostly holds (rank correlation 0.76).
- [x] **Same voice, not a block (changed).** Two ingredients count as one voice, with no
  bridge credit between them, when either:
  - their profiles are at least 90% the same; or
  - one is an aroma botanical (aromatic, herb or bitter role) already on the bill of a
    composite in the drink, such as coriander seed with gin.

  Juices, fruit and syrups on a bill still bridge (lemon with gin). Nothing is blocked, and
  the output names the voice ("amaretto and almond: same aroma").

  *Why:* 90% sits in the data's gap. Lemon and lime stay separate (0.818), while every exact
  copy and orange/triple sec (0.909) merge. The role test keeps the to-do's "coriander in
  gin" without killing gin + lemon (282 canon drinks). Reinforcing a note is a real technique
  (coffee liqueur with espresso; triple sec with orange, in 93 canon drinks), so it gets no
  credit rather than a ban.
- [x] **Suggestions only offer new voices (new).** In `build_around`, a candidate that would
  merge into a voice already in the drink isn't offered as a new idea.

  *Why:* an average can't penalise a pure copy, so without this limoncello still ranks first
  as an addition to the Olivia core. With it, limoncello and almond drop out and honey stays
  in (checked).
- [x] **Identity guards on `build_around` and `suggest_from_pantry` (changed).** Add:
  - `locked`: must-keep items, any number (anchors stay at 2–3);
  - `exclude`: ids never to add;
  - `max_spirits`: how many `spirit`-role items are allowed;
  - `max_additions`, replacing the fixed 2.

  Rank every candidate first, then work out balance, template and technique only for the top
  n.

  *Why:* Olivia has four fixed items, but anchors are capped at three. Cobber has no colour
  data, so "no dark modifiers" has to be an exclude list from the host Claude, who knows
  Averna is dark. A colour field on 163 entries isn't worth it for one drink. `build_around`
  already searches exhaustively, and the prototype's exhaustive check reached the same answer
  as its hill-climb loop, so don't port the loop. With four additions from a 40-bottle pool
  there are about 100,000 candidates, and today every one is fully annotated before sorting.
- [x] **Notices for stacking and for the target note (changed).** Count *sources* per flavour
  family, using each ingredient's curated `descriptors`.
  - Notice when 3 or more ingredients are sources of one family ("3 citrus sources: house
    gin, limoncello, lemon").
  - With an optional `target_family`, notice when the target has fewer sources than the
    strongest family.

  It is a notice, not a score change.

  *Why:* counting sources is exactly Ari's complaint, and it doesn't weight aroma by amount.
  Curated descriptors read like a bartender (amaretto: nutty and sweet; Bénédictine: herbal
  and sweet), while compound counts follow how much data an entry has. On IBA it flags 8 of
  75 drinks, all citrus-heavy (White Lady, Cosmopolitan, Lemon Drop and others). For Olivia,
  M2 is the only version where the nutty sources (amaretto, maraschino) match the citrus
  sources (gin, lemon). About half the descriptor words ("lime", "spice", "oak" and others)
  aren't in the family map yet, and adding them needs Ari's OK.
- [x] **`score_drink` engine function and server tool (new).** It scores an exact drink:
  harmony under the new rules, the voices and why they merged, the bridges per pair, the
  notices, and provisional flags. Step 3's numbers plug in here.

  *Why:* the Olivia work was all about scoring specific drinks, and today there is no tool
  for that, only pairs (`score_pairing`) and suggestions (`suggest_from_pantry`).
- [ ] **Done when (changed):** ordering checks plus snapshots, not golden numbers.
  - Gin + lemon is still a bridge (0.556), and lemon + lime are two voices.
  - House gin + lemon + limoncello gets the stacking notice and scores no higher than house
    gin + lemon.
  - Amaretto + almond, limoncello + lemon and gin + coriander seed are one voice each. So is
    Bénédictine + vanilla, until Bénédictine's bill is fixed.
  - Limoncello isn't offered as an addition to the Olivia core; honey is.
  - No IBA drink is blocked. Ari looks over the biggest movers (in the review run, Tommy's
    Margarita and White Lady fall; Gin Fizz and John Collins rise).
  - The new Olivia scores are recorded as regression snapshots.

  *Why:* the old numbers can't come from rules we've decided not to build, and one of them
  contains the duplicate these rules remove. Orderings carry the bartender's judgement, and
  snapshots catch drift.

  **Status (23 October):** every automated check passes (`tests/test_drink_scoring.py`).
  Ari looked over the movers and accepted them, and the baseline was re-saved. Ari also
  approved the word list with the proposed open calls (warm → spice, smoke → woody,
  cane → green/herbal, bright ignored); the words are in `data/flavor_families.json`. Ari's
  reading of the falls (Tommy's, Lemon Drop, Espresso Martini) is that those drinks stack a
  note on purpose, which leads to step 1b.
- [x] Write the rules into `docs/cobber-design-notes.md`, section 9 (known gaps).
- [x] Delete the prototypes in `scripts/prototypes/` once Ari has looked over the movers.
  They are recoverable from git history (commit `a528bce`).

## 1b. Amplification engine (new; Ari, 23 October; confirm this reading before building)

Ari's point: stacking a flavour is a deliberate technique, flavour amplification, not a
mistake.
- Tommy's Margarita stacks agave (tequila + agave syrup) to be agave-forward.
- The Lemon Drop stacks lemon (citron vodka + lemon).
- The Espresso Martini stacks coffee (espresso + coffee liqueur).

Balance always matters as well. Step 1 reads bridges between different notes correctly, but
it has no positive reading for amplification: a same-voice pair just earns no credit, and the
stacking notice treats every stack as a risk.

How I read it:
- **Amplification is one note carried through different parts of the drink**, the parts the
  drink needs anyway: Tommy's agave syrup *is* the sweetener, the Lemon Drop's citron vodka
  *is* the base, and the Espresso Martini's coffee liqueur *is* the sweetener. The note gets
  louder without adding sugar or acid, so the balance holds. Olivia already does it with the
  olive: brine in the salt slot, olive oil for texture, an olive on the rim.
- **It costs balance** when two carriers fill the same part, e.g. two sweet liqueurs (the
  amaretto and maraschino carrying nutty in M1) add sugar.
- **It crowds** when a note that isn't the hero picks up carriers, e.g. citrus in M1 (gin,
  vermouth, lemon) drowning the nutty note.

What the engine would do:
- [ ] Detect amplified notes (same-voice groups, and families with 2+ sources), and which
  part of the drink each carrier fills (base, sweetener, acid, bitter, modifier, seasoning,
  texture, garnish).
- [ ] Read intent. With a hero note named, amplifying it is good ("agave-forward: base +
  sweetener"), and another note amplified past it is crowding. This replaces the blanket
  stacking notice.
- [ ] Read the balance cost. Carriers in different parts are free; two in the same part add
  sugar, acid or bitterness. Step 3's grams make it exact.
- [ ] Suggest amplifiers. For a hero note, offer pantry items that carry it in a part the
  drink already needs (agave syrup instead of sugar syrup, olive brine instead of saline),
  alongside the bridge suggestions.
- [ ] Keep harmony as it is: amplification is a second reading next to it, so Tommy's and the
  Espresso Martini read as amplification drinks, not weak ones.

Needs from step 2: olive brine, olive oil and the other preps as their own entries, so
Olivia's amplification is visible to Cobber.

## 2. Data the checks depend on (moved up; review proposal, Ari approves)
- [ ] **House gin: confirm the bottle first (changed).** Get a label photo from Ari (name and
  ABV), then ask the distillery for the botanical bill. The only public listing found for
  Spirits of Newtown (a third-party delivery menu) shows a "Triple Juniper Gin" at 38%, made
  with juniper, coriander and angelica. That doesn't fit "very citrus-forward, little
  juniper".

  **Interim (Ari, 23 October):** until the label arrives, the house gin is Cobber's generic
  London dry `gin` at 40%. It already carries lemon, so it counts as a citrus source, and it
  sits between Ari's description and the listing without inventing a bill. Add a proper
  `house_gin` composite once the label and bill are in.

  *Why:* step 1's stacking test and step 3's strength test need it. At 38% rather than 40%,
  Olivia B is 1.51 standard drinks, not 1.56.
- [ ] **Fix the entries that are identical by accident, Bénédictine first (new).** These are:
  - Bénédictine, white rum, Scotch, Irish whiskey and crème de cacao (all `[vanilla]`);
  - Cynar (`[gentian]`) and sloe gin (`[juniper]`);
  - pisco and sherry (`[grape]`);
  - mezcal (`[agave]`, with no smoke);
  - Amaro Montenegro, which has exactly Aperol's bill (bitter orange peel, gentian, orange);
  - dark rum, which has exactly spiced rum's bill (vanilla, clove, cinnamon);
  - demerara, maple syrup and brown sugar (each is sotolon alone);
  - lemon aspen and lemon myrtle (the same compound list; both natives are still to be
    verified).

  Leave the fair ones as they are (limoncello, amaretto, crème de cassis, and Cointreau =
  triple sec = blue curaçao).

  *Why:* with the same-voice rule, these would quietly merge into "vanilla", and Scotch +
  Bénédictine (the Bobby Burns) would get no credit. Olivia B's lead came from exactly this.
- [ ] **Verify the olive profile (new).** It is provisional and enriched from FlavorDB. The
  olive–amaretto bridge (0.18) is just cinnamaldehyde and menthone, both odd for olive.

  *Why:* the whole Olivia direction ("olive's only real partner is amaretto") rests on these
  two compounds.
- [ ] **Add what Olivia uses (new):** vanilla syrup (101 recipes in the unmatched list), olive
  brine, olive oil and foamer.

  *Why:* step 3's Olivia B test can't run without them.

## 3. ml-weighted strength, sugar and acid
- [ ] Add the per-ingredient fields `abv`, `sugar_g_per_100ml`, `acid_g_per_100ml`
  (citric-acid equivalent) and `salt_g_per_100ml`. Each gets a source citation or a
  provisional flag in `notes`. Missing data is reported as missing, never assumed to be 0.
- [ ] Add an engine function that takes `{id: ml}` plus the method (shake, stir, or reverse
  dry shake with foamer). It returns ml in the tin and in the glass, ABV, Australian standard
  drinks (10 g of alcohol), sugar g/100 ml, acid %, the sugar-to-acid ratio, and salt.
- [ ] **Dilution model, cited (changed).** Use Dave Arnold's equations from *Liquid
  Intelligence* (stirred and shaken). Check them against the book and cite the page. The
  output says which model it used.

  *Why:* "about 18% ABV in the glass" quietly assumes about 30% dilution. Even the stirred
  equation (as quoted secondhand) gives 37% dilution for this drink, about 17% ABV, and
  shaking dilutes more. The target has to come from the model, not from a number in a chat.
- [ ] **One reading for sweet and sour (new).** When amounts are given, grams of sugar and acid
  replace the summed 0–1 sweet and sour axes. Bitter, umami, fat and funk stay as they are.
  The output says which was used.

  *Why:* otherwise the axes can say "sour-balanced" while the grams say "too sweet".
- [ ] **Texture: define it or drop the word (new).** The smallest honest version is dissolved
  solids (sugar + acid, g/100 ml), foam yes or no, and fat in ml, all flagged as proxies.

  *Why:* the step promises texture, but nothing in the plan computed it.
- [ ] Expose it through `score_drink` and write tests.
- [ ] **Done when (changed):**
  - From label strengths, Olivia B gives 1.56 standard drinks at 40% gin and 28% amaretto
    (1.51 at 38% gin), within ±0.05.
  - Its ABV in the glass is whatever the cited model gives. Expect roughly 15–17%, not 18%.
  - The house-spec hand maths checks out. M1 comes to 2.15 standard drinks with 45 ml of gin
    (the specs said "about 2.2") and 1.68 with 30 ml. M2 and P come to 1.47 and 1.42 with
    30 ml, because they drop the vermouth, so the specs' "about 1.6–1.7" only holds for M1.

## 4. Back-bar research (sub-agents allowed)
- [ ] Write the results to a review proposal (for example `data/backbar_proposal.json`).
  Don't edit `ingredients.json` or `composites.json` until Ari approves. Unconfident matches
  go to `unmatched_ingredients.txt`.
- [ ] **Order (changed):**
  1. Step 2's items.
  2. By recipe count in the unmatched list (summed across spellings):
     - Suze, Salers, Bonal and other gentian aperitifs (195);
     - walnut bitters and nocino (118);
     - crème de violette (103);
     - sherry by style: amontillado (102) and PX (96) as well as oloroso (62), manzanilla
       (52) and fino (7);
     - Licor 43 (77);
     - Frangelico (62);
     - yuzu (47).
  3. The rest of the bar: Massenez Popcorn and Cassis, Floc de Gascogne, Lillet Rosé,
     Italicus, pommeau, Skrewball, kumquat and macadamia.

  *Why:* the data the tests need comes first. After that, recipe count is how much of the
  corpus each entry unlocks. Amontillado and PX each out-count fino more than ten to one, but
  they weren't on the list.
- [ ] **Where sugar numbers come from (new).** Use producer tech sheets first, then Arnold's
  measured table. As a last resort, use the EU legal minimums, flagged "legal minimum, not
  measured": liqueur 100 g/L; cherry-spirit liqueurs such as maraschino 70; gentian liqueurs
  such as Salers and Suze 80; "crème de" 250; crème de cassis 400 (Regulation (EU) 2019/787,
  Annex I; check the text).

  *Why:* most producers don't publish sugar. "Cite every number" needs a ladder of sources
  that also says how good each number is.
- [ ] ABV, sugar and acid for every bottle on the Apéritif & Co bar (`docs/menu/menu.json`)
  and in `docs/house-specs.md`, from labels and producer specs.

## 5. Olivia amounts (after 1–4)
- [ ] **Re-score before choosing a lead (changed).** Score M1, M2, P and B with the new rules
  and the fixed Bénédictine. In the review run the four sit within 0.02 of each other
  (0.095–0.113), so Cobber can't pick between them on aroma, and the tasting decides. Put B
  into the tasting next to M1 and M2 rather than making it the lead in the house specs.

  *Why:* B's lead rested on the Bénédictine = vanilla duplicate.
- [ ] **The amount search is a small grid, not a loop (changed).** Ranges: gin 30–35, amaretto
  10–15, Bénédictine 5–10, vanilla 2.5–5, brine 5–10, lemon 17.5–20, in 2.5 ml steps (324
  sets). Keep the sets at 1.5–1.7 standard drinks with a sour's sugar-to-acid balance, and
  give Ari 2–3 to taste. This is a script, not an engine feature.

  *Why:* by the plan's own decision, amounts don't change the aroma score, so only the
  structure numbers move.
- [ ] Update the Olivia section of `docs/house-specs.md` after Ari's tasting verdict.

## 6. Tasting log (Ari): start now, not later (changed)
- [x] Keep a committed R&D log (for example `docs/tasting-log.md`, or `data/tasting_log.json`
  once the regression panel reads it). Each entry has the date, the spec with amounts, the
  verdict and notes. This isn't `record_tasting_feedback`, which is personal and local and is
  never committed, by design.
- [ ] Taste M1 against M2 (and B) now; the open tests in the house specs already list them.
  The verdicts become step 1's real check: do the new scores put the drinks in the same order
  as Ari's palate does?

  *Why:* nothing on Olivia has been tasted, and the scoring is being tuned on that one
  untasted drink. The tasting is the only ground truth, and it needs no code.
- [ ] Later: use the verdicts to correct the provisional data (sugar and strength).

## Decided against (don't build)
- **Weighting aroma by amount** (as approved). It would need compound concentrations, and
  those barely exist: FooDB has measured values for about 5% of entries, and spirits are the
  worst covered. "Shared compounds = good pairing" is also contested (Ahn et al. 2011:
  Western cuisines pair shared compounds, East Asian ones avoid them; critics note it ignores
  odour thresholds). Keep aroma harmony for finding ideas, not for judging amounts.
- **A hand-kept citrus list with full masking.** Masking erases what makes lemon, lime and
  grapefruit different, and a list goes stale. Replaced by per-compound diminishing returns.
- **Hard blocks for redundancy.** As blocks they forbid 41% of IBA. Replaced by same-voice
  merging and notices.
- **A colour field for "no dark modifiers".** The host Claude passes an exclude list instead.
- **Porting the hill-climb loop.** `build_around` is already exhaustive, and in the prototype
  the exhaustive check matched the loop.
- **Weighting compounds by how rare they are across the pantry, for now.** It would also cut
  a single classic link like gin + lemon (limonene is everywhere), which goes against "one
  citrus link does a real job". Revisit it with the regression panel.

## Decisions (Ari, 23 October 2026)
1. **Approved.** Redundancy earns no credit and raises a notice, but is never blocked (the
   22 October plan blocked it).
2. **Approved.** Per-compound diminishing returns instead of a citrus list, starting at ½.
3. **Approved.** "Same aroma" at 90%, so lemon and lime stay different. Orange with triple
   sec counts as one orange note, reinforced.
4. **Approved.** "Too bright" and the target note as source counts from the curated
   descriptors, shown as a notice, triggered at 3 sources. Taste words (sweet, sour, bitter,
   salty, umami) don't count as aroma sources. Still open: the word-list proposal, including
   where "smoke", "warm" and "cane" go.
5. **Approved.** Fix Bénédictine (and the other entries that are identical by accident)
   before trusting B's score. B joins the tasting rather than leading. Bénédictine gets a
   provisional bill from what the producer discloses.
6. **Pending.** Ari sends the gin label once back at work. Until then the house gin is the
   generic London dry `gin` at 40% (see step 2).
7. **Approved.** The tasting log starts now (`docs/tasting-log.md`), with M1 against M2 and B.
