"""Validation tests for the culinary-affinities loader.

The first cut of this data shipped with silent bugs: duplicate pairs that
collapsed under frozenset keying (one with a *conflicting* score that was lost
to last-wins overwrite) and a pair referencing an ingredient that doesn't exist
(silently dropped at lookup). These tests pin the loud-failure validation added
to stop that recurring, and confirm the shipped data file is itself clean.
"""

import pytest

from cobber import data
from cobber.data import _validate_culinary_row, load_pantry

# A minimal "known ingredients" stand-in: the validator only checks membership.
_KNOWN = {"gin": object(), "lemon": object(), "basil": object()}


def test_validator_rejects_unknown_ingredient():
    with pytest.raises(ValueError, match="unknown ingredient"):
        _validate_culinary_row(
            {"pair": ["gin", "not_a_real_ingredient"], "affinity_score": 0.5}, _KNOWN
        )


def test_validator_rejects_out_of_range_score():
    with pytest.raises(ValueError, match=r"\[0.0, 1.0\]"):
        _validate_culinary_row(
            {"pair": ["gin", "lemon"], "affinity_score": 1.4}, _KNOWN
        )


def test_validator_rejects_malformed_pair():
    with pytest.raises(ValueError, match="pair"):
        _validate_culinary_row({"pair": ["gin"], "affinity_score": 0.5}, _KNOWN)


def test_validator_rejects_self_pair():
    with pytest.raises(ValueError, match="distinct"):
        _validate_culinary_row(
            {"pair": ["gin", "gin"], "affinity_score": 0.5}, _KNOWN
        )


def test_validator_accepts_a_clean_row():
    key, payload = _validate_culinary_row(
        {"pair": ["gin", "lemon"], "affinity_score": 0.7, "note": "ok"}, _KNOWN
    )
    assert key == frozenset({"gin", "lemon"})
    assert payload["affinity_score"] == 0.7


def test_shipped_culinary_file_is_clean_and_unique():
    """The real data file loads, and every pair is unique with a valid score."""
    pantry = load_pantry()
    assert pantry.culinary, "culinary pairs should load"
    for key, payload in pantry.culinary.items():
        assert 0.0 <= payload["affinity_score"] <= 1.0
        assert len(key) == 2
        # Both ids must be real ingredients (no dead references survive).
        for ingredient_id in key:
            assert pantry.get(ingredient_id) is not None
