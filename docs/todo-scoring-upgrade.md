# To-do: Cobber scoring upgrade (approved by Ari, 22 October 2026)

Start here in the new chat. Branch: `claude/festive-einstein-3322ky` (house specs and the
prototypes are on it). Follow CLAUDE.md: commit and push after each step, and Ari approves
all data before it goes in.

## Why
Working on Olivia showed three problems with how Cobber scores:
- **Harmony counts redundant overlap as a good match.** It rewarded citrus on citrus with a
  citrus-forward house gin (limoncello, then lime), and amaretto against almond as a perfect
  pair.
- **Amounts never enter the maths,** so 2.5 ml of vanilla counts as much as 35 ml of gin.
  Strength and sugar had to be worked out by hand, and v3/v4 reached about 2.2 standard
  drinks before anyone caught it.
- **Half the back bar is missing or generic** in the data.

Decision: fix the counting and add ml-weighted taste, texture and strength. Don't weight
aroma by amount (reasons in the last section).

## 1. Put the redundancy rules into the engine
Reference prototype: `scripts/prototypes/olivia_loop2.py` (scoring rules) and
`olivia_loop3.py` (loop, identity guards, exhaustive check).
- [ ] **Citrus is a bridge, but with diminishing returns.** Ari's correction (22 Oct): lemon,
      lime, pink grapefruit and limoncello each have their own roundness, and one citrus
      link does a real job. The problem is stacking them: citrus-forward gin + limoncello +
      lemon is "way too bright".
      - Count the first citrus link in full, and discount each further citrus source
        sharply (for example, halve it each time).
      - Don't mask citrus compounds completely the way the prototype does. That erases the
        real differences between lemon, lime and grapefruit.
      - How much citrus the base brings depends on the gin. **The house gin is Spirits of
        Newtown** (confirmed by Ari): very citrus-forward with little juniper. Model it as
        its own composite, so its citrus counts as the drink's first citrus source.
- [ ] **The target note has to win, or at least compete.** If the drink is meant to be
      nutty (or any named note), check the balance of flavour families (via
      `data/flavor_families.json` and `engine.flavor_wheel`). Weighted by ml once step 2
      exists, the nutty family must come out at least level with the bright/citrus family.
      Warn when brightness outweighs it.
- [ ] **No credit for duplicates.** Block a candidate if its profile overlaps an ingredient
      already in the drink by 80% or more (amaretto = almond), if it's a botanical inside a
      composite already present (coriander in gin), or if it brings less than 20% new
      compounds.
- [ ] **Identity guards** (optional arguments): fixed anchors, one base spirit only, no
      dark modifiers, a maximum number of ingredients. Without these, the loop drifted
      Olivia into a brandy and coffee drink.
- [ ] Add these as options to the scoring and `build_around` functions, and expose them in
      the server tools. Write tests.
- [ ] **Done when** these numbers reproduce, all with corrected harmony:
      - restaurant Olivia (gin, dry vermouth, amaretto, honey, lemon, olive) = **0.072**;
      - amaretto + maraschino + dry vermouth = **0.111**;
      - gin, amaretto, Bénédictine, vanilla, lemon, olive = **0.149**;
      - limoncello no longer ranks above honey;
      - citrus-forward gin + limoncello + lemon triggers the "too bright" warning, while a
        single lemon link still counts.

      The first three numbers come from the prototype's full citrus masking. Expect small
      shifts under diminishing returns, and record the new values.
- [ ] Write the three rules into `docs/cobber-design-notes.md`, under section 9 (known gaps).

## 2. ml-weighted taste, texture and strength
- [ ] Add per-ingredient data fields: `abv`, `sugar_g_per_100ml`, `acid_g_per_100ml`
      (citric-acid equivalent) and `salt_g_per_100ml`. Each gets a source citation or a
      provisional flag in `notes`.
- [ ] Add an engine function that takes `{id: ml}` plus the method (shake or stir; dry
      shake with foamer) and returns:
      - ml in the tin and estimated ml in the glass after dilution;
      - ABV, and standard drinks (Australian: 10 g alcohol);
      - sugar g/100 ml, acid %, sugar-to-acid ratio, and salt.
- [ ] Combine it with the existing taste axes and role balance, then add a server tool and
      tests.
- [ ] **Done when** Olivia B (35 house gin / 10 amaretto / 7.5 Bénédictine / 2.5 vanilla
      syrup / 7.5 brine / 17.5 lemon / 5 olive oil) gives about **1.55 standard drinks**
      and about **18% ABV** in the glass, assuming 40% gin. Check the hand maths in the
      house specs against it.

## 3. Back-bar research (sub-agents allowed)
Write the results to a **review proposal** (for example `data/backbar_proposal.json`).
Don't edit `ingredients.json` or `composites.json` until Ari approves. Unconfident
matches go to `unmatched_ingredients.txt`.
- [ ] **ABV, sugar and acid for every bottle** on the Aperitif Co bar (`docs/menu/menu.json`)
      and in `docs/house-specs.md`, from labels and producer specs. Cite every number.
- [ ] **Profiles for missing or generic items:**
      - Licor 43 (77 recipes in the unmatched list), Frangelico (57), walnut bitters and
        nocino (more than 60), Massenez Popcorn, Violet and Cassis;
      - manzanilla, fino and oloroso as separate sherry styles;
      - Bénédictine (checking the existing entry), Floc de Gascogne, Lillet Rosé, Italicus,
        Salers, pommeau, Skrewball;
      - yuzu (47), kumquat (7), macadamia (3).
- [ ] **House gin = Spirits of Newtown Gin** (confirmed by Ari: very citrus-forward, little
      juniper). Research its botanicals and add it as its own composite, kept separate from
      the generic London dry `gin`.

## 4. After 1–3: amounts for Olivia B
- [ ] Run the loop over amounts: gin 30–35, amaretto 10–15, Bénédictine 5–10, vanilla
      2.5–5, brine 5–10, lemon 17.5–20. Use the redundancy rules plus the ml-weighted
      balance, with targets of about 1.5–1.7 standard drinks and a sour's sugar-to-acid
      balance.
- [ ] Give Ari a shortlist of 2–3 amount sets to taste.
- [ ] Update the Olivia section of `docs/house-specs.md`: Olivia B leads, with M1 and M2 as
      backups.

## 5. Later: tasting log (Ari)
- [ ] Record each tasting's verdict. Use them to correct the provisional data (sugar and
      strength) and to check what the scores predict.

## Decided against (don't build)
- **Weighting aroma by amount.** It would need compound concentrations, and those barely
  exist: FooDB has measured values for about 5% of entries, and spirits are the worst
  covered. "Shared compounds = good pairing" is also contested (Ahn et al. 2011: Western
  cuisines pair shared compounds, East Asian ones avoid them; critics note it ignores odour
  thresholds). Keep aroma harmony for finding ideas, not for judging amounts.
