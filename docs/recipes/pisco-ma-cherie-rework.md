# Pisco Ma Chérie: re-scored, and the options

Ari asked for a rework: re-score the drink with the updated Cobber and lay out what we could
change. This scores the current prep spec, [pisco-ma-cherie.md](pisco-ma-cherie.md) (last
updated 22 October; on branch `claude/stoic-fermat-1l819l` until it merges, with a copy in
[house-specs.md](../house-specs.md)). Nothing here changes the spec until it's tasted.
Last updated: 2026-10-23.

**In short:**
- Today's Cobber scores it 0.045 for harmony and 0.042 for novelty, which is low. Most of that
  is Cobber's data: it can't tell the pisco from the sherry, and its black pepper shares
  nothing with the rest of the drink.
- On sourced data (a proposal waiting for Ari's OK), the drink holds together: every part
  links to at least two others, and the Medium sherry links to all of them. Three threads run
  through it: juicy fruit, caramel and a malty, cocoa-like note.
- **Test first:** the caramel is now in three parts of the drink (the Medium, the demerara and
  the Moro vinegar) and the strawberry in two, so the caramel may sit on top of the fruit
  rather than under it. Taste a shrub made with all white sugar against today's.
- **Test second:** strawberry gum in the maceration. It carries the strawberry in a second
  part of the drink and doesn't change the sugar, acid or strength.
- **Keep:** the Elegante Medium (it beats La Guita on the sourced data), the black pepper and
  the orange wheel.

## 1. The score today

Scored with `score_drink` on pisco, sherry, strawberry, black pepper, demerara and orange. Soda,
salt and sugar count as structure, not aroma.

| | Harmony | Novelty |
|---|---|---|
| Pisco Ma Chérie | 0.045 | 0.042 |
| IBA drinks, median (75 drinks) | 0.109 | |

That puts it at the 17th percentile of the IBA drinks. Novelty is almost the same as harmony
because no classic drink in Cobber's corpus pairs pisco or sherry with strawberry, so nearly
every link counts as new.

What the number is made of:
- **One strong link:** strawberry to pisco and sherry (0.25), through the fruity esters and
  β-damascenone they share. That's the "Juicy" on the menu.
- **Weak links:** orange to strawberry and to pepper (0.08 each).
- **No links:** black pepper and demerara connect to nothing but the orange.

Why the number undersells the drink:
- **Pisco and sherry are the same entry** in Cobber (both "grape"), so they count as one voice,
  and the Medium's nut and caramel are invisible.
- **Black pepper is three compounds,** and none of them is in the strawberry, the grape or the
  sugar.
- **Demerara is one compound** (sotolon, the caramel note). Aged sherry and sherry vinegar both
  carry it in the published studies, but not in Cobber's data.
- **The shrub's vinegar isn't in Cobber at all.**

## 2. On sourced data (a proposal, not yet applied)

[`data/pisco_sherry_proposal.json`](../../data/pisco_sherry_proposal.json) gives pisco, sherry,
a new Medium sherry, sherry vinegar, black pepper and cacao nibs the key odorants named in
published studies (sources at the end). It changes nothing until Ari approves it. Scored on a
scratch copy:

| | Today's data | Sourced data |
|---|---|---|
| Harmony | 0.045 | 0.047 |
| Aroma voices | 5 | 7 (pisco and the Medium apart, and the vinegar counted) |
| Pairs that share compounds | 4 of 10 | 13 of 21 |

The number hardly moves, because Cobber averages over every pair and seven voices make 21
pairs. Drinks with more voices score lower on average: the IBA drinks with six or more have a
median of 0.078. The shape is what changes. Every part of the drink now links to at least two
others.

The links between pairs (Cobber's harmony for each pair on its own):

| Pair | Harmony | What they share |
|---|---|---|
| Pisco and Medium | 0.20 | isobutanal (malty), 2-phenylethanol (rose, honey), ethyl butyrate (fruity) |
| Demerara and Moro vinegar | 0.17 | sotolon (caramel) |
| Black pepper and orange | 0.17 | limonene, linalool, myrcene |
| Pisco and strawberry | 0.13 | β-damascenone, ethyl butyrate |
| Medium and Moro vinegar | 0.13 | sotolon, ethyl isobutyrate |
| Pisco and black pepper | 0.13 | isobutanal, linalool |
| Strawberry and orange | 0.11 | fruity esters |
| Medium and strawberry | 0.11 | fruity esters |
| Medium and black pepper | 0.10 | malty aldehydes |
| Medium and demerara | 0.09 | sotolon |
| Pisco and orange | 0.06 | linalool |
| Black pepper and Moro vinegar | 0.06 | isovaleric acid |
| Medium and orange | 0.05 | a fruity ester |

**The Medium is the hub:** it links to all six other parts.

**Three threads run through the drink:**
1. **Juicy fruit** (ethyl butyrate, β-damascenone): the strawberry, the pisco and the Medium.
   This is the hero.
2. **Caramel** (sotolon, the caramel-maple note of aged sherry): the Medium, the demerara and
   the Moro vinegar.
3. **Malty cocoa** (isobutanal and 2- and 3-methylbutanal, the malty aldehydes that also make
   cocoa smell of cocoa): the Medium, the black pepper and the pisco. So there's a chemical
   reason for the cocoa you get from the Medium.

**The pepper seasons rather than echoes:** it links to the pisco, the Medium and the orange,
not to the strawberry. The orange wheel with a pepper twist is the drink's strongest garnish
link.

**Caveats:**
- The new compound ids so far exist only in the proposal's entries, so they can over-link these
  entries to each other until the rest of the pantry is checked. Whisky, rum, coffee and beer
  carry malty aldehydes too. Use these numbers to compare versions of this drink, not to
  compare it with other drinks.
- The flavour words for the new entries ("caramel" for the Medium and the vinegar) come from
  tasting notes, and they decide the family counts in section 3.

## 3. Is the strawberry first? The amplification reading

This is Ari's amplification idea (step 1b of the scoring upgrade, not built yet), done by hand:
name the hero note, count what carries it, and check that nothing crowds it.
- **Hero:** strawberry (fruity). Sources: the strawberry and the pisco.
- **Underneath:** caramel. Sources: the Medium, the demerara and the Moro vinegar.

Cobber's notice on the sourced data, with fruity as the target: *"The target, fruity, has 2
sources (Pisco, Strawberry) against 3 sweet/creamy sources (Medium sherry, Demerara sugar,
Sherry vinegar): it may not come through."*

The switch to Moro sherry vinegar (22 October) added the third caramel carrier. It's the right
vinegar for the sherry, but it may have made the demerara one caramel too many. Sources are
counted, not weighed (200 g of demerara and 120 ml of vinegar count the same), so this is a
thing to taste for, not a verdict.

Today's data reads it the other way round ("3 fruity sources"), because it takes the sherry
for grape. The sourced data is closer to the bottle: Elegante Medium tastes of nuts, toffee and
dried fruit, not fresh fruit.

## 4. The options, in the order to taste them

### Changes to try

| # | Change | Cobber (sourced data) | Balance | Why, and the catch |
|---|---|---|---|---|
| 1 | Shrub with 600 g white sugar and no demerara | 0.047 to 0.060, and the crowding notice goes | Same sugar | Puts the caramel back under the fruit. The red stays redder, and it's one less stock item. Catch: less molasses, so check that the Medium and the Moro still give the toffee finish. |
| 2 | Strawberry gum in the maceration, next to the pepper | 0.047 to 0.048, and fruity goes to 3 sources | No change: it's a dried leaf | Carries the hero in a second part of the drink. Strawberry gum shares five compounds with strawberry (0.50, Cobber's closest match to strawberry), and it also links to the pisco (0.20) and the Medium (0.14). Harmony doesn't reward an ingredient that repeats a note, so the number stays flat; that's the case step 1b is for. Catch: it's a eucalyptus leaf, so the owner's "no herby flavours" rule needs a nod (it smells of strawberry and cinnamon, not menthol), and Cobber's entry for it is provisional. |
| 3 | Both 1 and 2 | 0.059: fruity 3 sources, caramel 2 | Same sugar | The strawberry-forward version. |
| 4 | Cacao nib pisco (10 g per 700 ml, 24 hours, from the R&D notes) | 0.044. It has the strongest links of any addition: Medium 0.21, strawberry 0.14 (through furaneol, strawberry's own caramel note), pepper 0.13 | No change | Only if the cocoa is shy once 1 is settled. It deepens the malty-cocoa thread rather than adding a new one, which is why harmony dips. Buy nibs without a "may contain nuts" warning, because the drink is sold as nut-free. |

**Strawberry gum, where and how much:** Warndu or FISH (dried, ground leaf). It's potent (sellers
advise a pinch of the milled leaf), so start at 1 g in the 1 kg maceration, steeped cold with
the fruit, and taste the syrup when you strain. Too much reads as cinnamon or eucalyptus.
Untested.

### Keep as they are

- **Elegante Medium, not La Guita.** On the sourced data the Medium shares more with the pisco
  (0.20 against 0.08) and the strawberry (0.11 against 0.07), and the drink scores 0.047
  against 0.042. Today's data can't tell the two apart. The Medium also holds up in the drum,
  where a Manzanilla would fade, so the planned La Guita test can go last.
- **Black pepper, not ginger.** With ginger in its place the drink scores 0.034. The pepper is
  also on the menu line.
- **The orange wheel.** Orange and lemon tie (0.047 each), but orange carries the pepper link,
  and sherry with orange is a classic (tradition 0.36, and 8 drinks in the frontier corpus). Pick
  by eye at the first tasting, as planned.

### Not now

- **More caramel** (the Fresa Tostada pan caramel, or more demerara): that's a fourth caramel
  carrier on top of the fruit.
- **Pink peppercorn:** Cobber's entry hasn't been re-sourced, so it can't be compared fairly. It
  does have strawberry precedents (Aster's METEOR in Sydney, and Ari's own strawberry and pink
  peppercorn sour), but black pepper is on the menu line.

**Balance:** options 1 to 4 don't change the sugar, acid or strength. A drink is about 17 g of
sugar and 1.1 g of acid (the vinegar's acetic acid tastes sharper than its grams suggest), 1.54
standard drinks at about 10% ABV.

## 5. Menu check

- **Strawberry is free** on the menu, and nothing above adds a fruit another drink already
  uses.
- **Mando Raspberry Fizz is the close neighbour:** another red fruit and vinegar fizz
  (raspberry, mandarin, balsamic, soda) on the same page. Pisco Ma Chérie stays distinct as the
  tall one, with sherry depth and pepper and no foam, and the descriptors already differ. That's
  one more reason to keep the strawberry and the sherry loud and the vinegar in the background.
- **Precedents, not canon:** no classic drink in Cobber's corpus pairs pisco with strawberry, so
  the core of the drink is new. Its neighbours are on current menus:
  - strawberry, sherry and crème de cacao: Pretty In Pink, Arches On Market, Sydney;
  - strawberry, balsamic and pink peppercorn: METEOR, Aster, Sydney;
  - strawberry and strawberry gum: Lorraine Bracco, Apollonia, Sydney;
  - pisco and sherry: Red, Red Room at The Connaught, London;
  - sherry and black pepper: Alabaster, Red Room at The Connaught; Shishi, Gouqi, London.

## 6. Tasting plan

This adds to the first-tasting checks in the prep spec.
- **Make a half shrub with white sugar only,** on the same day as the main one: 500 g frozen
  strawberries, 300 g white sugar and 1.5 g cracked pepper for 24 hours. Then add 60 ml Moro
  vinegar, 9 g citric, 3 g malic and 0.75 g salt. Rest both shrubs 2 days.
- **Glass A:** today's spec. **Glass B:** the same, with the white-sugar shrub. For a single
  serve, use 41 ml pisco, 18 ml Elegante Medium and 31 ml shrub (one 90 ml pour of batch), then
  75 ml soda.
- **If you have strawberry gum:** glass C is B with 0.5 g strawberry gum in the half shrub's
  maceration.
- **For each glass:**
  - Does the strawberry come first?
  - Is the caramel under the fruit or on top of it?
  - Can you name the pisco?
  - What colour is it?
- Record the answers in [the tasting log](../tasting-log.md) (Session 2).

## 7. Pisco with medium sherry elsewhere (web search, 23 October)

Ari asked for drinks that pair pisco with a medium sherry. Few do; these are the closest,
with the specs as published (none tasted here).

**Pisco with medium or other oxidative sherry:**
- **Fog Cutter, Smuggler's Cove (San Francisco, Martin Cate):** 1 oz pisco, 2 oz rum, ½ oz gin,
  1½ oz lemon, 1½ oz orange juice and ½ oz orgeat, shaken, then a ½ oz float of González Byass
  Nutty Solera. Nutty Solera is a medium oloroso from Elegante's bodega (Palomino with about 17%
  Pedro Ximénez, about 62–72 g/L sugar). This is the one well-known pisco and medium sherry
  drink. Trader Vic's original used brandy and cream sherry.
- **The Greatest Punch on Earth, Morgan Schick, Jupiter Olympus (San Francisco):** 4 oz pisco,
  2 oz oloroso, 1 oz sherry vinegar, 1 oz Luxardo Triplum, 4 oz apple cider, orange and Angostura
  bitters. Sherry as wine and as vinegar, the same idea as Pisco Ma Chérie. (In Cobber's Hotaling
  corpus.)
- **Campo Cooler, The NoMad (New York, Leo Robitschek):** 1½ oz pisco, ½ oz amontillado (Lustau
  Los Arcos), ½ oz unaged rum, ¾ oz honey syrup, ¾ oz lemon and 1 tsp raisin-infused Angostura.
- **Pera Seca, a pisco cobbler (Ricardo Rodriguez, Lita, New Jersey):** 1½ oz pisco, 1 oz verjus,
  ¾ oz spiced amontillado syrup (amontillado simmered with cinnamon and cardamom, sweetened with
  brown or palm sugar) and ½ oz pear brandy over crushed ice, with a ½ oz ruby port float.
- **Red, Red Room at The Connaught (London, June 2026 menu):** Courvoisier XO, pisco, Pedro
  Ximénez, Pinot Noir infused with eucalyptus and white peach, verjus, and peach and jasmine soda.
  (In Cobber's city menus.)
- **A Kindred Cocktails original (2022, unrated):** Capel pisco, Galleano Rose of Peru sweet
  sherry, prickly pear liqueur and Martini & Rossi 1872 Bitter.

**The nearest drink to Pisco Ma Chérie:**
- **The Laotong, Jeremy Buck, Coterie (Charleston):** chamomile-infused pisco and a strawberry and
  tomato shrub made with sherry, rice wine and red wine vinegars, topped with soda. So a pisco
  highball on a strawberry shrub with sherry vinegar already exists. Pisco Ma Chérie differs in
  the Medium, the black pepper, and no tomato or chamomile, so don't sell the shrub highball as a
  first.

**Pisco with dry sherry, for format:**
- **Pisces Rising, Leyenda (New York):** acholado pisco, Manzanilla, lemon, grapefruit, crème de
  pêche, celery bitters and soda, in a Collins.
- **Herencia de Jerez (a Difford's community recipe, unverified):** pisco, brandy de Jerez,
  Manzanilla, sherry vinegar, lemon and sugar.
- **Uncle Al (Punch):** 1½ oz gin, ½ oz pisco, ½ oz fino, ½ oz orgeat, ¾ oz lemon and thyme.

**What it means for this drink:**
- Pisco with a nutty, sweetened sherry works at about 2 parts pisco to 1 of sherry (Fog Cutter,
  Greatest Punch). Pisco Ma Chérie's 40 : 17.5 is in that range.
- Orange keeps turning up next to it (orange juice, triple sec, orange bitters), which backs the
  orange wheel.
- Sherry wine with sherry vinegar is a move a known bartender has already made, which backs
  keeping the Medium and the Moro together.
- Nutty Solera is a second medium sherry from the same bodega, if Elegante Medium is ever out.

## Sources

- **Pisco:**
  - Cacho, Culleré, Moncayo, Palma and Ferreira 2012, *Flavour and Fragrance Journal*
    27(4):322–333 (Quebranta, GC-olfactometry), listed in
    [Moncayo's 2013 thesis](https://zaguan.unizar.es/record/13513/files/TESIS-2014-024.pdf?version=1).
  - The group's [conference abstract](https://papiro.unizar.es/ojs/index.php/jji3a/article/view/1873/1687).
  - A [Quebranta odour-activity table](https://www.omicsonline.org/articles-images/2155-9600-3-245-t004.html).
- **Sherry:**
  - Moyano, Zea, Moreno and Medina 2010, *J. Agric. Food Chem.* 58:6900–6904
    ([record](https://pherobase.com/literature/data/details/C/20740)).
  - Marcq and Schieberle 2015, *J. Agric. Food Chem.* 63:4761–4770
    ([TUM record](https://portal.fis.leibniz-lsb.tum.de/en/publications/characterization-of-the-key-aroma-compounds-in-a-commercial-amont-3/)).
  - Marcq and Schieberle 2021, *J. Agric. Food Chem.* 69:5125–5133
    ([TUM record](https://portal.fis.leibniz-lsb.tum.de/en/publications/characterization-of-the-key-aroma-compounds-in-a-commercial-fino--4/)).
  - Elegante Medium: [United Cellars listing](https://unitedcellars.co.nz/products/gonzalez-byass-elegante-medium-dry).
- **Sherry vinegar:** Callejón and colleagues 2008, *J. Agric. Food Chem.*
  ([record](https://science.ulysseus.eu/records/7t0wv-9p280), [CORE](https://core.ac.uk/works/67808500)).
- **Black pepper:**
  - Jagella and Grosch 1999, *Eur. Food Res. Technol.* 209:16–21, as summarised in the
    [OENO One rotundone review](https://oeno-one.eu/article/view/2947).
  - Wood and colleagues 2008, *J. Agric. Food Chem.* 56:3738–3744
    ([Adelaide repository](https://digital.library.adelaide.edu.au/dspace/handle/2440/55602?mode=full)).
- **Cacao:** Frauendorfer and Schieberle 2008, *J. Agric. Food Chem.* 56:10244–10251
  ([TUM record](https://portal.fis.leibniz-lsb.tum.de/en/publications/changes-in-key-aroma-compounds-of-criollo-cocoa-beans-during-roas-3/)).
- **Strawberry:** Fukuhara and colleagues 2005, *J. Japan. Soc. Hort. Sci.* 74(4):300
  ([J-STAGE](https://www.jstage.jst.go.jp/article/jjshs/74/4/74_4_300/_article)).
- **Strawberry gum:** [Warndu](https://warndu.com/blogs/first-nations-food-guide/warndu-strawberry-gum);
  [Williamson Wines](https://williamsonwines.com/product/strawberry-gum) (a pinch of milled leaf;
  don't heat it for long).
- **Pisco and sherry drinks (section 7):**
  - Fog Cutter: [Classic Fog Cutter (Liq Culture)](https://liqculture.com/?p=4515),
    [SFist on Smuggler's Cove](https://sfist.com/2009/11/13/sfist_drinks_the_fogcutter_from_smu.php);
    Nutty Solera: [Difford's](https://www.diffordsguide.com/en-au/beer-wine-spirits/8510/gonzalez-byass-nutty-solera-medium-oloroso-sherry),
    [LCBO](https://www.lcbo.com/en/gonz-lez-byass-nutty-solera-medium-oloroso-sherry-35204).
  - The Greatest Punch on Earth: `data/raw/hotaling_cocktails.csv`.
  - [Campo Cooler (Punch)](https://punchdrink.com/recipes/campo-cooler/).
  - [Pera Seca (Imbibe)](https://imbibemagazine.com/recipe/pera-seca-a-pisco-cobbler).
  - Red: `data/raw/city_bar_cocktails.json`, from the
    [Red Room menu](https://dxp.maybourne.com/globalassets/our-hotels/the-connaught/rb/red-room/2026/6.-june/the-connaught-red-room-menu-june-2026.pdf).
  - [Kindred Cocktails original](https://kindredcocktails.com/node/10649).
  - The Laotong: [Imbibe](https://imbibemagazine.com/recipe/the-laotong-pisco-cocktail/),
    [Cocktails Distilled](https://cocktailsdistilled.com/recipe/the-laotong/).
  - [Pisces Rising (Imbibe)](https://imbibemagazine.com/?p=27396);
    [Herencia de Jerez (Difford's)](https://www.diffordsguide.com/cocktails/recipe/41718/herencia-de-jerez);
    [Uncle Al (Punch)](https://punchdrink.com/recipes/uncle-al/).
