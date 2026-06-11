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

Workflow when someone tells you what they have:
1. Call `resolve_ingredients` on their free-text list to turn it into known ids.
   Mention anything that came back unknown and offer to work around it.
2. The drink must be built around 2-3 nominated anchors. If they haven't picked
   2-3, ask them which two or three ingredients they want at the heart of it.
3. Call `suggest_from_pantry` with the full pantry and the anchors. Offer the
   native twist if they didn't ask for it.
4. Take the best one or two suggestions and write them up as real cocktails:
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
    return {
        "id": ingredient.id,
        "display_name": ingredient.display_name,
        "role": ingredient.role,
        "descriptors": list(ingredient.descriptors),
        "is_native": ingredient.is_native,
    }


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
    return {"resolved": resolved, "unknown": unknown}


@mcp.tool()
def score_pairing(a: str, b: str) -> dict:
    """Score a single pairing of two ingredient ids.

    Returns ``{"harmony", "tradition", "novelty", "shared_compounds"}``. Harmony
    is how much chemistry they share; tradition is how classic the pairing is;
    novelty is high when the chemistry supports a pairing few people actually make.
    """
    harmony_score, shared = engine.harmony(a, b)
    return {
        "harmony": round(harmony_score, 4),
        "tradition": round(engine.tradition(a, b), 4),
        "novelty": round(engine.novelty(a, b), 4),
        "shared_compounds": sorted(shared),
    }


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
    return {"suggestions": suggestions}


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
        return (
            f"{name_a} and {name_b} don't share any flavour compounds, so there's "
            "no natural bridge between them — you'd be relying on contrast, not "
            "harmony, to make it work."
        )

    shared_list = ", ".join(sorted(shared))
    trad = engine.tradition(a, b)
    if trad >= 0.6:
        verdict = "It's a classic pairing for good reason."
    elif trad <= 0.1:
        verdict = "Hardly anyone pairs them, which makes it a fun, novel bridge."
    else:
        verdict = "It's an uncommon but well-grounded pairing."

    return (
        f"{name_a} and {name_b} both carry {shared_list}, which is why the bridge "
        f"works (harmony {harmony_score:.2f}). {verdict}"
    )


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


def main() -> None:
    """Run the Cobber MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
