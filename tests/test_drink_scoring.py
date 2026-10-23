"""Tests for drink-level scoring: aroma voices and diminishing returns.

These pin the rules Ari approved on 23 October 2026 (docs/todo-scoring-upgrade.md):
structure items aren't scored for aroma, a compound repeated across a drink counts
with diminishing returns, and same-aroma ingredients count as one voice, with no
bridge credit and never a block.
"""

import json
from pathlib import Path

import pytest

from cobber import engine

ROOT = Path(__file__).resolve().parents[1]


def _harmony(ingredient_ids):
    return engine._score_combination(ingredient_ids)["harmony"]


def _iba_drinks():
    recipes = json.loads((ROOT / "data" / "recipes_components.json").read_text(encoding="utf-8"))
    return [row for row in recipes if row["source"] == "iba"]


def test_two_ingredient_drink_scores_its_pair_harmony():
    """One citrus link still counts in full: a pair's drink score is its Jaccard."""
    assert _harmony(["gin", "lemon"]) == round(engine.harmony("gin", "lemon")[0], 4)
    assert _harmony(["gin", "lemon"]) > 0.5


def test_structure_items_do_not_dilute_harmony():
    """Sugar, soda and egg white shape balance, not aroma (the Gin Fizz regression)."""
    plain = _harmony(["gin", "lemon"])
    assert _harmony(["gin", "lemon", "sugar_syrup", "soda_water", "egg_white"]) == plain
    _, structure_only = engine.voices(["gin", "lemon", "sugar_syrup", "soda_water"])
    assert structure_only == ["sugar_syrup", "soda_water"]


def test_repeats_decay_first_link_full_then_half():
    """A compound in k voices earns 1 + 1/2 + 1/4 ... credit, not one count per pair."""

    def voice(name):
        return {"ingredients": [name], "compounds": {"x"}, "reasons": []}

    for k, total_credit in ((2, 1.0), (3, 1.5), (4, 1.75)):
        scored = engine._score_voices([voice(f"v{i}") for i in range(k)], detail=True)
        assert sum(pair["harmony"] for pair in scored["pairs"]) == pytest.approx(total_credit)


def test_stacked_citrus_scores_below_one_link():
    assert _harmony(["gin", "lemon", "lime"]) < _harmony(["gin", "lemon"])


@pytest.mark.parametrize(
    "pair",
    [
        ["amaretto", "almond"],
        ["limoncello", "lemon"],
        ["gin", "coriander_seed"],
        ["coffee_liqueur", "coffee"],
        ["benedictine", "vanilla"],  # a data gap until Benedictine's bill is fixed
    ],
)
def test_same_aroma_is_one_voice_with_no_bridge_credit(pair):
    drink_voices, _ = engine.voices(pair)
    assert len(drink_voices) == 1
    assert drink_voices[0]["reasons"], "a merged voice must say why"
    assert _harmony(pair) == 0.0


@pytest.mark.parametrize("pair", [["gin", "lemon"], ["lemon", "lime"], ["amaretto", "maraschino"]])
def test_distinct_ingredients_stay_separate_voices(pair):
    """Juice on a composite's bill (lemon in gin) still bridges; lemon and lime differ."""
    assert engine.same_voice(*pair) is None
    assert len(engine.voices(pair)[0]) == 2


def test_lemon_and_lime_sit_below_the_same_voice_line():
    """Ari: lemon and lime each have their own roundness."""
    assert engine.harmony("lemon", "lime")[0] < engine.SAME_VOICE_JACCARD


def test_a_copy_does_not_raise_harmony():
    """Limoncello next to lemon reinforces the lemon; it adds no bridge credit."""
    assert _harmony(["gin", "lemon", "limoncello"]) <= _harmony(["gin", "lemon"])


def test_every_iba_drink_scores_without_blocking():
    drinks = _iba_drinks()
    assert len(drinks) == 75
    for row in drinks:
        scores = engine._score_combination(row["literal"])
        assert 0.0 <= scores["harmony"] <= 1.0, row["drink"]
        assert 0.0 <= scores["novelty"] <= scores["harmony"], row["drink"]


# ---------------------------------------------------------------------------
# build_around: only new voices are offered, and identity guards hold
# ---------------------------------------------------------------------------

OLIVIA_BAR = [
    "gin", "amaretto", "lemon", "olive", "limoncello", "honey", "almond", "maraschino",
    "peach_schnapps", "vanilla", "dry_vermouth", "sugar_syrup", "brandy", "coffee_liqueur",
    "coriander_seed",
]


def _olivia(**guards):
    """Develop Olivia: gin and amaretto as anchors, lemon and olive locked."""
    return engine.build_around(OLIVIA_BAR, ["gin", "amaretto"], n=100, locked=["lemon", "olive"], **guards)


def _offered(results):
    return {ingredient for result in results for ingredient in result["ingredients"]}


def test_copies_are_not_offered_as_new_ideas():
    """Limoncello only repeats the lemon, almond the amaretto, coriander the gin. Honey is new."""
    offered = _offered(_olivia(max_additions=1))
    assert not {"limoncello", "almond", "coriander_seed"} & offered
    assert "honey" in offered


def test_structure_items_are_not_offered():
    assert "sugar_syrup" not in _offered(_olivia())


def test_locked_items_are_always_kept():
    for result in _olivia():
        assert {"gin", "amaretto", "lemon", "olive"} <= set(result["ingredients"])


def test_excluded_items_are_never_added():
    results = _olivia(exclude=["brandy", "coffee_liqueur"])
    assert results
    assert not {"brandy", "coffee_liqueur"} & _offered(results)


def test_max_spirits_keeps_a_single_base():
    assert "brandy" in _offered(_olivia())
    assert "brandy" not in _offered(_olivia(max_spirits=1))


def test_max_additions_sets_how_far_the_drink_grows():
    assert max(len(result["ingredients"]) for result in _olivia(max_additions=3)) == 7
    assert [len(result["ingredients"]) for result in _olivia(max_additions=0)] == [4]


def test_suggestion_scores_match_the_drink_score():
    for result in _olivia()[:10]:
        assert result["scores"] == engine._score_combination(result["ingredients"])


@pytest.mark.parametrize(
    "guards, message",
    [
        ({"exclude": ["lemon"]}, "excluded"),
        ({"max_spirits": 0}, "max_spirits"),
        ({"max_additions": -1}, "max_additions"),
    ],
)
def test_contradictory_guards_are_refused(guards, message):
    with pytest.raises(ValueError, match=message):
        _olivia(**guards)


def test_locked_items_must_be_in_the_pantry():
    with pytest.raises(ValueError, match="Locked ingredient"):
        engine.build_around(["gin", "amaretto"], ["gin", "amaretto"], locked=["olive"])


def test_oversized_search_is_refused_not_sampled():
    with pytest.raises(ValueError, match="combinations"):
        engine.build_around(engine.PANTRY.all_ids(), ["gin", "lemon"], max_additions=4)


def test_same_voice_anchors_are_reported_not_rejected():
    results = engine.build_around(["amaretto", "almond", "lemon"], ["amaretto", "almond"], n=3)
    assert results
    for result in results:
        assert {"amaretto", "almond"} in [set(voice["ingredients"]) for voice in result["same_voice"]]
        assert "amaretto+almond" not in result["why"]
