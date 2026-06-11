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


def balance(ingredient_ids: list[str]) -> dict:
    """Run a deliberately simple V1 balance check over a set of role tags.

    A plausible drink has a base spirit and at least one balancing role
    (sour / sweet / bitter), and is not built entirely from a single role. This
    is a sanity heuristic, **not** a real recipe balancer — it checks the shape
    of a combination, not its ratios.

    Returns ``{"ok": bool, "roles_present": [...], "warning": str | None}``.
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
    return {"ok": ok, "roles_present": roles_present, "warning": warning}


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
