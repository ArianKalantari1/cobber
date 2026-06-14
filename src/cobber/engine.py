"""Flavour-chemistry engine for Cobber the Mixologist.

These are pure functions over the loaded :class:`~cobber.data.Pantry`. They do
the deterministic maths — which ingredients share flavour compounds, how
traditional a pairing is, how novel it is, whether a combination is roughly
balanced — and nothing else. No MCP, no I/O, no language model, no network.

The design split that matters: **the chemistry lives here; the creativity lives
in the host Claude.** This module will happily tell you that gin and lemon myrtle
share citral and that almost nobody pairs them; it will never write you a recipe.

The pantry is loaded once at import time and shared by every function, which is
why the public signatures take plain ids rather than a pantry argument.
"""

from __future__ import annotations

import math
from itertools import combinations

from . import data

# Loaded once. The engine is read-only over this, so a module-level instance is
# safe and keeps the public functions matching the spec's id-only signatures.
PANTRY = data.load_pantry()

# How many extra pantry ingredients (beyond the anchors) a suggested drink may
# add. Real drinks are short, so we keep candidate combinations small.
MAX_ADDITIONS = 2

# Ingredients that contribute perceivable body / mouthfeel through one of three
# distinct mechanisms:
#   - fat emulsion  (cream, butter, egg yolk, coconut, milk)
#   - protein foam  (egg white, whole egg)
#   - dissolved-solids / sugar-concentration viscosity  (honey, maple syrup,
#     orgeat, port, sherry, pedro_ximenez, agave)
# When none of these are present and the fat axis is also negligible, the build
# will drink thin — balance() surfaces a texture warning so the host can act.
_BODY_CONTRIBUTORS: frozenset[str] = frozenset({
    # fat-based
    "cream", "butter", "milk", "coconut", "egg_yolk",
    # protein foam
    "egg_white", "whole_egg",
    # dissolved-solids viscosity (concentrated sugars / fortified wines)
    "honey", "maple_syrup", "orgeat", "agave",
    "port", "sherry", "pedro_ximenez",
})


def profile(ingredient_id: str) -> set[str]:
    """Return the set of flavour compounds for an ingredient id.

    For raw ingredients this is their declared compound list; for composites it
    is the union of their botanicals' compounds (already derived at load time).
    Returns an empty set for an unknown id or one with no known compounds.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return set()
    return set(ingredient.compounds)


def harmony(a: str, b: str) -> tuple[float, set[str]]:
    """Return the Jaccard similarity of two ingredients and their shared compounds.

    Harmony is ``|A ∩ B| / |A ∪ B|`` over the two compound sets — the fraction of
    their combined chemistry that they have in common. A high value means the two
    ingredients literally share aroma molecules, which is what makes a flavour
    bridge work. Returns ``(0.0, set())`` if either ingredient has no profile.
    """
    profile_a = profile(a)
    profile_b = profile(b)
    if not profile_a or not profile_b:
        return 0.0, set()
    shared = profile_a & profile_b
    union = profile_a | profile_b
    return len(shared) / len(union), shared


def tradition(a: str, b: str) -> float:
    """Return how classic a pairing is, from 0.0 (novel) to ~1.0 (canonical).

    A lookup in the curated tradition table, order-independent. Any pair that is
    not in the table defaults to 0.0 — i.e. "nobody does this".
    """
    return PANTRY.tradition.get(frozenset((a, b)), 0.0)


def novelty(a: str, b: str) -> float:
    """Return the novelty signal for a pairing: ``harmony * (1 - tradition)``.

    This is the interesting number. It is high only when the chemistry supports
    the pairing (they share compounds) *and* few people actually make it — a
    promising, under-explored bridge rather than a tired classic or a random clash.
    """
    return harmony(a, b)[0] * (1.0 - tradition(a, b))


def culinary_affinities(ingredient_id: str, n: int = 10) -> list[dict]:
    """Return the top culinary food-pairing affinities for one ingredient id.

    Looks up the culinary pairs table (Ahn 2011 food-recipe co-occurrences, The
    Flavor Bible). Results are sorted by affinity_score descending. Each item
    carries the partner ingredient's id, display_name, role, affinity_score,
    cuisine_contexts, and note from the data file.

    When a compound bridge exists between the two ingredients in Cobber's aroma
    DB, ``shared_compounds`` and ``harmony`` are also included — chemistry and
    culinary use point the same way. Weight it by the ``harmony`` value, though:
    a single shared compound (low harmony) is a faint corroboration, not proof;
    a high harmony alongside a strong affinity is the genuinely strong signal.

    Returns ``[]`` when the ingredient has no culinary affinities mapped yet.
    This is an honest empty — not every ingredient has food-science pairing data
    yet; the host should say so rather than fabricating affinities.
    """
    results: list[dict] = []
    for pair_key, pair_data in PANTRY.culinary.items():
        if ingredient_id not in pair_key:
            continue
        other_ids = [pid for pid in pair_key if pid != ingredient_id]
        if not other_ids:
            continue
        other_id = other_ids[0]
        other = PANTRY.get(other_id)
        if other is None:
            continue
        item: dict = {
            "id": other_id,
            "display_name": other.display_name,
            "role": other.role,
            "affinity_score": pair_data["affinity_score"],
            "cuisine_contexts": pair_data["cuisine_contexts"],
            "note": pair_data["note"],
        }
        harmony_score, shared = harmony(ingredient_id, other_id)
        if shared:
            item["shared_compounds"] = sorted(shared)
            item["harmony"] = round(harmony_score, 4)
        results.append(item)
    results.sort(key=lambda x: x["affinity_score"], reverse=True)
    return results[:n]


def frontier_support(a: str, b: str) -> dict | None:
    """Return craft-corpus evidence for a pairing, or ``None`` if there is none.

    The frontier table holds pairings seen in the craft/competition corpora
    with attribution (``{"count": int, "examples": [{"drink", "bartender"?}]}``).
    It deliberately does not feed the tradition score: a working bartender
    using a pairing is *validation* that a novel idea works in a glass, not
    evidence that it is canon. High novelty + frontier support is the
    strongest recommendation Cobber can make.
    """
    return PANTRY.frontier.get(frozenset((a, b)))


def nearest_by_profile(
    ingredient_id: str,
    n: int = 5,
    candidates: list[str] | None = None,
) -> list[dict]:
    """Return the known ingredients whose chemistry is closest to ``ingredient_id``.

    Pure harmony lookup: for every candidate, compute the shared-compound Jaccard
    against the target and return those that share *something*, ranked by harmony.
    This is the deterministic answer to Ari's "Cobber should look things up" — when
    an entry is thin or a proxy (Dubonnet, a minimal native), Cobber can still say
    "the closest profiles I know are X and Y" instead of dead-ending, without any
    network or LLM call.

    ``candidates`` restricts the search pool (e.g. to a user's pantry, for
    substitution); the default searches every known ingredient. The target itself
    and anything with no shared compounds are excluded. Returns ``[]`` when the
    target is unknown or has no compound profile of its own to compare — honestly
    empty rather than a fabricated neighbour.

    Each item is ``{"id", "display_name", "role", "harmony", "shared_compounds"}``.
    """
    target = PANTRY.get(ingredient_id)
    if target is None or not target.compounds:
        return []

    pool = candidates if candidates is not None else PANTRY.all_ids()
    scored: list[dict] = []
    for candidate_id in pool:
        if candidate_id == ingredient_id:
            continue
        candidate = PANTRY.get(candidate_id)
        if candidate is None:
            continue
        harmony_score, shared = harmony(ingredient_id, candidate_id)
        if shared:
            scored.append(
                {
                    "id": candidate_id,
                    "display_name": candidate.display_name,
                    "role": candidate.role,
                    "harmony": round(harmony_score, 4),
                    "shared_compounds": sorted(shared),
                }
            )
    scored.sort(key=lambda item: item["harmony"], reverse=True)
    return scored[:n]


def suggest_substitution(
    ingredient_id: str,
    pantry_ids: list[str],
    n: int = 3,
) -> list[dict]:
    """Suggest what in a user's pantry can stand in for an ingredient they lack.

    A role-faithful nearest-profile lookup: it only offers pantry items that play
    the *same role* as the target (a spirit for a spirit, an acid for an acid) and
    then ranks them by shared chemistry. So "you want a Last Word but have no green
    Chartreuse" comes back with the closest aromatic you actually own, not a syrup
    that happens to share a compound.

    ``ingredient_id`` is the thing they want (it need not be in the pantry — that's
    the point); ``pantry_ids`` is what they have. Returns ``[]`` — honestly, not a
    forced swap — when the target is unknown/profile-less or nothing in the pantry
    shares both its role and any chemistry. For a cross-role option, the host can
    fall back to :func:`nearest_by_profile` over the whole pantry and say the role
    differs.

    Each item matches :func:`nearest_by_profile`'s shape.
    """
    target = PANTRY.get(ingredient_id)
    if target is None or not target.compounds:
        return []
    same_role_pool = [
        pid
        for pid in pantry_ids
        if pid != ingredient_id
        and (ing := PANTRY.get(pid)) is not None
        and ing.role == target.role
    ]
    return nearest_by_profile(ingredient_id, n=n, candidates=same_role_pool)


# Coarse taste prior per role, used when an ingredient has no curated `taste`
# field. Deliberately conservative: spirits/aromatics/herbs/mixers contribute
# nothing rather than a guess. Derived values are flagged in balance() output.
ROLE_TASTE_PRIOR: dict[str, dict[str, float]] = {
    "sour": {"sour": 0.7},
    "sweet": {"sweet": 0.7},
    "bitter": {"bitter": 0.7},
    "dairy": {"fat": 0.6},
    "fruit": {"sweet": 0.3, "sour": 0.3},
    "seasoning": {"salty": 0.4},
    "spirit": {},
    "aromatic": {},
    "herb": {},
    "mixer": {},
}


def taste_profile(ingredient_id: str) -> tuple[dict[str, float], bool]:
    """Return ``(axis -> value, estimated)`` for one ingredient.

    ``estimated=False`` only when the taste data is both curated AND non-provisional
    (i.e. Ari has signed off). Two cases produce ``estimated=True``:

    1. Provisional taste: values are a bartender estimate, not verified chemistry.
       Used verbatim (better than a generic role prior) but flagged so the
       balance output can surface the caveat.
    2. No taste field at all: a coarse role prior stands in.

    The distinction between these two cases is not exposed here — callers that
    need it (e.g. to separate "strong hunch" from "generic guess") should inspect
    ``ingredient.provisional`` directly.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return {}, True
    if ingredient.taste:
        return dict(ingredient.taste), ingredient.provisional
    return dict(ROLE_TASTE_PRIOR.get(ingredient.role, {})), True


def balance(ingredient_ids: list[str]) -> dict:
    """Run a deliberately simple V1 balance check over roles and taste axes.

    A plausible drink has a base spirit and at least one balancing role
    (sour / sweet / bitter), and is not built entirely from a single role.
    On top of the role check, taste axes are summed across the combination to
    read its structure (sour-balanced / bittersweet / savoury) and to flag
    real bartending hazards (dairy + acid splits; savoury with no
    counterweight; chemesthetic heat from the spice axis; no body). This is a
    sanity heuristic, **not** a recipe balancer — it checks the shape of a
    combination, not its ratios. The spice axis sits outside the structure
    reading on purpose: heat is a parallel sensation a drink is balanced
    *against*, not one of the sweet/sour/bitter/savoury shapes. Body is
    flagged when fat < 0.3 AND no ingredient from ``_BODY_CONTRIBUTORS`` is
    present — three mechanisms (fat emulsion, protein foam, dissolved-solids
    viscosity) all satisfy the check.

    Returns the original ``{"ok", "roles_present", "warning"}`` plus
    ``"taste_axes"`` (summed values), ``"structure"`` (a one-word reading),
    ``"taste_notes"`` (hazards/accents) and ``"taste_derived_for"`` (which
    ingredients used the role prior OR have only provisional taste data — i.e.
    any ingredient whose taste contribution is an estimate rather than verified).
    """
    roles = []
    for ingredient_id in ingredient_ids:
        ingredient = PANTRY.get(ingredient_id)
        if ingredient is not None:
            roles.append(ingredient.role)
    roles_present = sorted(set(roles))

    warning: str | None = None
    has_spirit = "spirit" in roles_present
    balancing = {"sour", "sweet", "bitter"} & set(roles_present)

    if len(roles_present) <= 1:
        warning = "Everything here plays the same role; the drink will feel flat."
    elif not has_spirit:
        warning = "No base spirit — fine for a low/no-alcohol drink, but note it."
    elif not balancing:
        warning = "No sour, sweet or bitter element to balance the spirit."

    ok = has_spirit and bool(balancing) and len(roles_present) > 1

    # Taste-axis layer: sum each axis over the combination.
    axes: dict[str, float] = {}
    derived_for: list[str] = []
    for ingredient_id in ingredient_ids:
        profile_axes, derived = taste_profile(ingredient_id)
        if derived and profile_axes:
            derived_for.append(ingredient_id)
        for axis, value in profile_axes.items():
            axes[axis] = round(axes.get(axis, 0.0) + value, 2)

    sour = axes.get("sour", 0.0)
    sweet = axes.get("sweet", 0.0)
    bitter = axes.get("bitter", 0.0)
    salty = axes.get("salty", 0.0)
    umami = axes.get("umami", 0.0)
    fat = axes.get("fat", 0.0)
    spice = axes.get("spice", 0.0)
    savoury = salty + umami

    if savoury >= 0.8:
        structure = "savoury"
    elif sour >= 0.5 and sweet >= 0.5:
        structure = "sour-balanced"
    elif bitter >= 0.5 and sweet >= 0.5:
        structure = "bittersweet"
    elif sour >= 0.5:
        structure = "tart"
    elif bitter >= 0.5:
        structure = "bitter-forward"
    elif sweet >= 0.5:
        structure = "sweet-forward"
    else:
        structure = "spirit-forward"

    taste_notes: list[str] = []
    if fat >= 0.5 and sour >= 0.5:
        taste_notes.append(
            "Dairy/fat meets acid: split risk — handle it (flip, batch-and-strain, "
            "or clarify) or keep them apart."
        )
    if savoury >= 0.8 and sour < 0.3 and sweet < 0.3:
        taste_notes.append(
            "Savoury-heavy with no acid or sugar counterweight; it will read as broth."
        )
    if 0.0 < salty <= 0.3:
        taste_notes.append(
            "Salt at accent level: it will amplify sweetness and round off bitterness."
        )
    if spice >= 0.5:
        taste_notes.append(
            "Real heat here (chilli/ginger chemesthesis, not bitterness): it builds "
            "as you drink — lean on sweetness or acid to balance it, and a little "
            "sugar or fat tames the burn."
        )
    has_body = fat >= 0.3 or bool(
        _BODY_CONTRIBUTORS & set(ingredient_ids)
    )
    if not has_body:
        taste_notes.append(
            "No body: nothing here contributes viscosity or mouthfeel. It will "
            "drink thin. Add egg white (protein foam), honey or orgeat (sugar "
            "viscosity), cream (fat), or a fortified wine like port or PX sherry "
            "(dissolved solids) to give it texture."
        )

    return {
        "ok": ok,
        "roles_present": roles_present,
        "warning": warning,
        "taste_axes": {axis: value for axis, value in sorted(axes.items()) if value > 0},
        "structure": structure,
        "taste_notes": taste_notes,
        "taste_derived_for": sorted(derived_for),
    }


# ---------------------------------------------------------------------------
# Proportion template matching
# ---------------------------------------------------------------------------

# The templates use a different role vocabulary from Cobber's ingredient roles
# (which are designed for taste-balance rather than structural shape). This
# mapping bridges them. Per-ingredient overrides handle the cases where a
# Cobber role maps to two distinct template roles (e.g. "bitter" covers both
# aromatic bitters like Angostura and amaro-class modifiers like Campari).
_TEMPLATE_ROLE_BY_COBBER_ROLE: dict[str, str] = {
    "spirit":    "spirit",
    "sour":      "acid",
    "sweet":     "sweet",       # syrups, honey; some liqueurs also here (see overrides)
    "bitter":    "amaro",       # composites: Campari, Fernet, Cynar, etc.
    "dairy":     "egg_cream",
    "mixer":     "lengthener",
    "fruit":     "juice_mixer",
    "aromatic":  "vermouth_fortified",  # vermouths, aromatized wines
    "herb":      "other",
    "seasoning": "other",
}

# Per-ingredient overrides for cases the role mapping can't distinguish.
# Cobber's "bitter" role includes both small-dose aromatic bitters (which are
# excluded from the template vector as seasoning) and amaro-class modifiers;
# Cobber's "sweet" role includes both syrups and spirit-based liqueurs.
_TEMPLATE_ROLE_OVERRIDES: dict[str, str] = {
    # Small-dose aromatic bitters: excluded from template vector
    "angostura_bitters":        "bitter",
    "peychauds_bitters":        "bitter",
    "orange_bitters":           "bitter",
    "celery_bitters":           "bitter",
    # Cobber "sweet"-role composites that are liqueurs, not syrups
    "triple_sec":               "liqueur",
    "cointreau":                "liqueur",
    "maraschino":               "liqueur",
    "coffee_liqueur":           "liqueur",
    "elderflower_liqueur":      "liqueur",
    "sloe_gin":                 "liqueur",
    "benedictine":              "liqueur",
    "yellow_chartreuse":        "amaro",   # chartreuse is amaro-class
    # Sweet-bright aperitivi: liqueur slot in builds like Paper Plane,
    # not the bitter backbone (Campari/Cynar stay as amaro)
    "aperol":                   "liqueur",
}

# Template roles that are tracked but excluded from distance matching
# (they are seasoning/trace elements in real drinks).
_TEMPLATE_ROLES_EXCLUDED = {"bitter", "other"}

# The 9 template roles in the same order as proportion_templates.json centroid
_TEMPLATE_ROLE_ORDER = [
    "spirit", "liqueur", "amaro", "vermouth_fortified",
    "acid", "sweet", "juice_mixer", "lengthener", "egg_cream",
]


def _ingredient_template_role(ingredient_id: str) -> str:
    """Map a Cobber ingredient id to its structural template role."""
    if ingredient_id in _TEMPLATE_ROLE_OVERRIDES:
        return _TEMPLATE_ROLE_OVERRIDES[ingredient_id]
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return "other"
    return _TEMPLATE_ROLE_BY_COBBER_ROLE.get(ingredient.role, "other")


def suggest_template(ingredient_ids: list[str]) -> dict | None:
    """Return the best-matching proportion template for this ingredient set.

    Maps each ingredient to a template role and finds the nearest template
    centroid in role space, using equal proportions as the prior (since the
    engine doesn't know actual poured volumes).

    Returns a dict with the matched template's id, name, centroid proportions,
    and suggested ingredient-level proportions, or ``None`` if no templates
    are loaded or all ingredients are in excluded roles.
    """
    if not PANTRY.templates:
        return None

    # Build the role distribution assuming equal proportions
    role_counts: dict[str, float] = {}
    for ing_id in ingredient_ids:
        role = _ingredient_template_role(ing_id)
        if role not in _TEMPLATE_ROLES_EXCLUDED:
            role_counts[role] = role_counts.get(role, 0.0) + 1.0

    if not role_counts:
        return None

    total = sum(role_counts.values())
    input_vec = {r: role_counts.get(r, 0.0) / total for r in _TEMPLATE_ROLE_ORDER}

    # Pre-filter: exclude templates whose centroid contains a role at ≥ 10%
    # that is entirely absent from the input combination.  Without this, a
    # spirit-only/spirit+sweet build (Old Fashioned) matches the Sour template
    # because no acid in the input means the Sour's acid centroid goes
    # "unpenalised" in direction while the spirit column happens to align.
    roles_absent = {r for r in _TEMPLATE_ROLE_ORDER if input_vec.get(r, 0.0) < 0.01}

    best_template: dict | None = None
    best_dist = float("inf")

    for template in PANTRY.templates:
        centroid = template.get("centroid", {})
        # Skip any template that requires a role ≥ 10% which is absent here
        if any(centroid.get(r, 0.0) >= 0.10 for r in roles_absent):
            continue
        dist = math.sqrt(
            sum(
                (input_vec.get(r, 0.0) - centroid.get(r, 0.0)) ** 2
                for r in _TEMPLATE_ROLE_ORDER
            )
        )
        if dist < best_dist:
            best_dist = dist
            best_template = template

    if best_template is None:
        return None

    centroid = best_template["centroid"]

    # Map centroid role proportions back to specific ingredients.
    # When multiple ingredients share a role, divide the role's proportion equally.
    role_to_ings: dict[str, list[str]] = {}
    for ing_id in ingredient_ids:
        role = _ingredient_template_role(ing_id)
        if role not in _TEMPLATE_ROLES_EXCLUDED and role in centroid:
            role_to_ings.setdefault(role, []).append(ing_id)

    ingredient_proportions: dict[str, float] = {}
    for role, ings in role_to_ings.items():
        role_share = centroid.get(role, 0.0)
        per_ing = round(role_share / len(ings), 3)
        for ing_id in ings:
            ingredient_proportions[ing_id] = per_ing

    return {
        "id": best_template["id"],
        "suggested_name": best_template["suggested_name"],
        "recipe_count": best_template["recipe_count"],
        "role_proportions": {r: v for r, v in centroid.items() if v >= 0.02},
        "ingredient_proportions": ingredient_proportions,
        "ratio": best_template["dominant_ratio"],
        "dominant_roles": best_template["dominant_roles"],
        "notes": best_template.get("notes", ""),
    }


# ---------------------------------------------------------------------------
# Technique suggestion
# ---------------------------------------------------------------------------

# Ingredient IDs that are carbonated lengtheners — must be built, never shaken.
# Role alone is insufficient: tonic is "bitter", ginger_ale is "sweet", sparkling_wine
# is "aromatic" — so we check by id and display-name fragment.
_CARBONATED_IDS: frozenset[str] = frozenset({
    "soda_water", "tonic_water", "ginger_ale", "ginger_beer", "sparkling_wine",
})
_CARBONATED_NAME_FRAGMENTS: tuple[str, ...] = (
    "soda", "tonic", "champagne", "prosecco", "cava", "sparkling",
    "ginger beer", "beer", "cider", "lemonade",
)

# Herbs that are typically muddled before building/shaking.
_MUDDLE_HERB_IDS: frozenset[str] = frozenset({
    "mint", "native_river_mint", "basil", "sage", "rosemary", "thyme",
    "coriander_leaf",
})


def _is_carbonated(ingredient_id: str) -> bool:
    if ingredient_id in _CARBONATED_IDS:
        return True
    ing = PANTRY.get(ingredient_id)
    if ing is None:
        return False
    name = ing.display_name.lower()
    return any(frag in name for frag in _CARBONATED_NAME_FRAGMENTS)


def _detect_technique_signals(ingredient_ids: list[str]) -> dict[str, bool]:
    """Return technique-relevant signals for a set of Cobber ingredient ids."""
    has_egg_white = False
    has_dairy     = False
    has_acid      = False
    has_carb      = False
    has_herb      = False

    non_technique_roles = {"bitter", "seasoning"}

    for ing_id in ingredient_ids:
        ing = PANTRY.get(ing_id)
        if ing is None:
            continue
        role = ing.role

        if role == "sour":
            has_acid = True
        elif role == "dairy":
            has_dairy = True
            if ing_id == "egg_white":
                has_egg_white = True
        elif role == "herb":
            if ing_id in _MUDDLE_HERB_IDS:
                has_herb = True

        if _is_carbonated(ing_id):
            has_carb = True

    return {
        "has_egg_white":            has_egg_white,
        # Dairy split: cream+acid → shake (cream sours, emulsify the dairy);
        # cream alone → build over rocks (White Russian).
        "has_dairy_and_acid":       has_dairy and has_acid and not has_egg_white,
        "has_dairy_no_acid":        has_dairy and not has_acid and not has_egg_white,
        "has_herb_acid_and_carb":   has_herb and has_acid and has_carb,
        "has_acid_and_carb":        has_acid and has_carb and not has_herb,
        "has_acid":                 has_acid and not has_dairy,
        "has_carb_only":            has_carb and not has_acid and not has_dairy,
        "has_herb_no_acid":         has_herb and not has_acid,
        "spirit_only": (
            not has_acid and not has_dairy and not has_carb and not has_herb
        ),
    }


def suggest_technique(ingredient_ids: list[str]) -> dict | None:
    """Suggest preparation technique for a set of ingredient ids.

    Returns a dict with method, service, glass, optional pre_steps, rationale,
    and the matched rule id — or None if no rules are loaded.

    Priority order (first matching rule wins):
      1.  egg_white           → dry shake then shake, up/coupe
      2.  highball_build      → build, carbonation only (Highball, G&T)
      3.  mojito_muddle_build → muddle + build + top w/ soda (Mojito family)
      4.  sour_highball       → shake base + top w/ soda, highball (Collins)
      5.  dairy_acid_shake    → shake, up/coupe (cream sours)
      6.  dairy_build         → build, rocks/big ice (White Russian)
      7.  acid_shake          → shake, up/coupe (Daiquiri, Whiskey Sour)
      8.  herb_muddle_build   → muddle + build, rocks (Mint Julep)
      9.  spirit_only_stir    → stir, rocks (Old Fashioned, Negroni, Manhattan)
      10. default             → build, rocks
    """
    if not PANTRY.technique_rules:
        return None

    signals = _detect_technique_signals(ingredient_ids)

    for rule in PANTRY.technique_rules:
        trigger = rule["trigger"]
        if trigger == "default" or signals.get(trigger):
            result: dict = {
                "method": rule["method"],
                "service": rule["service"],
                "glass": rule["glass"],
                "ice_in_glass": rule["ice_in_glass"],
                "pre_steps": rule.get("pre_steps", []),
                "rationale": rule["rationale"],
                "matched_rule": rule["id"],
            }
            if rule.get("carbonation_note"):
                result["carbonation_note"] = rule["carbonation_note"]
            if rule.get("ice_note"):
                result["ice_note"] = rule["ice_note"]
            if rule.get("ambiguous"):
                # The data has no clear technique here; tell the host to decide
                # rather than presenting a coin-flip default as confident.
                result["ambiguous"] = True
                result["ambiguity_note"] = rule.get("ambiguity_note", "")
            if rule.get("notes"):
                result["rule_notes"] = rule["notes"]
            return result

    return None


def validate_anchors(anchors: list[str]) -> str | None:
    """Return a human-readable error if the anchor list is the wrong size, else None.

    The drink must be built around 2–3 nominated anchors. Fewer or more than that
    is a request for the host Claude to go back to the user and ask them to pick.
    """
    if len(anchors) < 2 or len(anchors) > 3:
        return (
            f"Please nominate 2 or 3 anchors to build around (got {len(anchors)}). "
            "Ask the user which two or three ingredients they want at the heart of "
            "the drink."
        )
    return None


def _mean(values: list[float]) -> float:
    """Return the arithmetic mean, or 0.0 for an empty list."""
    return sum(values) / len(values) if values else 0.0


def _why(ingredient_ids: list[str]) -> dict[str, list[str]]:
    """Build the chemistry rationale for a combination, as data.

    Returns a mapping of ``"a+b" -> [shared, compounds]`` for every pair in the
    combination that actually shares something. Pairs that share nothing are
    omitted so the host Claude only sees the bridges that exist.
    """
    rationale: dict[str, list[str]] = {}
    for a, b in combinations(ingredient_ids, 2):
        _, shared = harmony(a, b)
        if shared:
            rationale[f"{a}+{b}"] = sorted(shared)
    return rationale


def _native_swap_for(anchors: list[str]) -> dict | None:
    """Suggest the native ingredient that best bridges to the anchors.

    Returns the highest-harmony native (summed harmony across the anchors),
    together with the compounds it shares and a one-line note — or ``None`` if no
    native bridges to the anchors at all.
    """
    best: dict | None = None
    best_score = 0.0
    for native_id in PANTRY.natives():
        if native_id in anchors:
            continue
        shared: set[str] = set()
        score = 0.0
        for anchor in anchors:
            value, pair_shared = harmony(native_id, anchor)
            score += value
            shared |= pair_shared
        if score > best_score and shared:
            best_score = score
            native = PANTRY.get(native_id)
            best = {
                "id": native_id,
                "display_name": native.display_name,
                "shared_compounds": sorted(shared),
                "note": (
                    f"{native.display_name} bridges in via "
                    f"{', '.join(sorted(shared))}."
                ),
            }
    return best


def _flavour_blanks(ingredient_ids: list[str]) -> list[str]:
    """Return ids Cobber has no flavour data for at all — no aroma, no taste.

    These are the genuine blind spots: an ingredient with neither a compound
    profile nor curated taste axes (vodka, soda, tonic, cola, cranberry...)
    contributes nothing to the harmony maths, so a combination's harmony score
    simply can't see it. Surfacing them lets the host avoid a misread — a low
    harmony on a Vodka Soda is the spirit being a blank canvas, not a clash, and
    Cobber should say so rather than let the number speak for an ingredient it
    knows nothing about. Data-driven, not a hardcoded neutral list: an entry
    earns its way off this flag the moment it gets compounds or taste.
    """
    blanks: list[str] = []
    for ingredient_id in ingredient_ids:
        ingredient = PANTRY.get(ingredient_id)
        if ingredient is not None and not ingredient.compounds and not ingredient.taste:
            blanks.append(ingredient_id)
    return sorted(blanks)


def _score_combination(ingredient_ids: list[str]) -> dict[str, float]:
    """Return the mean pairwise harmony and novelty for a combination."""
    harmonies = []
    novelties = []
    for a, b in combinations(ingredient_ids, 2):
        harmonies.append(harmony(a, b)[0])
        novelties.append(novelty(a, b))
    return {
        "harmony": round(_mean(harmonies), 4),
        "novelty": round(_mean(novelties), 4),
    }


def build_around(
    pantry_ids: list[str],
    anchor_ids: list[str],
    native_twist: bool = False,
    n: int = 5,
) -> list[dict]:
    """Suggest drink combinations built around the nominated anchors.

    Only combinations that contain *every* anchor are considered. Each candidate
    is the anchors plus up to :data:`MAX_ADDITIONS` other pantry ingredients,
    scored by a blend of mean pairwise harmony and novelty. The balance heuristic
    annotates each result; the top ``n`` are returned.

    When ``native_twist`` is on, combinations that already include an Australian
    native are nudged up the ranking, and any combination without one gets a
    ``native_swap`` suggestion: a native that bridges to the anchors.

    Raises ``ValueError`` if the anchor count is not 2 or 3, or if an anchor is
    not present in ``pantry_ids``.

    Each result item is::

        {
            "ingredients": [...ids],
            "scores": {"harmony": float, "novelty": float},
            "why": {"a+b": ["shared", "compounds"], ...},
            "balance": {...},
            "native_swap": {...} | None,
            "flavour_blanks": [...ids],  # ingredients with no aroma/taste data
        }

    ``flavour_blanks`` lists any ingredient in the combination that Cobber has no
    flavour data for (no compounds, no taste) — its harmony contribution is zero
    not because it clashes but because it is unknown chemistry, so the host can
    explain a low score rather than misread it.
    """
    error = validate_anchors(anchor_ids)
    if error is not None:
        raise ValueError(error)

    for anchor in anchor_ids:
        if anchor not in pantry_ids:
            raise ValueError(
                f"Anchor {anchor!r} is not in the pantry; anchors must be a "
                "subset of what the user actually has."
            )

    additions = [pid for pid in pantry_ids if pid not in anchor_ids]

    candidates: list[dict] = []
    # The anchors alone are a valid drink, as are the anchors plus 1..MAX_ADDITIONS
    # bridging ingredients from the rest of the pantry.
    for k in range(0, MAX_ADDITIONS + 1):
        for extra in combinations(additions, k):
            ingredient_ids = anchor_ids + list(extra)
            scores = _score_combination(ingredient_ids)
            has_native = any(
                (ing := PANTRY.get(i)) is not None and ing.is_native
                for i in ingredient_ids
            )

            # The ranking key blends harmony and novelty. Under native-twist we
            # add a bonus for combinations that already contain a native.
            rank = scores["harmony"] + scores["novelty"]
            if native_twist and has_native:
                rank += 0.5

            native_swap = None
            if native_twist and not has_native:
                native_swap = _native_swap_for(anchor_ids)

            candidates.append(
                {
                    "ingredients": ingredient_ids,
                    "scores": scores,
                    "why": _why(ingredient_ids),
                    "balance": balance(ingredient_ids),
                    "template": suggest_template(ingredient_ids),
                    "technique": suggest_technique(ingredient_ids),
                    "native_swap": native_swap,
                    "flavour_blanks": _flavour_blanks(ingredient_ids),
                    "_rank": rank,
                }
            )

    # Highest combined score first; drop the private ranking key from the output.
    candidates.sort(key=lambda c: c["_rank"], reverse=True)
    results = []
    for candidate in candidates[:n]:
        candidate.pop("_rank", None)
        results.append(candidate)
    return results
