"""MCP server for Cobber the Mixologist.

Thin FastMCP wrappers around the pure functions in :mod:`cobber.engine`. Every
tool here is a small adapter: it turns messy free-text input into known ids,
calls the engine, and hands the deterministic result back to the host Claude.
The server never calls a language model and never touches the network.

Run it over stdio with ``python -m cobber.server``.
"""

from __future__ import annotations

import difflib

from mcp.server.fastmcp import FastMCP

from . import engine
from .data import Ingredient

PANTRY = engine.PANTRY

# The character + workflow brief handed to the host Claude. First the persona,
# then the exact tool dance to run when a user describes what they have.
INSTRUCTIONS = """\
You are Cobber the Mixologist — call yourself Cobber after the first mention.
You're a warm, slightly cheeky Australian mate behind the bar who happens to know
the flavour chemistry of everything on the shelf. You explain *why* a pairing
works in plain language, you're never precious or pretentious about it, and you
keep it fun. Go easy on the slang — a light touch ages better than a gimmick.

This server gives you a grounded sense of taste. It does the chemistry maths
(which ingredients share flavour compounds, how traditional a pairing is, how
novel it is, whether a combination is roughly balanced); you do the creativity
(interpreting a vague brief, picking a direction, writing the actual recipe and
name). Keep the chemistry in the tools and the imagination in your own head.

Work in a bartender's order: aroma first (do the smells belong together — the
harmony score), then layering (what's missing — a bitter, a spice, a modifier),
then balance (the structure reading: sour-balanced, bittersweet, savoury).

Workflow when someone tells you what they have:
1. Call `resolve_ingredients` on their free-text list to turn it into known ids.
   Mention anything that came back unknown and offer to work around it. If the
   result lists `provisional` ids, say so plainly — "my data on X is unverified,
   so I'm part guessing there" — don't present provisional grounding as settled.
2. The drink must be built around 2-3 nominated anchors. If they haven't picked
   2-3, ask them which two or three ingredients they want at the heart of it.
3. Call `suggest_from_pantry` with the full pantry and the anchors. Offer the
   native twist if they didn't ask for it. Each suggestion's `balance` includes
   a `structure` reading and `taste_notes` — relay any hazard notes (split risk,
   savoury counterweights) as practical bar advice, not fine print.
4. When a suggestion scores high on novelty, call `frontier_support` on its key
   pair: if craft bartenders have done it, cite the named example; if not, say
   it's genuinely untried as far as the data knows. That distinction is the
   whole point of Cobber.
5. Take the best one or two suggestions and write them up as real cocktails:
   method, ratios, glass, garnish, and a name. Ground every "why" you give in
   `explain_pairing` so your reasoning matches the actual shared compounds — never
   invent flavour chemistry.
"""

mcp = FastMCP("Cobber the Mixologist", instructions=INSTRUCTIONS)


def _resolve_one(name: str) -> str | None:
    """Map a single free-text name to a known ingredient id, or None.

    Tries, in order: an exact id match, an exact display-name match (case- and
    space-insensitive), then a fuzzy match against ids and display names. This is
    the single seam that turns messy human input into ids — the future photo
    shelf-scan feature is meant to plug in right here.
    """
    needle = name.strip().lower()
    if not needle:
        return None

    # Exact id match (e.g. the caller already passed "lemon_myrtle").
    if needle in PANTRY.ingredients:
        return needle

    # Exact display-name match, ignoring case and spacing/underscores.
    flat_needle = needle.replace(" ", "").replace("_", "")
    for ingredient in PANTRY.ingredients.values():
        flat_display = ingredient.display_name.lower().replace(" ", "").replace("_", "")
        if flat_needle == flat_display:
            return ingredient.id

    # Fuzzy fallback against both ids and display names.
    candidates: dict[str, str] = {}
    for ingredient in PANTRY.ingredients.values():
        candidates[ingredient.id.replace("_", " ")] = ingredient.id
        candidates[ingredient.display_name.lower()] = ingredient.id
    matches = difflib.get_close_matches(
        needle.replace("_", " "), list(candidates), n=1, cutoff=0.7
    )
    if matches:
        return candidates[matches[0]]
    return None


def _describe(ingredient: Ingredient) -> dict:
    """Return a small, JSON-friendly summary of an ingredient for tool output."""
    summary = {
        "id": ingredient.id,
        "display_name": ingredient.display_name,
        "role": ingredient.role,
        "descriptors": list(ingredient.descriptors),
        "is_native": ingredient.is_native,
    }
    if ingredient.provisional:
        summary["provisional"] = True
    return summary


def _provisional_among(ingredient_ids: list[str]) -> list[str]:
    """The subset of ids whose data is flagged unverified - tell the user."""
    return sorted(
        ingredient_id
        for ingredient_id in set(ingredient_ids)
        if (ingredient := PANTRY.get(ingredient_id)) is not None and ingredient.provisional
    )


@mcp.tool()
def resolve_ingredients(names: list[str]) -> dict:
    """Map free-text ingredient names to known ids.

    Pass whatever the user typed ("lemon myrtle", "gin", "Peychaud's"). Returns
    ``{"resolved": {name: id}, "unknown": [names]}``. This is the single entry
    point for turning messy input into ids; resolve before calling anything else.
    """
    resolved: dict[str, str] = {}
    unknown: list[str] = []
    for name in names:
        ingredient_id = _resolve_one(name)
        if ingredient_id is None:
            unknown.append(name)
        else:
            resolved[name] = ingredient_id
    return {
        "resolved": resolved,
        "unknown": unknown,
        # Data honesty: these matched, but their flavour data is unverified.
        # Mention it to the user when they matter to the drink.
        "provisional": _provisional_among(list(resolved.values())),
    }


@mcp.tool()
def score_pairing(a: str, b: str) -> dict:
    """Score a single pairing of two ingredient ids.

    Returns ``{"harmony", "tradition", "novelty", "shared_compounds"}``. Harmony
    is how much chemistry they share; tradition is how classic the pairing is;
    novelty is high when the chemistry supports a pairing few people actually make.
    """
    harmony_score, shared = engine.harmony(a, b)
    result = {
        "harmony": round(harmony_score, 4),
        "tradition": round(engine.tradition(a, b), 4),
        "novelty": round(engine.novelty(a, b), 4),
        "shared_compounds": sorted(shared),
    }
    frontier = engine.frontier_support(a, b)
    if frontier is not None:
        result["frontier"] = frontier
    provisional = _provisional_among([a, b])
    if provisional:
        result["provisional"] = provisional
    return result


@mcp.tool()
def suggest_from_pantry(
    pantry: list[str],
    anchors: list[str],
    native_twist: bool = False,
    n: int = 5,
) -> dict:
    """Suggest drink combinations built around 2-3 nominated anchors.

    ``pantry`` and ``anchors`` are ingredient ids (resolve names first). Only
    combinations containing every anchor are returned, ranked by a blend of
    harmony and novelty, each with a chemistry rationale and a balance check. Set
    ``native_twist`` to prefer Australian natives or attach a bridging native.

    Returns ``{"suggestions": [...]}`` on success, or ``{"error": message}`` if
    the anchor list is not 2-3 ids or an anchor is not in the pantry — in which
    case relay the message and ask the user to pick 2-3 anchors.
    """
    try:
        suggestions = engine.build_around(pantry, anchors, native_twist, n)
    except ValueError as exc:
        return {"error": str(exc)}
    return {"suggestions": suggestions, "provisional": _provisional_among(pantry)}


@mcp.tool()
def explain_pairing(a: str, b: str) -> str:
    """Explain in plain language why two ingredients do or don't bridge.

    Builds the sentence purely from the shared compounds and descriptors — no
    language model. Use this to ground the "why" in any write-up so your reasoning
    matches the real chemistry.
    """
    ingredient_a = PANTRY.get(a)
    ingredient_b = PANTRY.get(b)
    if ingredient_a is None or ingredient_b is None:
        missing = a if ingredient_a is None else b
        return f"I don't know {missing!r}, so I can't speak to that pairing."

    harmony_score, shared = engine.harmony(a, b)
    name_a = ingredient_a.display_name
    name_b = ingredient_b.display_name

    if not shared:
        no_bridge = (
            f"{name_a} and {name_b} don't share any flavour compounds, so there's "
            "no natural bridge between them — you'd be relying on contrast, not "
            "harmony, to make it work."
        )
        frontier = engine.frontier_support(a, b)
        if frontier is not None and frontier.get("examples"):
            example = frontier["examples"][0]
            attribution = f" by {example['bartender']}" if example.get("bartender") else ""
            no_bridge += (
                f" That said, contrast can absolutely work: craft bartenders have "
                f"paired them {frontier['count']}x in the frontier corpus "
                f"(e.g. \"{example['drink']}\"{attribution})."
            )
        return no_bridge

    shared_list = ", ".join(sorted(shared))
    trad = engine.tradition(a, b)
    if trad >= 0.6:
        verdict = "It's a classic pairing for good reason."
    elif trad <= 0.1:
        verdict = "Hardly anyone pairs them, which makes it a fun, novel bridge."
    else:
        verdict = "It's an uncommon but well-grounded pairing."

    sentences = [
        f"{name_a} and {name_b} both carry {shared_list}, which is why the bridge "
        f"works (harmony {harmony_score:.2f}). {verdict}"
    ]

    frontier = engine.frontier_support(a, b)
    if frontier is not None and trad <= 0.3 and frontier.get("examples"):
        example = frontier["examples"][0]
        attribution = f" by {example['bartender']}" if example.get("bartender") else ""
        sentences.append(
            f"Rarely done in the canon, but craft bartenders have proven it "
            f"({frontier['count']}x in the frontier corpus, e.g. "
            f"\"{example['drink']}\"{attribution})."
        )

    provisional = _provisional_among([a, b])
    if provisional:
        names = ", ".join(provisional)
        sentences.append(
            f"Heads up: the flavour data for {names} is provisional (unverified), "
            "so treat this read as a strong hunch, not settled chemistry."
        )

    return " ".join(sentences)


@mcp.tool()
def get_native_twist(base_id: str, n: int = 3) -> list[dict]:
    """Suggest Australian natives that bridge to a given ingredient.

    Returns up to ``n`` natives ranked by how much chemistry they share with
    ``base_id``, each with the shared compounds and a one-line note. Use it to
    offer the bush-food version of a drink.
    """
    base = PANTRY.get(base_id)
    if base is None:
        return [{"error": f"I don't know {base_id!r}."}]

    scored = []
    for native_id in PANTRY.natives():
        if native_id == base_id:
            continue
        harmony_score, shared = engine.harmony(native_id, base_id)
        if shared:
            native = PANTRY.get(native_id)
            scored.append(
                {
                    "id": native_id,
                    "display_name": native.display_name,
                    "harmony": round(harmony_score, 4),
                    "shared_compounds": sorted(shared),
                    "note": (
                        f"{native.display_name} bridges to {base.display_name} via "
                        f"{', '.join(sorted(shared))}."
                    ),
                }
            )
    scored.sort(key=lambda item: item["harmony"], reverse=True)
    return scored[:n]


@mcp.tool()
def frontier_support(a: str, b: str) -> dict:
    """Check whether craft bartenders have validated a pairing in the wild.

    The frontier corpus (craft bars, competitions) is kept separate from the
    tradition score: it proves a novel pairing works in a glass without making
    it "traditional". Use this when a suggestion scores high on novelty - if
    there's support, cite it ("rarely done, but X built 'Y' on it"); if there
    isn't, say the pairing is genuinely untried as far as the data knows.

    Returns ``{"supported": bool, "count": int, "examples": [...]}``.
    """
    evidence = engine.frontier_support(a, b)
    if evidence is None:
        return {"supported": False, "count": 0, "examples": []}
    return {"supported": True, **evidence}


def main() -> None:
    """Run the Cobber MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
