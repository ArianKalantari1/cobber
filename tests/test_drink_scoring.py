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


# ---------------------------------------------------------------------------
# Notices and score_drink
# ---------------------------------------------------------------------------

OLIVIA = {
    "M1": ["gin", "dry_vermouth", "amaretto", "maraschino", "lemon", "olive"],
    "M2": ["gin", "amaretto", "maraschino", "vanilla", "lemon", "olive"],
    "B": ["gin", "amaretto", "benedictine", "vanilla", "lemon", "olive"],
}


def test_three_citrus_sources_raise_the_brightness_notice():
    """Ari's case: citrus-forward gin + limoncello + lemon is 'way too bright'; one link is fine."""
    stacked = engine.notices(["gin", "limoncello", "lemon"])
    assert len(stacked) == 1 and "3 citrus sources" in stacked[0] and "too bright" in stacked[0]
    assert engine.notices(["gin", "lemon"]) == []


def test_taste_words_and_no_aroma_items_are_not_sources():
    """'sweet' on a liqueur is sugar, not smell; sugar syrup has no aroma at all."""
    sources = engine.family_sources(["amaretto", "limoncello", "triple_sec", "sugar_syrup"])
    assert "sweet_creamy" not in sources
    assert "sugar_syrup" not in {i for members in sources.values() for i in members}
    assert sources["roasted_nutty"] == ["amaretto"]


def test_target_note_notice_on_the_olivia_versions():
    """Nutty is level with citrus only in M2 (amaretto + maraschino against gin + lemon)."""
    assert any("target" in n for n in engine.notices(OLIVIA["M1"], "roasted_nutty"))
    assert engine.notices(OLIVIA["M2"], "roasted_nutty") == []
    assert any("target" in n for n in engine.notices(OLIVIA["B"], "roasted_nutty"))
    assert any("no carrier" in n for n in engine.notices(["gin", "lemon"], "roasted_nutty"))


def test_unknown_target_family_is_refused():
    with pytest.raises(ValueError, match="Unknown flavour family"):
        engine.notices(["gin", "lemon"], "nutty")


def test_score_drink_shows_its_working():
    drink = engine.score_drink(["gin", "lemon", "limoncello", "sugar_syrup", "not_a_thing"])
    assert drink["harmony"] == engine._score_combination(["gin", "lemon"])["harmony"]
    assert drink["unknown"] == ["not_a_thing"]
    assert drink["structure_only"] == ["sugar_syrup"]
    merged = [v for v in drink["voices"] if len(v["ingredients"]) > 1]
    assert merged and set(merged[0]["ingredients"]) == {"lemon", "limoncello"} and merged[0]["reasons"]
    assert drink["bridges"][0]["between"] == [["gin"], ["lemon", "limoncello"]]
    assert any("too bright" in n for n in drink["notices"])


def test_score_drink_lists_decayed_repeats_and_provisional_data():
    drink = engine.score_drink(OLIVIA["B"])
    assert "benedictine" in drink["provisional"] and "olive" in drink["provisional"]
    m1 = engine.score_drink(OLIVIA["M1"])
    assert all(len(carriers) >= 3 for carriers in m1["repeated"].values())
    assert set(m1["repeated"]["limonene"]) == {"gin", "dry_vermouth", "lemon"}


@pytest.mark.parametrize(
    "ingredients, expected",
    [
        (["gin", "amaretto", "honey", "lemon", "olive"], 0.1014),  # restaurant, as on the menu
        (OLIVIA["M1"], 0.1110),
        (OLIVIA["M2"], 0.1015),
        (["gin", "amaretto", "peach_schnapps", "vanilla", "lemon", "olive"], 0.0986),  # P
        (OLIVIA["B"], 0.1191),
    ],
)
def test_olivia_snapshots(ingredients, expected):
    """Regression snapshots, not targets: the versions sit within 0.02 of each other,
    so the tasting decides between them. The house gin is the generic London dry
    gin until its label is in; B moves once Benedictine's bill is fixed."""
    assert engine.score_drink(ingredients)["harmony"] == pytest.approx(expected, abs=5e-4)


def test_two_ingredient_score_drink_matches_score_pairing():
    assert engine.score_drink(["gin", "lemon"])["harmony"] == round(engine.harmony("gin", "lemon")[0], 4)
    assert engine.score_drink(["gin", "lemon"])["novelty"] == round(engine.novelty("gin", "lemon"), 4)
