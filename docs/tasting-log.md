# Tasting log

Ari's verdicts on drinks Cobber helped build, in the repo so the scoring can be checked
against a palate. This is the shared R&D record. It is separate from
`record_tasting_feedback`, which keeps a personal profile on one machine and is never
committed.

Cobber's predictions go in *before* the tasting, so they can't be fitted to the result
afterwards.

## How to taste
- Make every version in one session, with the same lemon, foamer, shake and glass. Use single
  serves, not batches.
- If someone else can pour them under numbers, taste blind and reveal afterwards.
- Write down the exact ml actually used, and anything that differed from the spec.
- Strength changes how a drink reads (stronger tastes fuller), so each spec lists its standard
  drinks.

## What to record for each glass
- **Verdict:** loved / liked / ok / disliked / hated (the same words as Cobber's feedback
  tool).
- **Four questions.** Each one tests something Cobber claims:
  1. **Too bright?** This tests the stacking notice (3 or more citrus sources).
  2. **Does the target note come through,** level with the citrus? This tests the target-note
     notice.
  3. **Can you find the olive?** This tests the olive–amaretto bridge, which rests on a
     provisional olive profile.
  4. **Too sweet, too sour or too strong?** This tests the sugar, acid and strength maths
     (step 3 of the scoring upgrade).
- **Menu pick:** the version you'd put on the menu, and what you'd change.

---

## Session 1 (planned): Olivia, M1 against S, then M2 and B

Specs per serve, from `docs/house-specs.md` (M1, M2), the scoring to-do (B), and the
reimagining with the updated Cobber (S, 23 October). The house gin is the bar's gin. For
strength maths the gin is taken as 40% until the label is in.

| | M1: vermouth + maraschino | S: Manzanilla + maraschino | M2: maraschino + vanilla | B: Bénédictine + vanilla |
|---|---|---|---|---|
| House gin | 30 ml | 30 ml | 30 ml | 35 ml |
| French dry vermouth | 15 ml | none | none | none |
| Manzanilla | none | 15 ml | none | none |
| Amaretto | 15 ml | 15 ml | 15 ml | 10 ml |
| Maraschino | 7.5 ml | 7.5 ml | 7.5 ml | none |
| Bénédictine | none | none | none | 7.5 ml |
| Vanilla syrup | none | none | 2.5 ml | 2.5 ml |
| Green olive brine | 7.5 ml | 7.5 ml | 7.5 ml | 7.5 ml |
| Lemon | 20 ml | 20 ml | 20 ml | 17.5 ml |
| Extra-virgin olive oil | 5 ml | 5 ml | 5 ml | 5 ml |
| Foamer | yes | yes | yes | yes |
| Standard drinks (gin 40%) | about 1.68 | about 1.65 | about 1.47 | about 1.56 |

S's strength takes the Manzanilla at about 15%.

**Method (all):** reverse dry shake, double-strain into a chilled 150–180 ml coupe, then a
green olive on a pick and one pump of olive oil mist.

**Order:**
1. M1 against S first. The only difference is the vermouth against the Manzanilla, so this
   isolates the reimagining.
2. The winner against M2 and B.

**Bring in P** (crème de pêche instead of maraschino) only if you'd rather have peach.

**Why S (amplification).** The drink is meant to be nutty, savoury and bright, with the olive
forward. In M1 the vermouth is a third citrus carrier (after the gin and lemon), so the
brightness crowds the hero. S puts Manzanilla in the same slot. It is dry, so the sugar and
acid stay as in M1. It is briny, so it carries the olive in the modifier slot alongside the
brine (seasoning), the oil (texture) and the garnish (aroma). And its flor almond notes carry
the nutty side next to the amaretto and maraschino.

**Cobber's predictions** (from `score_drink`, 23 October; target `roasted_nutty`, and
`savoury` for the olive; the house gin scored as a generic London dry gin until its label is
in):
- **Aroma harmony:** M1 0.111, S 0.109, M2 0.102, B 0.119. That's within 0.02, so Cobber can't
  pick a winner on aroma; this tasting decides.
- **M1:** "3 citrus sources (gin, dry vermouth, lemon): check it isn't too bright." The nutty
  note (amaretto, maraschino) is outnumbered by the citrus.
- **S:** the citrus notice goes, with citrus back to gin and lemon. Sherry is the olive's
  strongest partner in the data (0.27, against 0.05 for dry vermouth), and novelty rises from
  0.048 to 0.065. A new notice: "3 nutty sources (sherry, amaretto, maraschino)". That's the
  support note amplified, but taste whether it crowds the olive. Caveat: Cobber's sherry is
  generic and provisional. It doesn't know Manzanilla is dry and briny, so its balance reading
  (a little sweeter than M1) is wrong; expect M1's sweetness.
- **M2:** no notices. The nutty note (amaretto, maraschino) is level with the citrus (gin,
  lemon).
- **B:** the nutty note rests on amaretto alone, against two citrus sources. B's score isn't
  trustworthy yet: Cobber has Bénédictine as vanilla only (provisional).
- **Olive (all four):** Cobber sees one olive source, because the brine, oil and garnish
  aren't separate entries yet (step 2 of the scoring upgrade). So its "the olive may not come
  through" is partly a data gap, and question 3 is the real test.
- **Strength:** M1 1.68, S 1.65, M2 1.47 and B 1.56 standard drinks (gin at 40%). Sugar and
  acid predictions come with step 3 of the scoring upgrade.

**Results:** to be filled in by Ari.

| | M1 | S | M2 | B |
|---|---|---|---|---|
| Verdict | | | | |
| Too bright? | | | | |
| Nutty note level with citrus? | | | | |
| Olive there? | | | | |
| Sweet / sour / strong | | | | |

**Menu pick and changes:**

**Next, on the winner (from the house specs):** brine at 5 / 7.5 / 10 ml, then olive oil at
5 against 10 ml. If the olive still hides, the next amplifier to try is a dash of celery
bitters (to buy), which carries the savoury note in the bitters slot.
