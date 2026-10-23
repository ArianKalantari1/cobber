# House specs

Service, batch, and prep specs for house drinks worked on with Cobber.
The engine suggested the flavour bridges; the amounts are bartender judgement.
None of it has been taste-tested yet unless a section says so.

---

## Olivia (venue owner's signature)

**On the menu now:** Olive Oil Washed Gin, Amaretto, Honey, Lemon.
**The owner's original:** 45 regular gin · 7.5 amaretto · 7.5 honey syrup · 10 lemon ·
7.5 ml extra-virgin olive oil · foamer, with a basil leaf on the foam. It comes out short
and light on flavour.
**As Ari makes it now:** 45 olive-oil-washed gin · 7.5 amaretto · 15 honey syrup · 20 lemon ·
7.5 ml extra-virgin olive oil · foamer. That gives more volume and more flavour. There's no
brine, so no salt, and the shaken oil gives a thick foam but very little olive flavour.

**Where it's going:** a nutty, savoury, bright gin sour with the olive forward.
The changes so far:

- **No gin wash.** Plain house gin. The wash is too much work, and the olive now
  comes from brine, oil and the garnish.
- **No basil.** Drops of basil oil sank through the foam and you couldn't smell
  them. Basil is out of the drink.
- **Green olive brine for the olive.** It replaces the saline: no salt and no
  saline once the brine is in. Brine brings the olive itself, which is what guests
  recognise, not olive oil.
- **One more fruit next to the amaretto.** Maraschino or fresh pear (23 October),
  never both. Apricot is taken (the apricot spicy margarita), and peach is already in
  the Sangria Branco.
- **Less gin (30 ml).** 45 ml of gin with the liqueurs came to about 2.2 standard
  drinks. At 30 ml it is about 1.6–1.7.
- **No orange bitters.** They made no difference in any scoring.

### Testing versions (per serve)

| | M1: maraschino + vermouth | M2: maraschino + vanilla | P: pêche + vanilla |
|---|---|---|---|
| Cobber (corrected) | 0.111 | 0.111 | 0.105 |
| Style | drier, longer | softer, close to the Oliveto | the peach option |
| House gin | 30 ml | 30 ml | 30 ml |
| French dry vermouth | 15 ml | none | none |
| Amaretto | 15 ml | 15 ml | 15 ml |
| Maraschino | 7.5 ml (don't go higher) | 7.5 ml | none |
| Crème de pêche | none | none | 10 ml |
| Vanilla syrup | none | 2.5 ml | 2.5 ml |
| Green olive brine | 7.5 ml | 7.5 ml | 7.5 ml |
| **Batch pour** | **75 ml** | **62.5 ml** | **65 ml** |

For the current tasting plan, with S (Manzanilla) and S-pear, see `docs/tasting-log.md`.

**Service (all versions):** batch pour + 20 ml lemon + foamer + 7.5 ml extra-virgin
olive oil (Ari's dose). Reverse dry shake, double-strain into a chilled 150–180 ml coupe.
Garnish with a green olive on a pick across the rim and 1 pump of extra-virgin
olive oil from an oil mister (e.g. the Cuisine::Pro Savor Oil Mister,
Woolworths).

**Tasting order:**
1. M1 against M2 (drier with vermouth, or softer with vanilla). Bring in P only
   if you'd rather have peach than maraschino. Make single serves; don't batch yet.
2. Brine on the winner: 7.5 ml for Castelvetrano brine, 5 ml for ordinary green
   olive brine (it's saltier). Go up by taste. If it tastes flat, add more brine,
   not salt.
3. Olive oil on the winner: 5, 7.5 (Ari's dose) and 10 ml.

### Batch (the winner only)

| | M1 (9 serves, 675 ml) | M2 (10 serves, 625 ml) | P (10 serves, 650 ml) |
|---|---|---|---|
| House gin | 270 | 300 | 300 |
| French dry vermouth | 135 | none | none |
| Amaretto | 135 | 150 | 150 |
| Maraschino | 67.5 | 75 | none |
| Crème de pêche | none | none | 100 |
| Vanilla syrup | none | 25 | 25 |
| Green olive brine, coffee-filtered | 67.5 | 75 | 75 |
| Keeps | about a week (the vermouth) | weeks | weeks |

Change the brine line once the dose is set. Use one brand of brine (or mix
several jars together) so the salt stays the same. Shake the bottle before
pouring. **Never put olive oil in the batch:** it floats, pours unevenly and
clouds in the cool room.

**Menu line:** the wash is gone, so it needs rewriting, e.g. *Gin, Olive,
Amaretto, Maraschino, Lemon*.

### How Cobber scored it (and the three mistakes to avoid)

The "corrected" scores above are prototype numbers from 22 October. Cobber's counting has
since been fixed (`docs/todo-scoring-upgrade.md`). For current scores of every version, Ari's
current spec (0.101) and the owner's original (0.075), see `docs/tasting-log.md`.

1. **Citrus is not a bridge.** The house gin is very citrus-forward. Cobber's gin,
   limoncello, lemon, lime and dry vermouth all carry lemon compounds, so raw
   harmony rewards citrus on citrus. That is why limoncello first looked good
   (0.198 → 0.302) and then fell to the bottom once citrus was ignored.
2. **No duplicates, and nothing already inside another ingredient.** Amaretto and
   almond are the same profile in Cobber. Orgeat is a subset of amaretto. Coriander
   seed is a gin botanical.
3. **Stop when it stops being Olivia.** Maximising average harmony pulls the drink
   toward whatever links to amaretto (brandy, coffee). Gin stays the only base
   spirit, and nothing dark goes in.

Under these rules, olive's only real partner is amaretto (0.18). Maraschino and
crème de pêche are the bottles on the bar that link to both olive and amaretto.
Manzanilla is the best olive match (0.27), but it lowered the whole drink;
Cobber's sherry is generic, so it's still worth one taste. The loop scripts are
not in the repo.

### Precedents
- **Oliveto** (Pip Hanson, Marvel Bar, Minneapolis, around 2011): a gin sour with
  Licor 43, extra-virgin olive oil and egg white. It's the family's best-known
  drink. Its vanilla matches the M2 and P versions.
- **"The Olivia"** (a published home recipe on Finding Time for Cooking): gin,
  amaretto, honey, lemon, olive oil and egg white. It's almost the original Olivia,
  with the same name, which is one more reason to move on.
- **Olive brine with lemon:** Olive Sour (Great British Chefs), Safe Passage
  (Essex, Seattle: 7.5 ml Castelvetrano brine).
- Neither Cobber's recipe data nor a web search found olive paired with amaretto,
  maraschino or peach. The direction looks new.

---

## Orient Espresso (espresso-martini twist; working name was Carajillo Amer)

**Idea:** a bittersweet espresso martini made only from stock already on hand.
No cream, no egg; the espresso makes the foam.

**What Cobber found:** two rounds of 10 refinement loops. Adding Mr Black was
the biggest gain (harmony 0.212 → 0.283). Averna won every bitter slot
(0.283, against 0.186 for Montenegro and 0.180 for Fernet). Brandy was the
best base (0.283; rye 0.263, bourbon 0.258, vodka 0.180).

| Per drink | ×11 (700 ml bottle) | |
|---|---|---|
| 25 ml | 275 ml | VS brandy |
| 15 ml | 165 ml | Mr Black |
| 10 ml | 110 ml | Averna |
| 10 ml | 110 ml | Licor 43 |
| 2 drops | about 1 ml | saline (20%) |

**Service:** 60 ml batch + 35 ml fresh espresso. Shake hard for 12–15 s,
fine-strain into a chilled coupe, garnish with a dehydrated orange wheel.
About 95 ml goes into the tin, giving about 119 ml in the glass at about
16.6% ABV (about 1.6 standard drinks) and about 8.5 g sugar per 100 ml. The
batch is shelf-stable.

Brandy went up to 25 and Averna down to 10 at Ari's call. The orange stays
dried, not a fresh expressed zest: in Cobber, fresh orange oil drops harmony
from 0.424 to 0.302. If the drink tastes too dry, take Licor 43 to 12.5
(about 9.1 g sugar per 100 ml). On aroma alone Averna is close to neutral
(0.424 with it, 0.444 without), so whether to keep it is a taste call (test
it at 10 ml against none).

**Sugar and ABV data used:** Mr Black 25% / 25.1 g per 100 ml (producer FAQ);
Averna 29% / 23 g per 100 ml (label data); Licor 43 31% / about 40 g per
100 ml (worked out from the label's calories, so unverified).

**Coffee-tequila (Mexican) edition, to clear stock:** if it is a dry
flavoured tequila, swap it 1:1 for the brandy. If it is a sweet liqueur, use
25 coffee tequila · 10 Mr Black · 10 Averna · 5 Licor 43 · 35 espresso ·
saline. The brand is still to be confirmed.

**More vanilla without more sugar:** 2 dashes of vanilla tincture, not more
Licor 43.

**Chocolate bitters (still to test):** Cobber has no cocoa ingredient, so I
scored a provisional proxy made of cocoa's key odorants that are in its
vocabulary (pyrazine, 2-acetylpyrrole, phenylacetaldehyde, furaneol, linalool,
vanillin, ethyl 2-methylbutyrate). The proxy is not in the data.

| Version | Harmony |
|---|---|
| Current spec | 0.424 |
| + 2 dashes cocoa bitters | 0.334 |
| Cocoa bitters in place of Averna | 0.326 |
| Mole (spiced) bitters | 0.329 |

The drop reflects the proxy's limits more than a real clash: Cobber is
missing most of the roast compounds that coffee and cocoa share. Use cocoa
bitters as an accent (2 dashes, or drops on the foam), never as a
replacement for Averna, and choose plain cocoa over mole-style.

---

## Summer Fling: apricot purée (simplified)

**Build:** three things go into the tin: the batch (tequila, agave, mezcal,
Floc de Gascogne and apricot liqueur), the apricot purée, and lime juice.

**Problem:** canned apricot in its full syrup tasted flat, and the apricot
didn't come through.

**Fix:** the apricot liqueur in the batch carries the apricot intensity, so
the purée stays simple: canned fruit, half the syrup, a fresh-fruit acid
blend and salt. No dried apricot, no cooking, no agave, no sieve (the
texture is like a frozen margarita). Generous acid because the starting pH of
the canned fruit is unknown; the lime in the tin is set by taste to match.

**One 825 g can, makes about 600–650 ml:**

| Ingredient | Amount | Why |
|---|---|---|
| Canned apricot halves | all of the fruit (about 480 g) | body and flavour |
| Can syrup | about 170 g (roughly half): drain all the syrup into a jug, put the blender jug on the scale and pour 170 g back in (150–200 g is fine); discard the rest | less sugar, more apricot |
| Malic acid | 6 g | apricot's own main acid, which tastes like fresh fruit |
| Citric acid | 3 g | brightness, and a lower pH (aim for 3.5 or below; check with cheap pH strips) |
| Vitamin C, optional | 1 g = 2 crushed 500 mg tablets (Blackmores Vitamin C 500 is unflavoured; Cenovis Sugarless C, the orange chewable, also works here) | stops browning. Make the first batch without it: the fruit is already heat-treated, the acid slows browning, and many cans already list antioxidant 300. Add it next time only if the purée looks duller or browner than fresh by day 3–5. Tablet binders can leave a faint haze, so crush them fine; plain ascorbic acid powder is cleanest |
| Salt | 1 g | lifts the fruit |
| Potassium sorbate | 5 ml of a 10% solution (= 0.5 g; recalculate if your solution is a different strength) | yeast and mould control; roughly doubles fridge life |
| Monin peach purée, optional | 30 ml | makes the apricot read riper (harmony 0.36). Skip it while the apricot liqueur is in the batch; use it if you drop the liqueur |

**Method:** blend everything on high for about 1 min. Canned apricots are
soft, so it blends quickly. No sieve. Use a wide-tip squeeze bottle or a pour
jug, and label and date it (note "contains preservative 202" if you use
sorbate). Never add sodium benzoate alongside the vitamin C.

**Storage and label:** "Made [date] · Use by [date + 10 days]". 10 days is the
cautious end of the 10–14 days sorbate gives; it hasn't been lab-tested.
Without sorbate it's 5 days. During service, keep it in the esky with the bottle
in ice up to its neck (not resting on top), top up the ice through the shift,
and put it back in the fridge at close. If the ice has gone and the bottle
feels warm, don't keep it past that shift. Throw it out if it fizzes, smells
yeasty or boozy, or grows mould.

**Freezing (once weekly sales are known):** make big batches, freeze flat in
Ziploc bags sized to service (e.g. 300 ml = 10 drinks), and label them
"apricot purée" with the date. They keep 2–3 months frozen. Thaw in the
fridge and never refreeze. Freezing pauses the clock but doesn't reset it:
fridge days before freezing plus after thawing count toward the same 10
days (5 without sorbate). Freeze on the day you make it. Cans per week = drinks
sold ÷ 20.

**Apricot liqueur in the batch:** it brings sugar as well as apricot, so for
every 10 ml of apricot liqueur per drink, take about 3 ml of agave out of the
batch.

**Service:** 30 ml purée per drink, single-strain with a Hawthorne strainer
only, and scrape the jigger.

### Summer Fling batch

Pour **60 ml** of batch per drink (a fixed 60 ml jigger stops over-pouring).
That keeps the same ratio as 35 tequila : 10 mezcal : 15 Floc : 5 apricot
liqueur : 5 agave, at about 14% less spirit cost per drink than a 70 ml pour.

| What's in each 60 ml pour | 700 ml bottle (11 pours) | |
|---|---|---|
| 30 ml | 330 ml | blanco tequila |
| 8.5 ml | 95 ml | mezcal |
| 13 ml | 140 ml | Floc de Gascogne |
| 4.25 ml | 47.5 ml | apricot liqueur |
| 4.25 ml | 47.5 ml | agave nectar, straight (95 ml if your agave is cut 1:1) |
| **60 ml** | **660 ml** | |

**Into the tin:** 60 ml batch + 30 ml apricot purée + 15 ml lime. The purée
now has a fixed 9 g of acid per can (6 malic + 3 citric), which works out to 15 ml
lime; fine-tune by taste. Shake hard and short (6–8 s; the ice in the glass does
the rest of the dilution) and single-strain (Hawthorne only) over fresh
cubed ice in a rocks glass.

**The drink (estimated):** 110 ml into the tin gives about 134 ml in the glass
at about 14% ABV (about 1.5 standard drinks), with about 9.3 g sugar per
100 ml and about 1.1% acid. The batch is about 31% ABV, so it is
shelf-stable. Floc's fresh grape notes fade, so make bottles to last about
1–2 weeks and keep them in the cool room overnight.

**Why 13 ml of Floc:** at around 17% ABV it is gentle, and at 5–7 ml its
honey and stone-fruit notes disappear behind the tequila, smoke, lime and
purée. It also does double duty as part of the sweetener, which is why the
agave is so small. If it reads too strong, go to 10 ml Floc and add 2.5 ml
tequila and 1 ml agave per pour. Cobber can't score Floc (it is not in the
data), so this comes from bartending judgement and the sugar maths.

**Without apricot liqueur (test):** replace its 47.5 ml in the bottle with
tequila; the drink comes out a touch drier. If the apricot fades, add 30 ml
of Monin peach to the purée batch.

**Why these numbers:** Floc, apricot liqueur and the purée all bring sugar,
so the agave stays small. The old build (45 tequila + 10 agave + purée +
lime) worked out at about 11.8 g sugar per 100 ml; this one is drier and
more layered, with smoke from the mezcal and honey from the Floc.

**Options:** without apricot liqueur, put 30 ml of Monin peach in the purée
batch instead (about 8.8 g sugar per 100 ml, slightly drier). Tune the agave
in 2.5 ml steps: 7.5 ml gives about 10.9 g sugar per 100 ml. The sugar
figures for Floc (about 15 g/100 ml), apricot liqueur (about 28 g/100 ml) and
the purée (about 16 g/100 ml) are estimates, so check the bottle labels.

---

## Pisco Ma Chérie (spec as supplied by Ari)

### 1. Strawberry shrub (about 1.1 L, enough for 4 rail bottles)

**The day before (5 min):** put these in a lidded tub in the cool room for
24 h, stirring once if you pass.

| Ingredient | Amount |
|---|---|
| Frozen strawberries | 1 kg |
| White sugar | 400 g |
| Demerara sugar | 200 g |
| Black peppercorns, coarsely cracked (not ground) | 3 g |

**Prep day (15 min):** strain through a sieve, pressing lightly (about 1 L of
syrup). Throw out the pulp and pepper. Whisk these in until dissolved:

| Ingredient | Amount |
|---|---|
| Vinegar (pick one, below) | 120 ml |
| Citric acid | 21 g |
| Malic acid | 7 g |
| Salt | 1.5 g |
| Potassium sorbate, optional | 5 ml of a 10% solution (= 0.5 g) |

**Vinegar options:**
- **FORVM Chardonnay vinegar** is the default. It's clean and fruity and lets the
  strawberry lead.
- **Sherry vinegar from Woolworths** (Ari thinks the brand is Moro) is nuttier and
  woodier, and links to the Elegante sherry in the batch. It can push the shrub
  slightly savoury and darken the colour.
- **A 60/60 split** gets some of each.
- **Check the acidity %** on both labels. If the sherry vinegar is stronger, start
  at 100 ml and top up by taste.

**Sorbate** backs up the untested 3–4 week fridge life. Skip it if a batch is
always finished within about 2 weeks.

**Taste check:** 15 ml shrub with 45 ml cold soda. If it tastes flat, add 3 g
citric and 1 g malic and taste again (at most twice). It should taste like a
bright strawberry soda, with no sharp prickle in the nose. Bottle it full to
the top, label and date it, and rest it in the fridge for 2 days before
batching.

**Keeps:** about 3–4 weeks in the fridge without sorbate (untested; freeze half
on day 0 if it's selling slowly). Throw it out if it fizzes or hisses when
opened, grows a film, or smells yeasty or boozy.

### 2. Batch (per 700 ml rail bottle)

| Ingredient | Amount |
|---|---|
| Pisco | 320 ml |
| Elegante Medium sherry (Summer Hill Wine Shop) | 140 ml |
| Strawberry shrub | 240 ml |

Exactly 700 ml at about 22% ABV, with no water added. One shrub batch makes 4
rail bottles, with about 140 ml of shrub to spare. Best within about 2 weeks;
colour and fresh aroma fade first. Keep the drum dark in the cool room, fill
the rail bottle with one or two shifts' worth at a time, and never pour warm
leftovers back into the drum.

### 3. Service

Fill a highball to the top with cubes. Pour 90 ml of batch (a 60 and a 30
jigger), shaking the bottle first if it has settled. Give it 3–4 spins with
the bar spoon, then pour 75 ml cold soda (or Purezza sparkling) down the spoon
and lift once. Garnish with a dehydrated orange wheel stood against the inside
of the glass, plus one twist of black pepper over the top.

**Finished drink:** about 190 ml, 10.2% ABV, 1.54 standard drinks. Each rail
bottle gives 7 full pours.

**Checked:** the maths holds. Pisco at 40–42% plus the sherry gives 21–22% ABV
in the batch, and 90 ml of batch with 75 ml soda and stirring melt comes to
about 190 ml at about 10%. Estimated sugar is about 9.7 g per 100 ml in the
glass, which suits a highball. The dehydrated orange wheel is shared with
Orient Espresso, so it is one prep for two drinks.

---

## Watermelon Reviver preps (A Refreshing Indulgence)

### Watermelon concentrate cordial (freeze-concentrated H2melon, about 550 ml)

The point is concentration: plain bottled juice gets lost in the drink. Freeze
1 L of H2melon and slowly thaw it upside down. The first melt carries most of
the sugar, flavour and colour, so keep the first 500 ml and discard the pale
ice.

**Step 1: freeze-concentrate (1 L → 500 ml)**

1. Freeze the 1 L of H2melon solid (about 24 h). If it is still in its
   plastic bottle, pour off a splash first, because it expands.
2. Turn it upside down over a jug (a funnel or sieve helps) in the cool room,
   never at room temperature.
3. Collect the melt until you have **500 ml**, measured on the jug (no
   refractometer needed; the drips also turn pale near the end). Discard the
   pale ice left behind.
4. Timing: in a cool room at 2–4 °C, expect roughly **12–20 h**. The earlier
   6–10 h figure was an optimistic estimate, and nothing here has been timed yet.
   Start it at close and check it in the morning. Cutting the bottle off and
   setting the bare block in a sieve over the jug speeds it up.

**Step 2: cordial (no added sugar except the optional rose syrup)**

| Ingredient | Per 500 ml concentrate | Why |
|---|---|---|
| Watermelon concentrate | 500 ml | base |
| Citric acid | 4 g | brightness; replaces most of the lemon |
| Malic acid | 2 g | rounder, fresh-fruit sourness |
| Salt | 0.5 g | lifts the watermelon |
| Potassium sorbate | 4 ml of a 10% solution (= 0.4 g, about 0.08%) | needed: the juice has little preservative and the concentrate is low in sugar |
| Rose syrup, optional | 50 ml | puts the pink and the drink's rose note in this one bottle, so there's no separate rose syrup at service. Leave it out if you'd rather control the rose per drink |
| Vitamin C, optional | 1 crushed Blackmores Vitamin C 500 mg tablet (unflavoured; not the orange Cenovis chewable, whose flavour, sweetener and orange colour would show here) | small help holding the watermelon colour (opaque bottles and cold matter more). **Skip it if you use the hibiscus shot:** ascorbic acid speeds up the fading of hibiscus red |

**Method:** stir everything into the cold concentrate until dissolved, adding
the sorbate solution last. Check that the pH is 3.8 or below. Fill opaque
bottles to the top and label "contains preservative 202" with the date. Keep
it in the fridge for about 7–10 days (untested, and low in sugar, so check it
before each service), or freeze portions.

**If the colour is pale: hibiscus.** Watermelon and hibiscus is a classic
pairing (Mexican agua fresca de jamaica y sandía). Hibiscus brings a deep red
and a tart, cranberry-like edge. Its anthocyanin pigments stay bright red at
low pH, and this cordial is acidified to about 3.5, so the colour holds well.
Make a small colouring shot rather than steeping into the cordial: 2 g dried
hibiscus (or one hibiscus–rooibos tea bag) in 30 ml just-boiled water for
5 min, then strain and cool. Add it to the cordial a few ml at a time until
the colour is right. Hibiscus is tart, so taste before adding all the citric
acid. Pure dried hibiscus (flor de jamaica) is better than the rooibos blend:
rooibos adds woody, honey notes and a brick-brown tint that can dull the pink.
At a few ml per 500 ml, though, the blend won't take over. Cobber can't score
this pairing, since neither watermelon nor hibiscus is in its data.

**Use:** a decent pour of 45–60 ml per drink (not 20–25 ml) so the watermelon
shows. At 45 ml the cordial's acid equals about 9 ml of lemon, so cut the
lemon to match. If the rose syrup is in the cordial, drop it at service.

### Watermelon Reviver: proposed build (from 7 items in the tin down to 3)

I don't have the current amounts; this is a consolidated proposal.

| Into the tin | Amount | |
|---|---|---|
| **Batch** | 54.5 ml | cucumber rum 30 + Lillet Rosé 15 + Cointreau 7.5 + absinthe 2 |
| **Watermelon–rose cordial** | 45 ml | concentrate, with the rose syrup inside |
| **Lemon** | 10 ml | |
| **Total** | **about 110 ml** | |

Shake hard. You get about 134 ml at about 14% ABV (about 1.5 standard drinks),
with an estimated 7.7 g sugar per 100 ml and 0.9% acid. With 60 ml cordial and
7.5 ml lemon: about 149 ml at 12.6%, still balanced but a bigger drink.

**Batch per 700 ml bottle (12 pours of 54.5 ml):** cucumber rum 385 ml, Lillet
Rosé 193 ml, Cointreau 96 ml, absinthe 26 ml. Keep it in the fridge (it has
fresh cucumber and an aromatised wine in it) and use within about 1–2 weeks.

### Cucumber-infused rum (700 ml)

| Ingredient | Amount |
|---|---|
| White rum | 700 ml |
| Cucumber (1 telegraph or 2 Lebanese), peel striped | 250 g |

**Quick method (recommended):** chop the cucumber, blend with the rum for
20–30 s, rest 20 min, then strain through a fine sieve and a coffee filter.
Ready in about an hour, and bright green. **Slow method:** slice thin and
infuse in the fridge for 12–24 h, then strain. **Storage:** fridge, amber
bottle, use within 2 weeks; the fresh cucumber note fades and can turn
pickle-like.

---

## Open tests
- Olivia: M1 against M2 (P only if peach is preferred); then brine dose (5 / 7.5 / 10 ml)
  and olive oil (5 against 10 ml) on the winner. See the Olivia section.
- Orient Espresso: blind head-to-head against the current espresso martini;
  Averna at 10 ml against none; sweetness (as specced against vanilla
  tincture against Licor 43 at 12.5); foam hold at 5 min; batch on day 1
  against day 7; service speed; a 2-week soft launch; cocoa bitters (none
  against 2 dashes in the shake against 3 drops on the foam).
