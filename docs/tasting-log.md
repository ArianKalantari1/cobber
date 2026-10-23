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

## Session 1 (planned): Olivia, one slot at a time

**Brief (Ari, 23 October):** olives with fruit. The current restaurant spec tastes of very
little olive, so it needs a little saltiness, nuttiness and fruit, with the olive forward.
Every version below has 7.5 ml of green olive brine for the salt (the restaurant spec has
none) and extra-virgin olive oil for texture. Each round changes one slot.

The house gin is the bar's gin, taken as 40% for strength maths until the label is in.
Standard drinks assume Manzanilla at 15%, apricot brandy at 24% and crème de pêche at 18%.

**Shared by every glass:** 20 ml lemon (17.5 in B), 7.5 ml green olive brine, 5 ml
extra-virgin olive oil and foamer. Reverse dry shake, double-strain into a chilled
150–180 ml coupe, then a green olive on a pick and one pump of olive oil mist.

### Control: the owner's original, as made

45 ml regular gin, 7.5 ml amaretto, 7.5 ml honey syrup, 10 ml lemon, 7.5 ml extra-virgin
olive oil and foamer, with a basil leaf on the foam. There's no brine. About 1.59 standard
drinks. Taste it next to every round, so each change is judged against what's served today.

**Cobber's prediction:** harmony 0.075 and novelty 0.042, the lowest of the session. The basil
leaf links only weakly to the rest (lemon 0.09, gin 0.09, olive 0.04): without it the original
scores 0.101. Every new version beats it by 0.024 to 0.044 on harmony and by 16% to 65% on
novelty. Two differences Cobber doesn't score but you will taste: it has no salt, and with
10 ml lemon against 15 ml of sweet it is gentler and more spirit-forward than the new
versions, which are full sours at 20 ml lemon.

### Round 1: what carries the olive best (the modifier)

| | M1: dry vermouth | S: Manzanilla | M2: no modifier |
|---|---|---|---|
| House gin | 30 ml | 30 ml | 30 ml |
| Modifier | French dry vermouth 15 ml | Manzanilla 15 ml | none |
| Amaretto | 15 ml | 15 ml | 15 ml |
| Maraschino | 7.5 ml | 7.5 ml | 7.5 ml |
| Vanilla syrup | none | none | 2.5 ml |
| Standard drinks | about 1.68 | about 1.65 | about 1.47 |

**Cobber's predictions** (from `score_drink`; the house gin scored as a generic London dry gin):
- **Aroma harmony:** M1 0.111, S 0.109, M2 0.102. That's within noise, so this round decides.
- **M1:** "3 citrus sources (gin, dry vermouth, lemon): check it isn't too bright." The vermouth
  is a third citrus carrier crowding the olive.
- **S:** the citrus notice goes, and sherry is the olive's strongest partner in the data (0.27,
  against 0.05 for dry vermouth). Manzanilla is dry, so the sugar and acid stay as in M1, and
  briny, so it carries the olive in the modifier slot. Cobber warns of three nutty sources
  (sherry, amaretto, maraschino): taste whether they cover the olive. Caveat: Cobber's sherry is
  generic and provisional. It doesn't know Manzanilla is dry and briny, so expect M1's sweetness
  whatever its balance reading says.
- **M2:** no notices. The nutty note (amaretto, maraschino) is level with the citrus.

### Round 2: which fruit with the olive (on the round 1 winner)

If S wins, swap the 7.5 ml of maraschino:

| | S (maraschino, cherry) | S-apricot | S-pêche |
|---|---|---|---|
| Fruit liqueur, 7.5 ml | maraschino | apricot brandy | crème de pêche |
| Standard drinks | about 1.65 | about 1.60 | about 1.56 |

**Cobber's predictions:**
- **Harmony:** 0.109, 0.105 and 0.099, a tie. With the Manzanilla in, none of the three gets a
  notice, because sherry and amaretto keep the nutty side level with the citrus.
- **Why stone fruit:** cherry, apricot and peach all share the almond-kernel note with
  amaretto (benzaldehyde), so the fruit and the nut tie together. In S-apricot the olive links
  to three partners (Manzanilla 0.23, amaretto 0.18, apricot 0.07).
- **If M2 wins instead,** swapping its maraschino for apricot or peach leaves amaretto alone
  against the citrus. In that case keep the maraschino.

### Round 3: does Bénédictine lift it (the winner against B)

B: 35 ml house gin, 10 ml amaretto, 7.5 ml Bénédictine, 2.5 ml vanilla syrup, plus the shared
items with 17.5 ml lemon. About 1.56 standard drinks.

**Cobber's prediction:** none worth trusting yet. Ari's case is that Bénédictine's herbs, honey
and saffron meet the olive's herbal side. Cobber's olive entry has no green or herbal
compounds (those belong to the olive oil, which isn't its own entry yet), and the proposed
Bénédictine bill (`data/backbar_proposal.json`) links to olive only weakly. Cobber can't see
this bridge, so this round is the palate's call.

### Results (Ari)

| | Original | M1 | S | M2 | S-apricot | S-pêche | B |
|---|---|---|---|---|---|---|---|
| Verdict | | | | | | | |
| Too bright? | | | | | | | |
| Nutty note level with citrus? | | | | | | | |
| Olive there? | | | | | | | |
| Fruit with the olive? | | | | | | | |
| Sweet / sour / strong | | | | | | | |

**Menu pick and changes:**

**Next, on the winner (from the house specs):** brine at 5 / 7.5 / 10 ml (more brine is the
first lever if the olive or salt still hides), then olive oil at 5 / 7.5 (the owner's dose) /
10 ml.
