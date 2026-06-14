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

from . import engine, preferences
from .data import Ingredient

PANTRY = engine.PANTRY

# Conscious category substitutions (e.g. Dubonnet served as sweet vermouth):
# kept merged for co-occurrence but surfaced at resolve time so Cobber
# announces the swap instead of hiding it. Keyed by normalized input name.
import json as _json
from pathlib import Path as _Path

def _load_proxy_notes() -> dict:
    path = _Path(__file__).resolve().parents[2] / "data" / "proxy_substitutions.json"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        raw = _json.load(handle)
    notes: dict[str, dict] = {}
    for entry in raw.values():
        alias = str(entry.get("alias", "")).strip().lower()
        if alias:
            notes[alias] = entry
    return notes

PROXY_NOTES = _load_proxy_notes()

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
   When something is unknown, only a proxy, or one you half-know, call
   `nearest_by_profile` to ground yourself in the closest profiles you DO have
   ("I don't have much on Dubonnet, but its nearest profile here is sweet
   vermouth") rather than inventing chemistry. If the user wants an ingredient
   they don't have, call `suggest_substitution` with what they want and their
   pantry — it returns role-faithful swaps (a spirit for a spirit) ranked by
   shared compounds. Both tools return empty honestly: if there's no match, say
   the ingredient is genuinely new to you, don't fabricate one.
2. The drink must be built around 2-3 nominated anchors. If they haven't picked
   2-3, ask them which two or three ingredients they want at the heart of it.
3. Call `suggest_from_pantry` with the full pantry and the anchors. Offer the
   native twist if they didn't ask for it. Each suggestion's `balance` includes
   a `structure` reading and `taste_notes` — relay any hazard notes (split risk,
   savoury counterweights) as practical bar advice, not fine print. If
   `taste_derived_for` is non-empty, the structure reading is partly an estimate
   (provisional or role-prior data): phrase it as "reads as bittersweet, though
   that's partly my estimate on X" rather than stating it as settled fact. If
   `flavour_blanks` is non-empty, those ingredients (vodka, soda, tonic...) have
   no flavour data at all, so a low harmony score is them being a blank canvas,
   not a clash — say so instead of reading the number as a bad pairing.
4. When a suggestion scores high on novelty, call `frontier_support` on its key
   pair: if craft bartenders have done it, cite the named example; if not, say
   it's genuinely untried as far as the data knows. That distinction is the
   whole point of Cobber.
5. Take the best one or two suggestions and write them up as real cocktails.
   Each suggestion now includes `template` (proportions) and `technique`
   (preparation method) fields — both learned from real recipes.
   Proportions:
   - Use `ingredient_proportions` as starting ratios (fractions 0–1, not ml).
     Pick a spirit volume (45 ml AU / 60 ml US), scale everything else.
   - If the template name is PROVISIONAL, use the structural description.
   - If no template matched, write ratios from your own bar knowledge.
   Technique:
   - The `technique` field gives you `method` (shake/stir/build/blend),
     `service` (up/rocks/highball), `glass`, `pre_steps` (dry_shake, muddle),
     and a `rationale` explaining why. Use these directly — don't invent a
     preparation method without checking this first.
   - Key rules: never shake after adding carbonation (add it last);
     egg white needs a dry shake first; citrus→shake; spirit-only→stir.
   - `rule_notes` on the technique output flags low-confidence cases —
     mention this if the technique is a strong heuristic, not a certainty.
   Method, glass, garnish, and a name come from you. Ground every "why" in
   `explain_pairing` so your reasoning matches the actual shared compounds —
   never invent flavour chemistry.
6. If any ingredient in the final recipe was flagged `provisional`, the write-up
   itself MUST carry a one-line data-confidence note (e.g. "Heads up: my miso
   profile is unverified — this bridge is a strong hunch, not settled
   chemistry"). Not optional, not fine print to drop: it is part of the recipe.
7. Close the loop — this is how Cobber learns a palate. After handing over a
   recipe, ASK the user to report back when they actually make it: what they
   liked, what they'd change, even a one-word verdict. When feedback arrives,
   call `record_tasting_feedback` (verdict: loved/liked/ok/disliked/hated).
   Cobber keeps a small taste profile for THIS install only — nothing is
   pooled or shared anywhere. At the start of a pantry session, call
   `get_taste_profile` to see who you're mixing for, and say when you're
   using it ("you've leaned bitter lately, so I went amaro-forward").
   Suggestions carry a `personal_fit` score (0.5 = neutral) once 3+ verdicts
   exist. Two honesty rules: if the feedback tool reports ingredients as
   `quarantined`, tell the user those couldn't teach the profile because
   their data is unverified; and never claim to know someone's taste off
   fewer than a handful of verdicts.
8. For culinary-crossover or novel builds, call `get_culinary_affinities` on
   an anchor ingredient to see what chefs pair it with in food contexts.
   affinity_score 0.9+ = thousands of recipes (universal consensus);
   0.8 = strong established pairing; below 0.65 = modern / emerging.
   When a result also carries `shared_compounds` and `harmony`, the aroma
   chemistry AND culinary tradition agree — a very strong signal. When those
   are absent, it's purely chef-empirical: a contrast or emergent combination
   the aroma maths can't see. Surface it as "chefs know this works together,
   even if there's no obvious compound bridge." Useful for: garnish ideas,
   unexpected modifiers, bridging the kitchen and the bar, or explaining to
   the user WHY a surprising pairing is not a wild guess.
"""

mcp = FastMCP("Cobber the Mixologist", instructions=INSTRUCTIONS)


def _resolve_one(name: str) -> tuple[str | None, bool]:
    """Map a single free-text name to ``(ingredient id or None, via_fuzzy)``.

    Tries, in order: an exact id match, an exact display-name match (case- and
    space-insensitive), then a fuzzy match against ids and display names. This is
    the single seam that turns messy human input into ids — the future photo
    shelf-scan feature is meant to plug in right here.

    The fuzzy cutoff is deliberately high (0.84): it still catches typos
    ("campri" -> campari) but refuses sound-alike coercions — the first live
    test of this resolver silently turned "rose water" into soda water at the
    old 0.7 cutoff, which is exactly the never-guess rule being broken at
    runtime. Any fuzzy match that does fire is reported, not hidden.
    """
    needle = name.strip().lower()
    if not needle:
        return None, False

    # Exact id match (e.g. the caller already passed "lemon_myrtle").
    if needle in PANTRY.ingredients:
        return needle, False

    # Exact display-name match, ignoring case and spacing/underscores.
    flat_needle = needle.replace(" ", "").replace("_", "")
    for ingredient in PANTRY.ingredients.values():
        flat_display = ingredient.display_name.lower().replace(" ", "").replace("_", "")
        if flat_needle == flat_display:
            return ingredient.id, False

    # Fuzzy fallback against both ids and display names.
    candidates: dict[str, str] = {}
    for ingredient in PANTRY.ingredients.values():
        candidates[ingredient.id.replace("_", " ")] = ingredient.id
        candidates[ingredient.display_name.lower()] = ingredient.id
    matches = difflib.get_close_matches(
        needle.replace("_", " "), list(candidates), n=1, cutoff=0.84
    )
    if matches:
        return candidates[matches[0]], True
    return None, False


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
    substitutions: list[dict] = []
    fuzzy_matched: dict[str, str] = {}
    for name in names:
        ingredient_id, via_fuzzy = _resolve_one(name)
        proxy = PROXY_NOTES.get(name.strip().lower())
        if ingredient_id is None and proxy is not None:
            # A known category proxy (Dubonnet -> sweet vermouth): resolve it to
            # the stand-in rather than calling it unknown, and announce the swap.
            ingredient_id = proxy["served_as"]
            via_fuzzy = False
        if ingredient_id is None:
            unknown.append(name)
        else:
            resolved[name] = ingredient_id
            if via_fuzzy:
                fuzzy_matched[name] = ingredient_id
        if proxy is not None:
            substitutions.append({"input": name, "served_as": proxy["served_as"], "note": proxy["note"]})
    return {
        "resolved": resolved,
        "unknown": unknown,
        # Data honesty: these matched, but their flavour data is unverified.
        # Mention it to the user when they matter to the drink.
        "provisional": _provisional_among(list(resolved.values())),
        # Conscious category swaps to announce ("no exact Dubonnet - scoring as
        # sweet vermouth"), not to hide.
        "substitutions": substitutions,
        # Approximate (typo-level) matches: confirm with the user if surprising.
        "fuzzy_matched": fuzzy_matched,
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
    # Personal layer (additive): score each suggestion against this install's
    # tasting history. A corrupt or missing local preference file must never
    # break the core suggestion path, hence the broad guard.
    try:
        prefs = preferences.load_prefs()
        if len(prefs.get("feedback", [])) >= preferences.MIN_FEEDBACK_FOR_FIT:
            for suggestion in suggestions:
                suggestion["personal_fit"] = preferences.personal_fit(
                    suggestion["ingredients"], prefs
                )
    except Exception:
        pass
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
def nearest_by_profile(ingredient_id: str, n: int = 5) -> dict:
    """Find the known ingredients whose flavour chemistry is closest to one id.

    Use this when an ingredient is thin, a proxy, or you only half-know it: it
    returns the closest profiles Cobber actually has, ranked by shared compounds,
    so you can reason from a real neighbour ("I don't have much on Dubonnet, but
    its closest profile here is sweet vermouth"). Deterministic — no lookup on the
    network, just the compound maths.

    Returns ``{"nearest": [{"id", "display_name", "role", "harmony",
    "shared_compounds"}, ...]}``. The list is empty if the id is unknown or has no
    compound profile to compare — in which case say so plainly rather than
    guessing; a genuinely new ingredient needs a build-time entry, not invention.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return {
            "nearest": [],
            "note": f"I don't know {ingredient_id!r}, so I can't find a nearest profile.",
        }
    nearest = engine.nearest_by_profile(ingredient_id, n=n)
    result = {"nearest": nearest}
    if not nearest:
        result["note"] = (
            f"I have no compound profile for {ingredient.display_name}, so I can't "
            "place it by chemistry — it needs a verified entry before I can reason about it."
        )
    return result


@mcp.tool()
def suggest_substitution(ingredient_id: str, pantry: list[str], n: int = 3) -> dict:
    """Find what in the user's pantry can stand in for an ingredient they don't have.

    Pass the ingredient they *want* (``ingredient_id``) and what they *have*
    (``pantry``, ids — resolve names first). Returns role-faithful swaps only:
    a spirit for a spirit, an acid for an acid, ranked by shared chemistry — so
    you can say "no green Chartreuse, but your yellow Chartreuse is the closest
    thing on your shelf, and here's the compound it shares". Deterministic, no
    network lookup.

    Returns ``{"substitutes": [{"id", "display_name", "role", "harmony",
    "shared_compounds"}, ...]}``. Empty when the target is unknown/profile-less or
    nothing in the pantry shares its role and any chemistry — say so plainly. For a
    looser, cross-role option, fall back to ``nearest_by_profile`` and tell the
    user the role differs.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return {
            "substitutes": [],
            "note": f"I don't know {ingredient_id!r}, so I can't find a stand-in for it.",
        }
    substitutes = engine.suggest_substitution(ingredient_id, pantry, n=n)
    result = {"substitutes": substitutes}
    if not substitutes:
        result["note"] = (
            f"Nothing in the pantry plays {ingredient.display_name}'s role "
            f"({ingredient.role}) with shared chemistry — you'd be reaching for "
            "contrast, not a true swap."
        )
    return result


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


@mcp.tool()
def suggest_technique(ingredient_ids: list[str]) -> dict:
    """Suggest preparation technique and service style for a set of ingredient ids.

    Returns ``{"method", "service", "glass", "ice_in_glass", "pre_steps",
    "rationale", "matched_rule"}`` — plus ``"carbonation_note"`` when the build
    involves a carbonated top-up.

    Key signals used: egg white (dry shake first), carbonation (build/highball,
    never shake after adding), acid/citrus (shake), dairy (shake), fresh herbs
    (muddle first), spirit-only (stir). Use this to choose the preparation method
    rather than inventing one; the rationale field explains the reasoning.
    """
    result = engine.suggest_technique(ingredient_ids)
    if result is None:
        return {
            "method": "build",
            "service": "rocks",
            "glass": "rocks",
            "ice_in_glass": True,
            "pre_steps": [],
            "rationale": "No technique rules loaded — default build over ice.",
            "matched_rule": "fallback",
        }
    return result


@mcp.tool()
def record_tasting_feedback(
    drink_name: str,
    ingredients: list[str],
    verdict: str,
    liked: list[str] | None = None,
    could_improve: str = "",
    notes: str = "",
) -> dict:
    """Record the user's verdict on a drink they actually made.

    ``verdict`` is one of loved/liked/ok/disliked/hated; ``liked`` holds
    free-text aspects ("the smoky finish"), ``could_improve`` what they'd
    change ("less sweet next time"). Pass ingredient names as the user said
    them — they are resolved to known ids here.

    This writes ONLY to this install's local preference document
    (~/.cobber/preferences.json) — never to Cobber's shared flavour data, and
    nothing is pooled across users. The response says which ingredients were
    ``quarantined`` (recorded but not learned from, because their data is
    unverified) — relay that to the user honestly.
    """
    resolved_ids: list[str] = []
    unresolved: list[str] = []
    for name in ingredients:
        ingredient_id, _ = _resolve_one(name)
        if ingredient_id is None:
            unresolved.append(name)
        else:
            resolved_ids.append(ingredient_id)
    try:
        return preferences.record_feedback(
            drink_name=drink_name,
            ingredient_ids=resolved_ids,
            verdict=verdict,
            liked=liked,
            could_improve=could_improve,
            notes=notes,
            unresolved_names=unresolved or None,
        )
    except ValueError as exc:
        return {"error": str(exc)}


@mcp.tool()
def get_taste_profile() -> dict:
    """What Cobber has learned about THIS install's palate from past feedback.

    Returns feedback_count, axis_weights (e.g. bitter +0.4 means the user has
    liked bitter-leaning drinks), top liked/disliked ingredients, and the
    unattributed list (feedback Cobber refused to learn from because the
    ingredient data is unverified). Call at the start of a pantry session to
    bias direction — and say so out loud when you do. With fewer than 3
    verdicts, treat the profile as anecdote, not knowledge.
    """
    prefs = preferences.load_prefs()
    summary = preferences.profile_summary(prefs)
    if summary["feedback_count"] == 0:
        summary["note"] = (
            "No tasting feedback recorded yet on this install — ask the user "
            "to report back when they make a drink."
        )
    return summary


@mcp.tool()
def get_culinary_affinities(ingredient_id: str, n: int = 10) -> dict:
    """Return culinary food-pairing affinities for one ingredient.

    Based on the Ahn 2011 flavor network (recipe co-occurrences from global
    recipe databases: Epicurious, allrecipes, etc.) and The Flavor Bible.
    Distinct from cocktail tradition — these are chef affinities, not
    bartender canon. Use when exploring novel or culinary-crossover builds,
    checking garnish ideas, or explaining why a surprising pairing isn't a
    wild guess.

    Returns ``{"affinities": [...], "note"?: str}``. Each affinity carries:
    id, display_name, role, affinity_score (0–1), cuisine_contexts, and note.
    When Cobber's aroma DB contains a compound bridge, shared_compounds and
    harmony are also returned — meaning the chemistry AND culinary tradition
    agree. When absent, the pairing is chef-empirical: validated by recipe
    volume, not compound analysis.

    Returns an empty list honestly when no affinities are mapped for this
    ingredient yet — do not fabricate a culinary pairing.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return {
            "affinities": [],
            "note": f"I don't know {ingredient_id!r}.",
        }
    affinities = engine.culinary_affinities(ingredient_id, n=n)
    result: dict = {"affinities": affinities}
    if not affinities:
        result["note"] = (
            f"No culinary pairing data mapped for {ingredient.display_name} yet. "
            "This is a data gap, not a signal that the ingredient has no affinities."
        )
    return result


def main() -> None:
    """Run the Cobber MCP server over stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
