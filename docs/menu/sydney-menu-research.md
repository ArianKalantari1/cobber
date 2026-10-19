# Sydney Cocktail Menus: What They Do (October 2026)

Notes from Ari's screenshots of five Sydney bar menus, used to shape the Apéritif & Co
cocktail menu ([menu.json](menu.json) → [PDF](aperitif-co-cocktail-menu.pdf)).
Last updated: 2026-10-19.

## Prices

| Venue | Cocktails | Notable |
|---|---|---|
| Bopp & Tone | $22–29 | Pomodoro Martini $27; Wagyu Old Fashioned $29; NON Kalimotxo $15 |
| Rook | $25–26.50 | Strawberry Cheesecake Milk Punch; brown butter bourbon |
| Zephyr (Hyatt) | mostly $28 | Pistachio Press $35; Barrelled & Aged $32 |
| Aria | $27–47 | Non-alcoholic $14–18 |
| 83 Sydney Tower | $26–42 | Mocktails $19 |
| **Apéritif & Co** | **$21–25** | The value end of the group |

Apéritif & Co is the cheapest of the group, usually by a few dollars a drink. For example,
its Tomato Martini ($22) is $5 under Bopp & Tone's Pomodoro ($27).

## How they write the menu

- **Bopp & Tone:** name and price on one line; short Title Case ingredients with a brand on
  the main spirit only; three italic descriptors (*Boozy, Textural, Complex*). Value words
  stay on the menu: "Rescued Champagne", "Generous pour of…". The June list had a
  **Ruby Cobbler**.
- **83 Sydney Tower:**
  - "/" between ingredients; prices with no "$"; a fine rule under each name.
  - A "Creative Corner" refreshed every two months, with bartender credits and a
    "WINNER!" tag.
  - "Our classics with an elevated twist"; aquafaba instead of egg; "(contains gelatin)";
    numbered footnotes.
  - Dietary codes V, VG, GF, DF, NF.
- **Rook:** drink photos, a "Popular" tag, and a separate Spritz section.
- **Zephyr:** "Classic cocktails available on request"; House Specialties (G&Ts, Spritzes);
  a **Barrelled & Aged** section (Century Negroni, Vieux Carré, 3 months, $32).
- **Aria:** centred layout and a premium savoury list:
  - Umami onion Gibson, Nitro Bloody Gin Fizz.
  - Duck fat cognac with Manzanilla in an Old Fashioned.
  - Cinnamon myrtle, native plum salt, ají amarillo, miso caramel.
  - Banoffee Milk Punch.

## Trends across the five

- **Milk punch** (three venues): clear, silky, batchable, and stable for weeks.
- **Fat-washing:** wagyu, brown butter, duck fat.
- **Savoury and umami:** tomato, onion, miso, Manzanilla.
- **Australian natives:** cinnamon myrtle, native plum, lemon myrtle.
- **Dessert flavours:** banana, cheesecake, coffee, chocolate, pistachio.
- **Lychee** still appears (we've already ruled out a lychee martini).
- **Non-alcoholic** is now a real section at $14–19.

## Applied to the Apéritif & Co PDF

- Bopp & Tone's format throughout: short ingredients and three descriptors.
- **Prices without "$"**, as at 83. Menu-pricing research (Cornell, 2009) found guests spend a
  little more when the currency sign is dropped. To bring it back, change `item_html` in
  [build_menu.py](build_menu.py).
- An **Off the Menu** box: "Don't see your favourite? Ask us: most classics can be made on
  request" (Zephyr's line, to confirm with the owner).
- Egg white shown with a † and a footnote, not in every ingredient line.
- Tags kept to two (Apéritif Favourite, Sommelier's Favourite). Like Rook's "Popular", a tag
  only works if it's rare.

## Ideas not applied (owner's call)

- **Rescued wine cobblers as their own section.** Bopp & Tone sells "Rescued Champagne" and
  a Ruby Cobbler, which shows the angle sells. See
  [../recipes/rescued-white-wine-cobblers.md](../recipes/rescued-white-wine-cobblers.md).
- **A non-alcoholic section, 2–3 drinks at $14–16.** Everyone else has one. The Lyre's
  Classico and Altina sparkling rosé already behind the bar are a starting point.
- **A nut marker.** It needs a full check before it goes on, because a partial marker is
  worse than none:
  - Nuts for certain: Nutty Old Fashioned (peanut butter whiskey, walnut) and Espresso
    Sour (orgeat).
  - Depends on the amaretto brand: Olivia and the amaretto sour.
- **Milk punch** as a wine-waste route: milk-washing the rescued wine gives a clear,
  long-keeping batch, and it's the most common trend across these menus.
- **A rotating "Creative Corner"** (83) for staff drinks. It keeps the list fresh without
  reprinting the whole menu.
