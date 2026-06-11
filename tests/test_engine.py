"""Unit tests for the Cobber flavour-chemistry engine.

These pin the behaviours the build spec calls out: that a native bridges in via
shared compounds, that an isolated ingredient is handled rather than crashing,
that a composite's profile is the union of its botanicals, and that the anchor
mechanic is enforced.
"""

import pytest

from cobber import engine
from cobber.data import load_pantry


def test_finger_lime_bridges_to_lime():
    """A native citrus and an ordinary lime should share compounds (harmony > 0)."""
    score, shared = engine.harmony("finger_lime", "lime")
    assert score > 0
    assert shared  # at least one shared compound, e.g. limonene / citral


def test_wattleseed_and_citrus_share_nothing():
    """Roasted wattleseed and a citrus share no compounds — handled, not crashed."""
    score, shared = engine.harmony("wattleseed", "lemon")
    assert score == 0
    assert shared == set()


def test_composite_profile_is_union_of_botanicals():
    """Gin's derived profile must equal the union of its botanicals' compounds."""
    pantry = load_pantry()
    gin = pantry.get("gin")
    expected: set[str] = set()
    for botanical_id in gin.botanicals:
        expected |= set(pantry.get(botanical_id).compounds)
    assert engine.profile("gin") == expected


def test_suggestions_always_contain_every_anchor():
    """Every returned combination must include all of the nominated anchors."""
    pantry = ["gin", "lime", "lemon_myrtle", "mint", "sugar_syrup", "cardamom"]
    anchors = ["gin", "lime"]
    results = engine.build_around(pantry, anchors, n=10)
    assert results  # we expect at least one suggestion
    for result in results:
        for anchor in anchors:
            assert anchor in result["ingredients"]


def test_too_few_anchors_is_rejected_clearly():
    """An anchor list shorter than 2 is rejected with a clear, actionable message."""
    with pytest.raises(ValueError) as excinfo:
        engine.build_around(["gin", "lime"], ["gin"])
    assert "2 or 3 anchors" in str(excinfo.value)


def test_too_many_anchors_is_rejected_clearly():
    """An anchor list longer than 3 is rejected with a clear, actionable message."""
    pantry = ["gin", "lime", "lemon", "mint"]
    with pytest.raises(ValueError) as excinfo:
        engine.build_around(pantry, ["gin", "lime", "lemon", "mint"])
    assert "2 or 3 anchors" in str(excinfo.value)


def test_novelty_rewards_chemistry_without_tradition():
    """A chemically-supported but rarely-made pairing should out-score a classic."""
    # gin + lemon_myrtle share citral-family compounds but almost nobody makes it.
    novel = engine.novelty("gin", "lemon_myrtle")
    # gin + lime is the canonical pairing (high tradition), so its novelty is low.
    classic = engine.novelty("gin", "lime")
    assert novel > classic


def test_native_twist_attaches_a_swap_when_no_native_present():
    """With the twist on and no native in the combo, a native_swap is suggested."""
    pantry = ["gin", "lime", "sugar_syrup"]
    results = engine.build_around(pantry, ["gin", "lime"], native_twist=True, n=5)
    # None of these ingredients is native, so at least the top result should carry
    # a bridging native suggestion.
    assert any(r["native_swap"] is not None for r in results)


def test_classic_pair_has_positive_tradition():
    """A classic pairing from the corpus should produce a positive tradition score."""
    assert engine.tradition("tequila", "lime") > 0.1


def test_unlisted_pair_defaults_to_zero_tradition():
    """Pairs missing from the co-occurrence table should return zero tradition."""
    assert engine.tradition("wattleseed", "cointreau") == 0.0


def test_tradition_file_with_extra_fields_loads_cleanly():
    """Tradition rows with additive fields (count/confidence) should load and validate."""
    pantry = load_pantry()
    assert pantry.tradition
