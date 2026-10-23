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

**Brief (Ari, 23 October):** olives with fruit. Today's Olivia tastes of very little olive,
so it needs a little saltiness, nuttiness and fruit, with the olive forward. Every new version
adds 7.5 ml of green olive brine for the salt, which today's spec doesn't have. Each round
changes one slot. Fruit already on the menu is off limits: apricot (the apricot spicy
margarita), peach (Sangria Branco), apple, raspberry, passionfruit, pineapple, cassis and
grapefruit.

The house gin is the bar's gin, taken as 40% for strength maths until the label is in.
Standard drinks assume Manzanilla at 15%.

**Shared by every new glass:** 20 ml lemon (17.5 in B), 7.5 ml green olive brine, 7.5 ml
extra-virgin olive oil (Ari's dose) and foamer. Reverse dry shake, double-strain into a chilled
150–180 ml coupe, then a green olive on a pick and one pump of olive oil mist.

### Control: today's Olivia, as Ari makes it

45 ml olive-oil-washed gin, 7.5 ml amaretto, 15 ml honey syrup, 20 ml lemon, 7.5 ml extra-virgin
olive oil and foamer. There's no brine. About 1.59 standard drinks. Taste it next to every round,
so each change is judged against what's served today.

**Cobber's prediction:** harmony 0.101 and novelty 0.046. Amaretto is its only nutty source,
against two citrus (gin, lemon). For reference, the owner's original (45 regular gin, 7.5
amaretto, 7.5 honey syrup, 10 lemon, 7.5 olive oil, foamer, basil leaf) scores 0.075: it is
shorter and lighter, and the basil links only weakly to the rest.

### Ari's version (tasting 23 October)

40 ml house gin, 15 ml Manzanilla, 7.5 ml amaretto, 7.5 ml pear liqueur, 20 ml lemon, 7.5 ml
green olive brine, 7.5 ml extra-virgin olive oil and foamer. It's S-pear (round 2) with more gin
and half the amaretto. About 1.75 standard drinks, taking the pear liqueur as 25%.

**Cobber's prediction:** harmony 0.101 and novelty 0.068, with no notices. These are S-pear's
scores, because the bottles are the same and Cobber doesn't weigh doses yet (step 3 of the scoring
upgrade). Nutty has two sources (Manzanilla, amaretto), level with the two citrus (gin, lemon).

**Balance (arithmetic, not Cobber):**
- **Sugar:** about 4 g, from the amaretto and pear liqueur at about 0.25 g/ml each. The Manzanilla
  is dry.
- **Acid:** about 1.2 g, from the lemon.
- **Ratio:** about 3:1, against about 8:1 in today's spec (15 ml honey syrup plus the amaretto,
  about 10 g of sugar). Expect it much tarter and drier than today's.

If it's too tart, try these in order:
1. **7.5 ml honey syrup.** It's on the bar today and keeps the menu's honey. That makes about 8 g of
   sugar, around 7:1.
2. **7.5 ml house pear syrup,** once it's made. Same sweetness, with more pear.
3. **15 ml lemon,** if you'd rather keep it dry.

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
- **Aroma harmony:** M1 0.111, S 0.109, M2 0.102, against 0.101 for today's spec. That's
  within noise, so this round decides.
- **M1:** "3 citrus sources (gin, dry vermouth, lemon): check it isn't too bright." The vermouth
  is a third citrus carrier crowding the olive.
- **S:** the citrus notice goes, and sherry is the olive's strongest partner in the data (0.27,
  against 0.05 for dry vermouth). Manzanilla is dry, so the sugar and acid stay as in M1, and
  briny, so it carries the olive in the modifier slot. Cobber warns of three nutty sources
  (sherry, amaretto, maraschino): taste whether they cover the olive. Caveat: Cobber's sherry is
  generic and provisional, so expect M1's sweetness whatever its balance reading says.
- **M2:** no notices. The nutty note (amaretto, maraschino) is level with the citrus.

### Round 2: which fruit with the olive (on the round 1 winner)

If S wins, swap its 7.5 ml of maraschino for 7.5 ml of the bar's pear liqueur. It's the same
slot and the same format, so only the fruit changes:

| | S (maraschino, cherry) | S-pear |
|---|---|---|
| Fruit liqueur, 7.5 ml | maraschino | pear liqueur |
| Standard drinks | about 1.65 | about 1.6 (check the bottle's ABV) |

**Check the label** for the name, the ABV, and whether it's a sweet liqueur or a dry pear
eau-de-vie (Poire Williams). A dry eau-de-vie brings no sugar and counts as a second spirit,
which would change the balance.

**Backup: house pear syrup, made to last.** Use 10 ml in place of the liqueur.
- Macerate sliced ripe pears (Packham or Williams) in an equal weight of caster sugar
  overnight in the fridge, then strain.
- Per 500 ml of syrup, add 4–5 ml of the 10% potassium sorbate solution and 1 g of vitamin C
  (2 crushed 500 mg Blackmores tablets, or plain ascorbic acid powder) against browning.
- Check that the pH is 3.8 or below (add a little citric acid if not). Never add sodium
  benzoate with the vitamin C.
- Expect 3–4 weeks in the fridge, as with the strawberry shrub (untested).

**Cobber's predictions:**
- **S-pear:** harmony 0.101, novelty 0.068 (47% more novel than today's spec), no notices.
- **Why pear:** it links to amaretto through benzaldehyde, the almond-kernel note (0.23), and
  to the Manzanilla through β-damascenone (0.13). That ties fruit, nut and sherry together.
  Nothing else on the menu uses it, and it keeps the drink pale.
- **Caveat:** pear's link to the olive (0.25) rests mostly on cinnamaldehyde and menthone. Those
  are the same two unverified compounds behind the olive–amaretto link, so verifying the olive
  profile (step 2 of the scoring upgrade) will firm up or weaken both.
- **Fig, for a later round** (fresh figs from January, or a fig syrup). In Cobber's test fig
  scores 0.093 against pear's 0.101. It ties to amaretto and Manzanilla, but Cobber sees no
  fig–olive link, partly the same olive data gap. Fig and pear together trigger "3 fruity
  sources".
- **Other fruit:** grape scores higher, but Cobber's grape is its sherry data, so it can't be
  told apart from the Manzanilla. Cherry adds a third nutty source next to the Manzanilla.

### Round 3: does Bénédictine lift it (the winner against B)

B: 35 ml house gin, 10 ml amaretto, 7.5 ml Bénédictine, 2.5 ml vanilla syrup, plus the shared
items with 17.5 ml lemon. About 1.56 standard drinks.

**Cobber's prediction:** none worth trusting yet. Ari's case is that Bénédictine's herbs, honey
and saffron meet the olive's herbal side. Cobber's olive entry has no green or herbal
compounds (those belong to the olive oil, which isn't its own entry yet), and the proposed
Bénédictine bill (`data/backbar_proposal.json`) links to olive only weakly. Cobber can't see
this bridge, so this round is the palate's call.

### Results (Ari)

| | Today's | Ari's | M1 | S | M2 | S-pear | B |
|---|---|---|---|---|---|---|---|
| Verdict | | | | | | | |
| Too bright? | | | | | | | |
| Nutty note level with citrus? | | | | | | | |
| Olive there? | | | | | | | |
| Fruit with the olive? | | | | | | | |
| Sweet / sour / strong | | | | | | | |

**Menu pick and changes:**

**Next, on the winner (from the house specs):** brine at 5 / 7.5 / 10 ml (more brine is the
first lever if the olive or salt still hides), then olive oil at 5 / 7.5 (Ari's dose) / 10 ml.

---

## Session 2 (planned): Pisco Ma Chérie, the caramel against the fruit

**Brief (Ari, 23 October):** rework the drink by re-scoring it, and lay out the options. The
working, the options and the sources are in `docs/recipes/pisco-ma-cherie-rework.md`. The
question for this session is whether the caramel (now in three parts of the drink: the Medium,
the demerara and the Moro vinegar) sits under the strawberry or on top of it.

**Glasses** (single serves: 41 ml pisco, 18 ml Elegante Medium, 31 ml shrub, then 75 ml soda,
built as in the prep spec):
- **A:** today's spec.
- **B:** the same, with the white-sugar half shrub (500 g strawberries, 300 g white sugar, no
  demerara; the full recipe is in the rework doc).
- **C (if strawberry gum is in):** B with 0.5 g strawberry gum in the half shrub's maceration.

**Cobber's predictions** (on the sourced data in `data/pisco_sherry_proposal.json`, which isn't
applied yet):
- **A:** harmony 0.047. *"The target, fruity, has 2 sources against 3 sweet/creamy sources: it
  may not come through."* Expect the caramel on top of the strawberry.
- **B:** harmony 0.060, with no notices. Expect the strawberry first and a redder colour, with the
  toffee finish still there from the Medium and the Moro vinegar.
- **C:** harmony 0.059 and *"3 fruity sources"*. Expect the strawberry louder still. Check it
  doesn't read as cinnamon or eucalyptus.

### Results (Ari)

| | A | B | C |
|---|---|---|---|
| Verdict | | | |
| Strawberry first? | | | |
| Caramel under the fruit or on top? | | | |
| Can you name the pisco? | | | |
| Colour | | | |
| Sweet / sour / strong | | | |

**Pick and changes:**
