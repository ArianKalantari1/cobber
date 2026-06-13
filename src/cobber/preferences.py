"""Per-install taste-preference layer for Cobber the Mixologist.

Local, personal, additive. Each MCP install keeps ONE preference document on
the user's own machine (default ``~/.cobber/preferences.json``, overridable
with the ``COBBER_PREFS_PATH`` environment variable). When the user reports
back on a drink they actually made ("loved it", "too sweet"), the raw verdict
is appended to that document and a small derived taste profile is recomputed
from the full raw log — the log is the source of truth, the profile is a cache.

Honesty rules (the same moat as the rest of Cobber):

- The shared scoring data (ingredients / tradition / templates / technique) is
  NEVER written at runtime. This file is the only thing the server writes, it
  belongs to the user, and it is never committed to the repo. There is no
  pooling of feedback across installs — public knowledge accumulation was
  considered and deliberately rejected (spam/poisoning risk; Ari's ruling).
- The learner only attributes a verdict through ingredients whose taste data
  is curated AND non-provisional. Everything else is quarantined as
  "unattributed" — recorded, visible, but never learned from. Dirty data is
  inert instead of corrosive: a wrong provisional profile cannot teach the
  user's palate model to chase a phantom.
- Cold start is admitted, not papered over: below MIN_FEEDBACK_FOR_FIT
  verdicts, ``personal_fit`` returns None rather than a made-up score.
"""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

from . import engine

# Verdict vocabulary -> learning weight. Deliberately coarse: a bartender asks
# "did you like it?", not "rate it 0.0-1.0".
VERDICT_WEIGHTS = {
    "loved": 1.0,
    "liked": 0.5,
    "ok": 0.0,
    "disliked": -0.5,
    "hated": -1.0,
}

# Below this many feedback entries the profile is noise, and personal_fit
# says so (returns None) instead of inventing a number.
MIN_FEEDBACK_FOR_FIT = 3


def prefs_path() -> Path:
    """Where this install's preference document lives (env-overridable)."""
    return Path(
        os.environ.get("COBBER_PREFS_PATH", "~/.cobber/preferences.json")
    ).expanduser()


def load_prefs() -> dict:
    """Load the local preference document, or an empty one if none exists."""
    path = prefs_path()
    if not path.exists():
        return {"version": 1, "feedback": []}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_prefs(prefs: dict) -> None:
    """Write the preference document back to the user's local path."""
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(prefs, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _attributable(ingredient_id: str) -> bool:
    """Can a verdict teach the profile anything through this ingredient?

    Only if the entry exists, is not flagged provisional, and carries CURATED
    taste axes (an empty ``taste`` means the engine would fall back to a
    role-derived guess — guesses must not train a palate model).
    """
    ingredient = engine.PANTRY.get(ingredient_id)
    return (
        ingredient is not None
        and not ingredient.provisional
        and bool(ingredient.taste)
    )


def record_feedback(
    drink_name: str,
    ingredient_ids: list[str],
    verdict: str,
    liked: list[str] | None = None,
    could_improve: str = "",
    notes: str = "",
    unresolved_names: list[str] | None = None,
) -> dict:
    """Append one tasting verdict and recompute the derived profile.

    Returns the recorded entry plus the updated profile summary, including
    which ingredients were quarantined (so Cobber can tell the user honestly
    that those didn't teach the profile anything).
    """
    if verdict not in VERDICT_WEIGHTS:
        raise ValueError(
            f"verdict must be one of {sorted(VERDICT_WEIGHTS)}, got {verdict!r}"
        )
    if not ingredient_ids and not unresolved_names:
        raise ValueError("feedback needs at least one ingredient")

    known_ids = sorted(set(ingredient_ids))
    attributed = [i for i in known_ids if _attributable(i)]
    quarantined = [i for i in known_ids if not _attributable(i)]

    entry = {
        "date": date.today().isoformat(),
        "drink": drink_name,
        "ingredients": known_ids,
        "verdict": verdict,
        "liked": list(liked or []),
        "could_improve": could_improve,
        "notes": notes,
        # Per-entry audit trail of what the learner used vs refused.
        "attributed": attributed,
        "quarantined": quarantined,
    }
    if unresolved_names:
        entry["unresolved_names"] = sorted(set(unresolved_names))

    prefs = load_prefs()
    prefs.setdefault("feedback", []).append(entry)
    prefs["profile"] = _derive_profile(prefs["feedback"])
    save_prefs(prefs)

    return {"recorded": entry, "profile": profile_summary(prefs)}


def _derive_profile(feedback: list[dict]) -> dict:
    """Recompute the derived taste profile from the full raw feedback log.

    Recomputing from scratch keeps the result deterministic and
    order-independent, and means a corrected data file (e.g. an ingredient
    losing its provisional flag) flows through on the next feedback rather
    than being baked in forever.
    """
    axis_totals: dict[str, float] = {}
    axis_counts: dict[str, int] = {}
    affinity: dict[str, dict] = {}
    unattributed: dict[str, int] = {}

    for entry in feedback:
        weight = VERDICT_WEIGHTS.get(entry.get("verdict", "ok"), 0.0)
        # Re-check attributability live rather than trusting the stored list:
        # the data files may have improved since the entry was written.
        for ing_id in entry.get("ingredients", []):
            if _attributable(ing_id):
                ingredient = engine.PANTRY.get(ing_id)
                slot = affinity.setdefault(ing_id, {"count": 0, "score": 0.0})
                slot["count"] += 1
                slot["score"] += weight
                for axis, value in ingredient.taste:
                    axis_totals[axis] = axis_totals.get(axis, 0.0) + weight * value
                    axis_counts[axis] = axis_counts.get(axis, 0) + 1
            else:
                unattributed[ing_id] = unattributed.get(ing_id, 0) + 1

    axis_weights = {
        axis: round(max(-1.0, min(1.0, axis_totals[axis] / axis_counts[axis])), 3)
        for axis in sorted(axis_totals)
        if axis_counts[axis] > 0
    }
    for slot in affinity.values():
        slot["score"] = round(max(-1.0, min(1.0, slot["score"] / slot["count"])), 3)

    return {
        "axis_weights": axis_weights,
        "ingredient_affinity": affinity,
        "unattributed": unattributed,
    }


def profile_summary(prefs: dict) -> dict:
    """A small, tool-friendly view of what Cobber knows about this palate."""
    feedback = prefs.get("feedback", [])
    profile = prefs.get("profile") or _derive_profile(feedback)
    affinity = profile.get("ingredient_affinity", {})

    ranked = sorted(affinity.items(), key=lambda kv: kv[1]["score"], reverse=True)
    top_likes = [
        {"id": ing_id, **slot} for ing_id, slot in ranked if slot["score"] > 0
    ][:5]
    top_dislikes = [
        {"id": ing_id, **slot}
        for ing_id, slot in reversed(ranked)
        if slot["score"] < 0
    ][:5]

    return {
        "feedback_count": len(feedback),
        "axis_weights": profile.get("axis_weights", {}),
        "top_likes": top_likes,
        "top_dislikes": top_dislikes,
        "unattributed": profile.get("unattributed", {}),
        "note": (
            "Learned only from verified, taste-curated ingredients; anything "
            "under 'unattributed' was recorded but deliberately not learned "
            "from because its data is unverified."
        ),
    }


def personal_fit(ingredient_ids: list[str], prefs: dict | None = None) -> dict | None:
    """Score a combination against this install's tasting history (0..1).

    0.5 is neutral. Returns None when the profile is too thin to mean
    anything (cold start) or when no ingredient in the combination carries
    curated taste data — no number is better than a fake number.
    """
    if prefs is None:
        prefs = load_prefs()
    feedback = prefs.get("feedback", [])
    if len(feedback) < MIN_FEEDBACK_FOR_FIT:
        return None

    profile = prefs.get("profile") or _derive_profile(feedback)
    weights = profile.get("axis_weights", {})
    if not weights:
        return None

    # The combination's curated taste-axis means (skip uncurated ingredients).
    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    curated_used: list[str] = []
    for ing_id in ingredient_ids:
        ingredient = engine.PANTRY.get(ing_id)
        if ingredient is None or ingredient.provisional or not ingredient.taste:
            continue
        curated_used.append(ing_id)
        for axis, value in ingredient.taste:
            sums[axis] = sums.get(axis, 0.0) + value
            counts[axis] = counts.get(axis, 0) + 1
    if not curated_used:
        return None
    combo = {axis: sums[axis] / counts[axis] for axis in sums}

    # Alignment: cosine similarity between the palate vector and the drink's
    # taste vector (missing axes count as 0). Cosine matches the SHAPE of the
    # profile — a plain dot product would let a one-note drink max out a
    # single mildly-liked axis and outrank a drink that mirrors the user's
    # whole balance (sugar syrup beating a Negroni for a Negroni lover).
    axes = set(weights) | set(combo)
    numerator = sum(weights.get(a, 0.0) * combo.get(a, 0.0) for a in axes)
    weight_norm = sum(w * w for w in weights.values()) ** 0.5
    combo_norm = sum(v * v for v in combo.values()) ** 0.5
    denominator = weight_norm * combo_norm
    alignment = numerator / denominator if denominator else 0.0

    # Direct history with these exact ingredients, when there is any.
    affinity = profile.get("ingredient_affinity", {})
    direct = [affinity[i]["score"] for i in ingredient_ids if i in affinity]
    direct_mean = sum(direct) / len(direct) if direct else 0.0

    score = max(0.0, min(1.0, 0.5 + 0.35 * alignment + 0.15 * direct_mean))
    return {
        "score": round(score, 3),
        "based_on_feedback": len(feedback),
        "axis_alignment": round(alignment, 3),
        "known_ingredients": sorted(set(ingredient_ids) & set(affinity)),
        "note": "fit against this install's tasting history; 0.5 is neutral",
    }
