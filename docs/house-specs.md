# House specs

Service, batch, and prep specs for house drinks worked on with Cobber.
The engine suggested the flavour bridges; the amounts are bartender judgement.
None of it has been taste-tested yet unless a section says so.

---

## Olivia (venue owner's signature)

**On the menu now:** Olive Oil Washed Gin, Amaretto, Honey, Lemon.
**As made in practice:** 45 washed gin · 7.5 amaretto · 15 honey syrup · 20 lemon ·
5 ml extra-virgin olive oil · foamer. The shaken oil gives a thick foam, but very
little olive flavour.

**Where it's going:** a nutty, savoury, bright gin sour with the olive forward.
The changes so far:

- **No gin wash.** Plain house gin. The wash is too much work, and the olive now
  comes from brine, oil and the garnish.
- **No basil.** Drops of basil oil sank through the foam and you couldn't smell
  them. Basil is out of the drink.
- **Green olive brine for the olive.** It replaces the saline: no salt and no
  saline once the brine is in. Brine brings the olive itself, which is what guests
  recognise, not olive oil.
- **One more liqueur next to the amaretto.** Maraschino or crème de pêche,
  never both.
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

**Service (all versions):** batch pour + 20 ml lemon + foamer + 5 ml extra-virgin
olive oil. Reverse dry shake, double-strain into a chilled 150–180 ml coupe.
Garnish with a green olive on a pick across the rim and 1 pump of extra-virgin
olive oil from an oil mister (e.g. the Cuisine::Pro Savor Oil Mister,
Woolworths).

**Tasting order:**
1. M1 against M2 (drier with vermouth, or softer with vanilla). Bring in P only
   if you'd rather have peach than maraschino. Make single serves; don't batch yet.
2. Brine on the winner: 7.5 ml for Castelvetrano brine, 5 ml for ordinary green
   olive brine (it's saltier). Go up by taste. If it tastes flat, add more brine,
   not salt.
3. Olive oil on the winner: 5 ml against 10 ml.

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

The "corrected" scores above leave out redundant matches, so they sit lower than
the early numbers (the current restaurant spec scores 0.072 on this scale).

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

---

## Tasting log

### 27 October 2026 (Ari, served to guests)

| Drink | Verdict | Next test |
|---|---|---|
| **Orient Espresso** | Too much coffee, too strong, not special enough. | **Rebuild, no Mr Black; the coffee comes only from the espresso.** Per serve: 30 VS brandy · 15 Pedro Ximénez sherry · 10 Licor 43 · 2 drops saline + 30 espresso, shaken, coupe, dehydrated orange wheel. Batch, 12 serves: 360 brandy · 180 PX · 120 Licor 43 · 1 ml saline; pour 55 ml. About 1.4 standard drinks. Too sweet: PX to 10 ml. Fallback (smallest change): the old spec without Mr Black, i.e. 30 brandy · 10 Averna · 10 Licor 43 + 30 espresso. |
| **Pisco Ma Chérie** | Very good. More sherry would help. | Per serve: 35 pisco · 25 Elegante Medium · 30 shrub · 75 soda. Batch per 700 ml: 270 pisco · 195 sherry · 235 shrub. |
| **Watermelon Reviver** (R&D sheet version B) | Too syrupy. | Rose watermelon cordial 30 → 22.5 ml, lemon unchanged. If it's still sweet, curaçao 10 → 7.5 ml. Spec: `docs/recipes/spring-signatures-rnd.md`. |
| **Cherry cobbler** (layers: vodka, sweet vermouth, Aperol) | Shaken with lemon and bitters: not nice, probably too much lemon. **Built: bang on, guests loved it.** | Make the built serve the default: muddle an orange slice and a lemon slice with a little lemon juice, add the batch, fill with cubes. Optional Coca-Cola top. Write down the lemon juice amount next time. Spec: `docs/recipes/rescued-red-wine-cobblers.md`. |

### Orient Espresso: round 2 tasting plan (27 October 2026)

All three use VS brandy and 25 ml espresso, shaken, fine-strained, chilled coupe. Keep the
brandy, coffee, dilution and temperature the same, and score each 1–5 for coffee clarity, brandy
visibility, sweetness, finish and "want another sip".

| | A: Nightcap-style | B: Black Forest | C: Salted caramel |
|---|---|---|---|
| Inspired by | Blue Nightcap (Vito Nicotra, 2015: Cognac, amontillado, PX, espresso, honey, walnut bitters) | Matriarch Martini (Haley Traub, 2024: cherry and espresso, no coffee liqueur) | House burnt-sugar technique (La Pasión R&D) |
| Brandy | 35 ml | 30 ml | 35 ml |
| Second element | 25 ml Elegante Medium sherry (stands in for amontillado + PX in one bottle) | 25 ml cherry cobbler batch | 15 ml salted burnt-sugar syrup |
| Accent | 2.5 ml honey syrup · 1 dash walnut bitters, if the bar's walnut is bitters | optional 5 ml crème de cacao | none |
| Std drinks (approx.) | 1.45 | 1.3 | 1.1 |

Parked: prune–Armagnac (new bottle plus prep), brown-butter-washed brandy (Ari doesn't want washes),
Massenez Popcorn (Pop Star Martini owns it).

## Me.. Espresso: idea bank (27 October 2026)

Brief: lighter and enjoyable, not too boozy (about 1.1–1.4 standard drinks, against 1.75 for
the house Espresso Martini of 45 vodka + 20 Kahlúa). Coffee comes from 30 ml espresso only; no
coffee liqueur. Shake hard 12–15 s, fine-strain, chilled coupe. "Coffee link" is Cobber's
strongest score between that flavour and coffee (shared compounds or recipe tradition). Liqueur
strengths are typical values: check the labels.

| # | Idea | Stack | Spec (ml) | Std drinks | Coffee link | Stock |
|---|---|---|---|---|---|---|
| 1 | Me.. Espresso (juice) | white rum · pineapple · almond | 40 white rum · 20 pineapple juice · 10 orgeat · 2 drops saline | 1.25 | pineapple 0.26, almond 0.41 | bar |
| 2 | Me.. Espresso (liqueur) | rum · pineapple liqueur · a little juice for foam | 30 white rum · 15 pineapple liqueur (e.g. Giffard Caribbean Pineapple) · 10 pineapple juice · 5 orgeat | 1.25 | pineapple–rum 0.75 | buy liqueur |
| 3 | Me.. Espresso (pineapple rum) | pineapple rum · pineapple · almond | 40 pineapple rum (e.g. Plantation Stiggins' Fancy) · 15 pineapple juice · 7.5 orgeat | 1.25 | as above | buy rum |
| 4 | Jaffa | vodka · white cacao · orange | 30 vodka · 15 white crème de cacao · 5 Cointreau, orange zest | 1.4 | orange 0.46, cacao 0.32 | buy cacao |
| 5 | Wattleseed | rum or brandy · roasted wattleseed · cacao | 35 spiced rum or brandy · 10 wattleseed–demerara syrup · 5 crème de cacao | 1.2 | wattleseed 0.40 | buy wattleseed |
| 6 | Noisette | brandy · hazelnut · salt | 30 brandy · 15 Frangelico · 2 drops saline | 1.2 | not in Cobber | buy Frangelico |
| 7 | Raspberry truffle | vodka · raspberry · white cacao | 30 vodka · 10 Chambord · 10 white crème de cacao | 1.25 | raspberry 0.23, cacao 0.32 | Chambord on bar |
| 8 | Banana & salt | spiced rum · banana · salt | 30 spiced rum · 15 banana liqueur (e.g. Giffard Banane du Brésil) · 2 drops saline | 1.25 | not in Cobber | buy liqueur |
| 9 | Qahwa | vodka or brandy · cardamom · honey | 40 vodka or brandy · 10 cardamom–honey syrup, optional 2 drops rosewater | 1.25 | cardamom 0.18, honey 0.26 | buy cardamom |
| 10 | Café Romano | vodka · anise accent | 35 vodka · 5 sambuca · 5 demerara syrup, 3 coffee beans | 1.25 | anise 0.26 | buy sambuca |
| 11 | Irish cream float | Irish whiskey · demerara · cream | 40 Irish whiskey · 10 demerara syrup, 15 lightly whipped cream floated on top | 1.25 | cream 0.67 | buy whiskey |
| 12 | Smoked Cherry (light) | mezcal · cherry · maraschino | 25 mezcal · 20 cherry cobbler batch · 5 maraschino | 1.2 | cherry 0.12 (agave–cherry 0.60) | bar |
| 13 | Highland (light) | scotch · Averna · honey | 30 blended scotch · 10 Averna · 5 honey syrup | 1.2 | scotch–Averna 0.54 | bar |
| 14 | Normandy | brandy · Pommeau · honey | 25 brandy · 20 Pommeau · 7.5 honey syrup | 1.1 | apple 0.12, honey 0.26 | bar |
| 15 | Pera Negra (light) | tequila · pear · maraschino | 35 blanco tequila · 10 pear liqueur · 5 maraschino | 1.4 | pear 0.12 | bar |

All amounts are per serve plus 30 ml espresso. Syrups: wattleseed (10 g roasted ground
wattleseed steeped 20 min in 250 ml hot 1:1 syrup, coffee-filtered) and cardamom–honey (10 crushed
pods simmered 5 min in 250 ml 1:1 honey syrup, strained). Both keep 2–3 weeks in the fridge.

### Banana & salt family (27 October 2026)

Ari's favourite from the idea bank. Banana isn't in Cobber's data (it's on the unmatched list),
so these are bar judgement. Each is about 1.1–1.35 standard drinks, plus 30 ml espresso, shaken
and fine-strained into a chilled coupe. Banana liqueur means e.g. Giffard Banane du Brésil.

| Idea | Spec (ml) | Salt | Garnish |
|---|---|---|---|
| Salted Banana (core) | 30 aged rum · 15 banana liqueur · 5 salted burnt-sugar syrup | in the syrup | a few flakes of sea salt on the foam |
| Café Foster (Bananas Foster, New Orleans) | 30 spiced rum · 15 banana liqueur · 5 cinnamon–brown-sugar syrup | 2 drops saline | brûléed banana coin |
| Banana Bread | 30 bourbon · 15 banana liqueur · 5 demerara syrup · 1 dash walnut bitters | 2 drops saline | grated nutmeg |
| Smoky Plátano | 25 mezcal · 15 banana liqueur · 5 demerara syrup | smoked salt flakes on top | none |
| Choc-Banana | 30 white rum or vodka · 10 banana liqueur · 10 white crème de cacao | 2 drops saline | cacao dust on half |
| Miso Banana (wildcard) | 30 aged rum · 15 banana liqueur · 5 miso caramel syrup | from the miso | sesame on half |

#### Banana: balance rethink (27 October 2026)

Checked against the house Espresso Martini (45 vodka · 20 Kahlúa · 5–10 ml sugar syrup · 30 espresso;
about 10–13 g sugar per drink, estimated, assuming 1:1 syrup). The first Miso Banana spec (30 aged rum · 15 banana liqueur · 5 miso
caramel) comes to about 6–7 g of sugar on paper. Deep caramel tastes less sweet than its sugar,
and there's no coffee liqueur to round the espresso, so it would likely drink **drier and heavier**
than the Espresso Martini. Revised options (sugar figures are estimates; check labels):

| | Per serve (+ 30 espresso) | Sugar (est.) | Std drinks |
|---|---|---|---|
| **V1 Miso Banana, balanced** | 30 aged rum · 20 banana liqueur · 10 miso caramel | about 11 g | 1.35 |
| **V2 Lighter body** | 15 white rum · 15 aged rum · 20 banana liqueur · 10 miso caramel | about 11 g | 1.35 |
| **V3 Salted caramel, no miso** | 30 aged rum · 20 banana liqueur · 10 salted burnt-sugar syrup | about 11 g | 1.35 |

V1 batch, 11 serves (660 ml): 330 aged rum · 220 banana liqueur · 110 miso caramel. About 28% ABV,
so it's stable; best within about 4 weeks. Pour 60 ml batch + 30 ml espresso.

Adjust in this order: too bitter, +2.5 ml caramel; too sweet, −2.5 ml banana liqueur; too heavy,
swap half the aged rum for white rum (V2); flat, +1 drop saline.

#### Banana: all-bottled version, no house preps (27 October 2026)

Ari prefers shelf-stable bottles only, so batching stays simple. No miso caramel and no burnt-sugar
syrup.

**Salted Banana (lead).** Bottle, 700 ml: 380 aged rum · 240 banana liqueur (e.g. Giffard Banane du
Brésil) · 80 Monin Salted Caramel syrup. Pour **60 ml batch + 30 ml espresso**, shake hard,
fine-strain, chilled coupe; optional sea-salt flakes on the foam. Per drink that's about 11 g
sugar (estimate: Monin syrups are roughly 0.85 g sugar per ml; check the label) and about 1.4
standard drinks. The batch is about 30% ABV, so it's shelf-stable; best within about 6 weeks.

**Smoky version:** the same bottle with mezcal instead of aged rum (or half and half).

If it drinks too sweet, cut the Monin to 60 ml per bottle. Too dry: add 5 ml sugar syrup at
service, as with the house Espresso Martini.

**Novelty check (Cobber's bar-menu corpus):** banana with coffee is already common, especially in
Sydney:
- Midnight Monkey (Bar Ombré, Sydney): whisky, banana liqueur, Tia Maria, espresso, caramelised banana.
- Monkey Business (Employees Only Sydney): miso-butter-washed dark rum, coffee honey, banana, walnut bitters.
- Second Wave (Shell House, Sydney): scotch, coffee liqueur, banana liqueur, rosso, amaro, coconut.
- James Gandolfini (Apollonia, Sydney): bourbon, aperitivo, bitter, vermouth, banana, chocolate, coffee.
- Chicory (SOMA Soho, London): banana-peel rum, cognac, jaggery and almond, chicory foam.

Rum or whisky with banana and caramel is not novel. None of these uses **agave** or **cardamom**,
so the novel angle is mezcal and cardamom bitters (still all bottled): 380 mezcal (or 190 mezcal
+ 190 aged rum) · 240 banana liqueur · 80 Monin Salted Caramel · 10 ml cardamom bitters per 700 ml
bottle. Garnish with smoked sea-salt flakes.

## Coffee pairing exploration: food science (27 October 2026)

No specs or batch amounts; this is for tasting. "Cobber" figures are shared-compound harmony with
coffee and recipe tradition (0 = never seen together, i.e. novel). Other chemistry notes are
general food-science knowledge, not Cobber data.

| Bridge | Pairing with coffee | Why | Cobber |
|---|---|---|---|
| Roast on roast | Wattleseed | Shares coffee's roasted compounds (pyrazine, 2-furfurylthiol, furfural) | 0.40, tradition 0 |
| Roast on roast | Toasted / black sesame | Roasted sesame is known for the same "roasted coffee" thiol | not in Cobber |
| Roast on roast | Roasted barley or hojicha | Roasted-grain pyrazines | not in Cobber |
| Earthy | Mushroom (porcini, shiitake) | 1-octen-3-ol (earthy) is in both; mushroom adds umami | 0.23, tradition 0 |
| Earthy and briny | Olive / olive brine | Shares 1-octen-3-ol and fruity esters; brine adds salt | 0.25, tradition 0 |
| Fruity esters | Mango | Shares fruity and roasted notes; echoes Ethiopian and Kenyan coffees | 0.20, tradition 0 |
| Fruity esters | Grape, pisco, sparkling wine | Winey esters, like natural-process coffees | 0.14–0.21, tradition 0 |
| Floral | Lemon myrtle | Shares geraniol and myrcene (coffee's floral side) | 0.17, tradition 0 |
| Sour caramel | Tamarind | Caramel-like furfural plus fruit acidity | 0.14, tradition 0 |

Banana (not in Cobber): ripe banana's aroma is mainly fruity esters (isoamyl acetate), with a
clove-like note (eugenol). Partners by mechanism:
- clove or allspice: the same clove note, as in banana bread;
- rum or mezcal: fruity esters, and smoke;
- sesame or tahini: roast plus fat;
- miso: salt and umami against sweet;
- wattleseed: roast that bridges to the coffee;
- cardamom.

Taste levers:
- Salt suppresses bitterness and lifts sweetness.
- A little acid makes coffee read "bright", like specialty coffee.
- Fat carries aroma and rounds the drink.
- Umami deepens caramel.

Method: bench-test pairs first (a splash of espresso with one element), then build drinks only
from pairs that work.

### Research audit results (ChatGPT deep research, 27 October 2026)

An odour-threshold and novelty audit of the pairing map above. Its rule: a bridge only counts if
the shared compound is odour-active in both foods (OAV, AEDA or recombination evidence). Its
citations haven't all been checked here.

**Corrections to Cobber's bridges:**
- **Olive:** the real link is guaiacol (smoky-phenolic), not the esters Cobber listed. Dose-
  sensitive: guaiacol can read as a "bad olive" note.
- **Mango:** the real link is beta-damascenone (one of coffee's strongest odorants). Mango's very
  potent fruity esters add contrast.
- **Porcini:** linked through methional (cooked-potato, savoury) more than 1-octen-3-ol.
- **Miso:** the strongest chemistry of all (2-furfurylthiol, the core roasted-coffee odorant,
  plus methional), but low novelty.
- **Wattleseed, lemon myrtle and tamarind:** unproven bridges. Treat them as sensory hypotheses
  and contrasts.
- **Cardamom:** a contrast pairing, low novelty.

**Taste corrections:**
- Salt suppressing bitterness is solid (Breslin & Beauchamp, Nature 1997), but test it on the
  house espresso.
- Umami does **not** reliably boost sweetness; it depends on concentration.
- Fat (milk, tahini, oil) can **reduce** coffee's roasted top note rather than carry it.
- Aromatic brightness (mango, citrus aroma) is safer than added sourness against 30 ml espresso.

**Novelty notes:**
- Banana + coffee is crowded in Sydney: add Arms Length (Potts Point) Banana Espresso Martini,
  2026.
- Miso, cardamom and wattleseed espresso drinks already exist.
- Olive brine + espresso, hojicha + espresso and mango appear least occupied.

**Recommended ranking for this brief:**
1. Green olive brine (bridge plus salt; apéritif-style). Crawley's Dirty Martini Olive Brine is
   bottled; it could be the same bottle as Olivia's, but that makes two olive drinks on the menu.
2. Roasted sesame (aroma rather than tahini texture).
3. Hojicha or roasted barley (the most elegant roast-on-roast).
4. Mango (Monin Mango; bench the actual bottle).
5. Banana + salt: the safest crowd-pleaser and the commercial control. Make salt the twist; don't
   stack more flavours.

**Bench flights** (same espresso, plain-espresso reference each round):
1. Mango, then banana with and without salt, then hojicha or barley.
2. Sesame, then olive brine, then miso (miso as the "positive control" for a real roast bridge).
3. Lemon myrtle, pisco, wattleseed, tamarind, mushroom (last: biggest carry-over).

Score each 1–5:
- coffee integrity, integration, distinctiveness, bitterness balance;
- brightness against sourness, aroma lift, finish;
- recognition, crowd appeal, novelty, operational fit.

Weight integration, coffee integrity, finish and crowd appeal above novelty.

### Liqueur shortlist beyond banana (27 October 2026)

Built on the audit's strongest finding: beta-damascenone is one of coffee's most intense
odorants. In Cobber's data the fruits that carry it are grape, apple, pear, strawberry,
raspberry, cherry, Davidson plum and muntries. Pairings only, no specs.

| Liqueur | Link to coffee | Novelty | Status |
|---|---|---|---|
| Crème de framboise / Chambord | beta-damascenone (raspberry); also an ionone floral note | medium | Chambord on the bar |
| Crème de cassis | Kenyan coffees are described as blackcurrant; French | medium–high | Massenez Cassis on the bar (El Diablito) |
| Mango liqueur or Monin Mango | beta-damascenone; very potent fruity esters for contrast | medium–high | Monin Mango in Australia; check liqueur brands |
| Pear liqueur / Pommeau | beta-damascenone (pear, apple); Normandy story | medium | on the bar |
| Crème de châtaigne (chestnut) | roast-on-roast (not audited); French Mont Blanc dessert | high | buy; check availability |
| Sesame shochu (e.g. Beniotome) | roasted-sesame aroma (audited as a strong roast bridge) | high | buy; check availability at Japanese liquor stores |
| Pineapple liqueur | furaneol-type caramel note (not audited) | medium | buy |
| Davidson plum (native) | beta-damascenone in Cobber; tart, Australian | high | check bottled options |

### Follow-up audit: verification (27 October 2026)

The follow-up audit came back as an infographic. Its citations are **unreliable**. Crossref is
blocked here, so four key claims were spot-checked by web search:

| Claim in the infographic | Check | Verdict |
|---|---|---|
| Blackcurrant–coffee bridge via the thiol 4-methoxy-2-methyl-2-butanethiol ("Kenyan coffee", Fredesdorff 2016) | The thiol is confirmed in blackcurrant (Jung, Fastowski & Engel, Flavour Fragr. J. 2016). No source found for it in coffee | **Coffee side unverified.** Cassis stays a tasting-note story, not a proven bridge |
| Sesame shochu carries roasted-sesame odorants | The evidence found is for Chinese **sesame-flavour baijiu** (zhimaxiang), not Japanese shochu: 2-furfurylthiol OAV 1182, beta-damascenone OAV 116, methional OAV 99, confirmed by omission and recombination. Roasted sesame itself: 2-furfurylthiol "coffee-like" (Schieberle 1996) | **Strongly supported, for baijiu.** Three of coffee's key odorants at high OAV. Shochu (Beniotome) is unverified |
| Mezcal–coffee bridge via guaiacol, "Yes" | Guaiacol is present in mezcal (GC-MS, not olfactometry) and has a very low odour threshold (Schranz et al., Food Chem. 2017). No mezcal OAV study found | **Partial,** not yes |
| Davidson plum citation, DOI 10.1111/fwb.13373 | A Freshwater Biology DOI, unrelated to Davidson plum | **Wrong citation** |

Also: the infographic says guaiacol is not detected in pisco, but the first audit listed guaiacol
among pisco's grape-derived odorants. **Unresolved.**

Use for Cobber data only what is verified above. The new lead: **sesame-flavour baijiu** is a
bottled carrier of 2-furfurylthiol, beta-damascenone and methional, i.e. coffee's own key
odorants. Check availability in Sydney (Chinese liquor stores).

### Ten combinations to bench (27 October 2026)

Combinations only, no amounts. All are built on fresh espresso with no coffee liqueur, lighter
than the house Espresso Martini.

Evidence tiers:
- **V:** verified in this session.
- **A:** from the first audit (its citations weren't individually checked).
- **S:** sensory or culinary tradition only.

| # | Combination | Why | Evidence | Novelty | Carrier |
|---|---|---|---|---|---|
| 1 | Vodka or white rum · **sesame-flavour baijiu accent** · demerara · salt | The baijiu carries coffee's own key odorants (2-furfurylthiol, beta-damascenone, methional) | V | high | bottle (check Sydney stock) |
| 2 | Vodka or blanco tequila · **green olive brine** · demerara | Guaiacol bridge, plus salt suppressing bitterness | A + V (salt) | high | bottle (Crawley's brine); a second olive drink next to Olivia |
| 3 | White rum · **mango** · salt | Beta-damascenone bridge, potent fruity esters | A | medium–high | bottle (Monin Mango) |
| 4 | Brandy · **pear liqueur or Pommeau** · honey | Beta-damascenone in pear and apple; Normandy story | A | medium | bar |
| 5 | Brandy or vodka · **crème de cassis** | Kenyan coffees taste of blackcurrant; French | S | medium–high | bar |
| 6 | Vodka · **hojicha** · demerara | Roast on roast; roasted barley/tea is well evidenced | A | medium–high | prep (tea infusion) |
| 7 | Brandy · **crème de châtaigne** · salt | Roasted chestnut, Mont Blanc; French | S | high | buy |
| 8 | Aged rum · **banana liqueur** · **toasted sesame (baijiu accent)** · salt | Sesame and coffee share roast; coffee bridges to banana; not on the Sydney banana list | V (sesame) + S | medium–high | bottles |
| 9 | Aged rum · banana liqueur · salted caramel | The crowd-pleaser and commercial control | S + V (salt) | low | bottles |
| 10 | Vodka · Chambord · white crème de cacao | Beta-damascenone in raspberry; familiar dessert | A | low | bar + buy cacao |

Bench order: 1, 2, 3 (the strongest evidence and novelty), then 8 against 9 (banana with and
without sesame), then the rest.

### Wider sourcing research: liqueurs available in Australia (27 October 2026)

Web research for the Me.. Espresso exploration. Prices and ABV are as listed by retailers on
the day; check before buying. No specs.

| Flavour | Bottle (ABV) | Where (AU) | Coffee idea | Evidence | Novelty |
|---|---|---|---|---|---|
| Chestnut | Gabriel Boudier Liqueur de Châtaigne (25%); also Vedrenne, Briottet, Massenez | Nicks ($64.99); Luca Collections ships to AU | Brandy · chestnut · salt: Mont Blanc, French | sensory/roast (unaudited) | high |
| Wattleseed toffee | Tamborine Mountain Wattle Toffee Liqueur (20%, 375 ml) | Dan Murphy's; distillery ($55) | Aged rum or brandy · wattle toffee · salt. Label notes "coffee hints"; the producer suggests it for Espresso Martinis | label + Cobber 0.40 (bridge unaudited) | medium (wattleseed EMs exist) |
| Walnut (Australian nocino) | Marionette Nocino (28%, walnut + lemon myrtle + wattleseed); Boatrocker (33%); Autonomy (22%); Underground Spirits (16%) | Nicks; Dan Murphy's | Brandy · nocino: Italian coffee-and-nocino digestif | culinary | medium (walnut is in the Nutty Old Fashioned) |
| Pistachio | Paesano Pistachio Liqueur (17%, cream) | Dan Murphy's | Vodka · pistachio · salt: Sicilian café | culinary | medium |
| Ube | Destileria Barako Ube Cream Liqueur | Dan Murphy's (2026, via 7000 Islands) | White rum · ube: Filipino ube latte culture | culinary | medium–high |
| Hojicha | Komasa Hojicha Gin (40%, 500 ml) | Nicks ($99.99) | Hojicha gin as base · demerara: bottled roast-on-roast | first audit (roasted tea/barley) | medium–high |
| Matcha | Gabriel Boudier Matcha (20%, French); Tia Maria Matcha (17%); Kyoto Matcha Sake Liqueur (6%) | Caravan Wines ($68); Nicks ($69.99) | Matcha · espresso: the café "dirty matcha" | café trend | medium |
| Ume (plum) | Choya and other umeshu; Ozeki Yuzu Umeshu (12%) | Dan Murphy's | Umeshu · espresso: ume kernels give an almond (marzipan) note, and almond–coffee is a strong pair | culinary chemistry (unaudited) | high |
| Yuzu | Kikuyasaka Yuzuyuzu (10%, shochu base); Choya Yuzu (14.7%); Umenoyado Yuzu (8–9%) | Dan Murphy's; BWS | Yuzu espresso tonic, long and low-ABV: aromatic brightness | first audit (aromatic brightness over sourness) | medium |
| Strega | Strega (40%: saffron, mint, fennel) | Nicks ($94.99); BWS | A small accent with brandy · honey: caffè corretto | culinary | high (polarising) |
| Mastiha | Skinos (30%) | via Tirnavos Wines (distributor) | Vodka · mastiha · vanilla: Greek | hypothesis | high (risky) |
| Mirto | Osare Mirto (Hobart; myrtle + Tasmanian honey) | Osare (seasonal) | Coffee then mirto: the Sardinian digestif ritual | culinary | high |
| Hazelnut | Giffard Classic Noisette (25%) | Nicks | Café noisette | culinary | low–medium |
| Vanilla / caramel | Giffard Vanille de Madagascar; Giffard Caramel Toffee; Cognac & Caramel | AU retailers (check) | Bottled sweeteners instead of house syrups | — | — |

Not found in Australia:
- sesame-flavour baijiu (Jingzhi);
- kokuto spirits (Kokuto De Lequio);
- osmanthus liqueur;
- black sesame liqueur;
- a hojicha liqueur (one exists only in the UK).

Caveat: cream liqueurs (pistachio, ube) add fat, which can mute coffee's roasted top note.

### Pistachio option and the banana stacking question (27 October 2026)

**Pistachio:** the bar has plenty of pistachio kernels. Make a **toasted pistachio spirit**, not a
fat wash or a cream. It's shelf-stable, it keeps nut fat (which mutes coffee aroma) mostly out of
the drink, and toasting builds the roasted-nut notes that sit next to coffee's roast. Pistachio
isn't in Cobber's data.
1. Toast 150 g kernels at 160 °C for 8–10 min (or in a dry pan) until fragrant and lightly golden,
   not brown. Cool, then crush roughly.
2. Infuse in 700 ml vodka (or white rum) for 48–72 h at room temperature, shaking daily. Taste at
   48 h.
3. Strain through a sieve, then a coffee filter. If it's hazy, freeze it overnight and filter
   again.
4. Yields about 650 ml. Shelf-stable (about 40% ABV); best within 2–3 months.

Salted kernels add a little salt for free. Alternative with body: pistachio orgeat (fridge about
2 weeks, about 3–4 weeks with sorbate). **Allergen:** tree nut; flag it on the menu and in the
allergen protocol.

**Banana: stack or not?**
- Default to **banana + salt only**. The research says salt should be the twist, and Sydney's
  banana–coffee drinks all stack more flavours.
- Add a layer only if the bench shows a specific gap: a thin mid-palate (try toasted pistachio),
  or too sweet or flat (more salt before any new flavour).
- Rule: at most two flavours, plus coffee and salt. Each must be named by tasters without being
  told, and must raise the integration score.

**Bench (single serves, house espresso, same base spirit):**
1. House Espresso Martini, as the control.
2. Banana + salt.
3. Toasted pistachio + salt.
4. Banana + toasted pistachio + salt.

If 4 beats both 2 and 3 on integration and crowd appeal, the stack has earned its place;
otherwise keep the single-flavour winner.

**No vodka? Infuse the drink's own base spirit** (same recipe: 150 g toasted kernels per 700 ml,
48–72 h). Then the pistachio is the base itself and nothing is added.
- **Brandy:** French pâtisserie (pistachio macaron, Paris–Brest); the most on-brand.
- **White rum:** the lightest.
- **Aged rum:** if it joins the banana.

Keep the spirit at about 35–40% for good extraction and shelf life. Optional: sweeten the infused
spirit into a house pistachio liqueur (dissolve sugar to taste), so one bottle is base, flavour and
sweetener. No-alcohol route: pistachio orgeat.

**Pistachio × coffee trends (October 2026 search):**
- Pistachio lattes at the big chains: Starbucks brought back its pistachio latte and added a
  pistachio cortado for winter 2026; Tim Hortons launched a chocolate–pistachio line.
- The viral TikTok pistachio latte: espresso poured over pistachio cream.
- Dubai chocolate (pistachio, chocolate, crunchy kataifi): the craze is fading, but pistachio has
  outlasted it.
- Pistachio tiramisu and affogato: mostly a recipe trend.
- No pistachio Espresso Martini found on Sydney or Melbourne bar menus: an opening.

Stack plan: first add pistachio as a **garnish** (crushed toasted, salted kernels on half the
foam); move it into the liquid (pistachio brandy) only if it earns its place.
