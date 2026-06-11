# Cobber the Mixologist

Meet **Cobber the Mixologist**. You can just call him Cobber. He's a mate behind
the bar who happens to know the flavour chemistry of everything on your shelf —
tell him what bottles and ingredients you've got, nominate two or three to build
around, and he'll invent chemically plausible, genuinely novel drinks, with an
optional Australian native-ingredient twist.

`cobber` is a small, local [MCP](https://modelcontextprotocol.io) server written
in Python. It gives any Claude a grounded "sense of taste".

## How it works

The core idea is a clean split: **the server is deterministic and dumb; the
reasoning lives in the host Claude.** Cobber does the flavour-chemistry maths —
which ingredients share aroma compounds (harmony), how classic a pairing is
(tradition), how interesting an under-explored-but-grounded pairing is (novelty),
and whether a combination is roughly balanced. It never calls a language model
and never touches the network; it just reads three flat JSON data files and runs
pure functions over them. The host Claude does everything creative: interpreting
a vague brief, picking a direction, and writing the actual recipe, ratios, and
name. That split is what makes it free per drink, fast, and trustworthy — the
chemistry stays in code, the creativity stays in the model.

Composites (gin, Campari, Peychaud's…) don't carry their own compound lists; they
carry a *botanical bill*, and their flavour profile is derived as the union of
those botanicals' compounds. So gin "knows" it shares citral with lemon myrtle
because juniper, coriander seed, and its citrus peel say so.

## The tools

| Tool | What it does |
| --- | --- |
| `resolve_ingredients(names)` | Fuzzy-maps free-text names to known ids. The single input seam. |
| `score_pairing(a, b)` | Returns harmony, tradition, novelty, and shared compounds. |
| `suggest_from_pantry(pantry, anchors, native_twist=False, n=5)` | The primary tool: drink combinations built around 2–3 anchors. |
| `explain_pairing(a, b)` | A plain-language, data-driven rationale for a pairing. |
| `get_native_twist(base_id, n=3)` | Australian natives that bridge to a given ingredient. |

The **anchor mechanic** is required: you give a full pantry, but the drink is
built around 2–3 nominated anchors. Every suggestion contains all the anchors,
and the rest of the pantry is ranked by how well each addition bridges to them.
Supply fewer than 2 or more than 3 anchors and the tool returns a clear message
asking you to pick 2–3.

## Install

You'll need Python 3.11+.

```bash
git clone <your-fork-url> cobber
cd cobber
pip install -e .
```

### Claude Desktop

Add Cobber to your `claude_desktop_config.json` (Settings → Developer → Edit
Config). Use `cobber` as the server key:

```json
{
  "mcpServers": {
    "cobber": {
      "command": "python",
      "args": ["-m", "cobber.server"]
    }
  }
}
```

If `python` isn't on Claude Desktop's PATH, use the absolute path to the
interpreter in the environment where you ran `pip install -e .` (e.g.
`/usr/local/bin/python3`), and add a `"cwd"` pointing at the repo if needed.
Restart Claude Desktop and Cobber will appear in the tools list.

### Claude Code

From inside the repo:

```bash
claude mcp add cobber -- python -m cobber.server
```

Or add the same `mcpServers` block shown above to your Claude Code MCP config.

## Example chat

> **You:** Oi Cobber, I've got gin and Peychaud's — build me something funky
> around them.
>
> **Cobber:** *(resolves "gin" → `gin`, "Peychaud's" → `peychauds_bitters`,
> confirms those two as your anchors, runs `suggest_from_pantry`, and grounds the
> why in `explain_pairing`)* Right, those two share limonene through the citrus in
> the gin and the bitters' botanicals — so there's a real bridge to lean on, and
> almost nobody builds a drink around it, which makes it a fun one. Here's a short
> gin-and-Peychaud's sour, and if you're up for it I'll show you the bush-food
> version with a touch of lemon myrtle, which slots straight in on shared citral…

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

The suite pins the behaviours that matter: a native citrus bridges to lime,
roasted wattleseed shares nothing with citrus (handled, not crashed), gin's
derived profile equals the union of its botanicals, every suggestion contains all
anchors, and a 2–3 anchor list is enforced.

## Data provenance — entries flagged `TODO: verify`

**A wrong-but-confident compound profile is worse than a flagged uncertain one.**
The common bar ingredients are drawn from well-documented essential-oil and
food-volatile profiles. The entries below carry a `TODO: verify` in their
`source` field — best estimates I want fact-checked against the flavour-chemistry
literature before this ships under anyone's name. The two broad reasons are
(1) **Australian natives**, where published volatile data is genuinely sparse, and
(2) **composites with secret or fermentation-derived profiles** (commercial
liqueurs, aged spirits), where the botanical bill is a representative
approximation, not the real recipe.

**Australian natives (sparse published data):**
- Desert lime — minor terpene fraction unverified
- Lemon aspen — limited published volatile data
- Cinnamon myrtle — dominant compound varies by chemotype
- Riberry — described as clove-like; sparse compound data
- Tasmanian pepperberry — polygodial confirmed as the pungent principle; terpene fraction unverified
- Wattleseed — roast compounds modelled by analogy to coffee (Maillard pyrazines/furans)
- Davidson plum — modelled on dark-plum volatiles
- Quandong — modelled on stone-fruit lactones
- Muntries — described as spiced apple; sparse data
- Bush tomato — modelled on caramel/sotolon notes
- Strawberry gum — high in fruity esters/furaneol; exact profile unverified
- Native river mint — chemotype (menthol vs pulegone) varies

**Composites & a few raw ingredients (proprietary / fermentation-derived / approximated):**
- White rum, dark rum — rum aroma is largely fermentation esters not modelled here
- Tequila, mezcal — cooked-agave volatiles; mezcal's smoke phenols omitted
- Bourbon, rye whiskey, brandy — barrel-derived vanillin/oak-lactone approximations
- Sweet vermouth, dry vermouth — proprietary blends; representative bills
- Campari, Aperol — secret recipes; bitter-orange + gentian representative
- Green Chartreuse — 130 secret botanicals; a tiny representative subset
- Angostura bitters, Peychaud's bitters — secret recipes; representative bills
- Bitter orange peel — exact aldehyde balance unverified
- Angelica root — musk-lactone content unverified
- Elderflower — rose/nerol-oxide ratios unverified
- Passionfruit — sulfur-thiol contribution not modelled
- Honey — varies widely by floral source
- Agave syrup — largely sweet, low aroma; volatile content unverified

## Designed-for-later (not built in V1)

- **Photo shelf-scan.** `resolve_ingredients` is deliberately the only input seam,
  so a future vision step can hand it ids without touching anything else.
- **Seasonal produce.** Natives carry a `season` field, but it stays `null` and
  unused — there is no seasonal logic anywhere in V1.

## Non-goals for V1

No vision/photo handling, no seasonal filtering, no ingestion of external flavour
databases, no network calls, no database, no LLM calls inside the server, no web
UI. Flat JSON + pure functions + thin MCP wrappers, nothing more.
