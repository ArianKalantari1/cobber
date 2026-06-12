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
    """Return ``(axis -> value, derived)`` for one ingredient.

    Curated ``taste`` data is used verbatim (``derived=False``). When absent,
    a coarse prior from the ingredient's role stands in (``derived=True``) so
    the balance heuristic still has something to reason over — honestly
    flagged rather than silently invented.
    """
    ingredient = PANTRY.get(ingredient_id)
    if ingredient is None:
        return {}, True
    if ingredient.taste:
        return dict(ingredient.taste), False
    return dict(ROLE_TASTE_PRIOR.get(ingredient.role, {})), True


def balance(ingredient_ids: list[str]) -> dict:
    """Run a deliberately simple V1 balance check over roles and taste axes.

    A plausible drink has a base spirit and at least one balancing role
    (sour / sweet / bitter), and is not built entirely from a single role.
    On top of the role check, taste axes are summed across the combination to
    read its structure (sour-balanced / bittersweet / savoury) and to flag
    real bartending hazards (dairy + acid splits; savoury with no
    counterweight). This is a sanity heuristic, **not** a recipe balancer —
    it checks the shape of a combination, not its ratios.

    Returns the original ``{"ok", "roles_present", "warning"}`` plus
    ``"taste_axes"`` (summed values), ``"structure"`` (a one-word reading),
    ``"taste_notes"`` (hazards/accents) and ``"taste_derived_for"`` (which
    ingredients used the role prior rather than curated data).
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
    "soda_water", "tonic_water", "ginger_ale", "sparkling_wine",
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
        "has_dairy":                has_dairy and not has_egg_white,
        "has_acid":                 has_acid,
        "has_carb":                 has_carb,
        "has_herb":                 has_herb,
        "has_herb_acid_and_carb":   has_herb and has_acid and has_carb,
        "has_acid_and_carb":        has_acid and has_carb and not has_herb,
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
      1. egg_white      → dry shake then shake, served up
      2. highball_build → build (carbonation only, no acid)
      3. sour_highball  → shake base, top with carbonation, highball glass
      4. dairy_shake    → shake, served up
      5. acid_shake     → shake, served up
      6. herb_muddle_build → muddle then build, rocks
      7. spirit_only    → stir, rocks
      8. default        → build, rocks
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
        }
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
