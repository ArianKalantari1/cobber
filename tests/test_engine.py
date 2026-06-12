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
    """The spec's canonical pair (gin + lime) must score clearly positive.

    Under the old raw-NPMI score this landed at 0.0 — gin and lime are both so
    common that co-occurring 12 times is no better than chance. The log-prevalence
    score reflects how often the pairing is actually made, so a gimlet ranks high.
    """
    assert engine.tradition("gin", "lime") > 0.3


def test_ubiquitous_classic_outranks_a_one_off_pair():
    """A pair made in many recipes must out-score one seen in a single recipe.

    This pins the fix for the NPMI inversion: lavender + St-Germain appeared in
    exactly one recipe (raw NPMI = 1.0), yet must rank below the daiquiri's
    lime + white rum, which the corpus makes constantly.
    """
    assert engine.tradition("white_rum", "lime") > engine.tradition("lavender", "st_germain")


def test_unlisted_pair_defaults_to_zero_tradition():
    """Pairs missing from the co-occurrence table should return zero tradition."""
    assert engine.tradition("wattleseed", "cointreau") == 0.0


def test_tradition_file_with_extra_fields_loads_cleanly():
    """Tradition rows with additive fields (count/confidence) should load and validate."""
    pantry = load_pantry()
    assert pantry.tradition


def test_curated_taste_is_used_verbatim():
    """An ingredient with curated taste data returns it, not a role prior."""
    axes, derived = engine.taste_profile("salt")
    assert not derived
    assert axes == {"salty": 1.0}


def test_missing_taste_falls_back_to_role_prior_and_is_flagged():
    """An uncurated ingredient derives a coarse prior from its role, flagged."""
    axes, derived = engine.taste_profile("pineapple")  # fruit role, no curated taste
    assert derived
    assert axes == {"sweet": 0.3, "sour": 0.3}


def test_savoury_crossover_bridges_via_shared_compounds():
    """Miso and coffee share roasty pyrazines — the umami crossover has real chemistry."""
    score, shared = engine.harmony("miso", "coffee")
    assert score > 0
    assert "pyrazine" in shared


def test_balance_flags_dairy_acid_split_risk():
    """Cream plus citrus must surface the split hazard a bartender would flag."""
    result = engine.balance(["gin", "cream", "lemon"])
    assert any("split" in note.lower() for note in result["taste_notes"])


def test_balance_reads_savoury_structure():
    """A Bloody Mary build should read as savoury, not as a sour."""
    result = engine.balance(["vodka", "tomato", "worcestershire", "salt", "lemon"])
    assert result["structure"] == "savoury"


def test_balance_still_returns_original_keys():
    """The taste layer is additive: the original role-check contract holds."""
    result = engine.balance(["gin", "lime", "sugar_syrup"])
    assert result["ok"] is True
    assert "roles_present" in result and "warning" in result


def test_frontier_support_returns_attributed_evidence():
    """A pairing seen in the craft corpus comes back with count and examples."""
    evidence = engine.frontier_support("gin", "honey")
    assert evidence is not None
    assert evidence["count"] >= 1
    assert evidence["examples"] and "drink" in evidence["examples"][0]


def test_frontier_support_is_separate_from_tradition():
    """Frontier evidence must not have leaked into the tradition score's corpus.

    miso never appears in a canon recipe, so any pairing with it has zero
    tradition — even if a craft bartender someday uses it (frontier channel).
    """
    assert engine.tradition("miso", "bourbon") == 0.0


def test_provisional_flag_is_loaded_from_notes():
    """Entries flagged TODO-verify/PROVISIONAL in notes carry provisional=True."""
    pantry = load_pantry()
    assert pantry.get("miso").provisional is True
    assert pantry.get("lemon").provisional is False


# ---------------------------------------------------------------------------
# Proportion template tests
# ---------------------------------------------------------------------------

def test_templates_are_loaded():
    """Pantry must load proportion templates from the JSON file."""
    from cobber.data import load_pantry
    pantry = load_pantry()
    assert pantry.templates, "proportion_templates.json should load non-empty templates"
    # Each template must have the required keys
    for t in pantry.templates:
        assert "id" in t
        assert "centroid" in t
        assert "recipe_count" in t


def test_sour_template_matches_daiquiri_ingredients():
    """A spirit + acid + sweet combination should suggest the Sour template."""
    t = engine.suggest_template(["white_rum", "lime", "sugar_syrup"])
    assert t is not None
    assert "sour" in t["suggested_name"].lower(), (
        f"Expected Sour template for daiquiri ingredients, got: {t['suggested_name']!r}"
    )


def test_negroni_template_matches_negroni_ingredients():
    """A spirit + amaro + vermouth combination should suggest the Negroni template."""
    t = engine.suggest_template(["gin", "campari", "sweet_vermouth"])
    assert t is not None
    assert "negroni" in t["suggested_name"].lower(), (
        f"Expected Negroni-style template, got: {t['suggested_name']!r}"
    )


def test_spirit_forward_template_for_old_fashioned():
    """A spirit + bitters + small-sweet combination (no acid) should be Spirit-Forward."""
    t = engine.suggest_template(["bourbon", "angostura_bitters", "sugar_syrup"])
    assert t is not None
    # The Sour template has structural acid; Old Fashioned has none, so Sour
    # must be filtered out and the spirit-forward template wins.
    assert "sour" not in t["suggested_name"].lower(), (
        f"Old Fashioned must not match Sour template, got: {t['suggested_name']!r}"
    )
    assert "spirit" in t["suggested_name"].lower(), (
        f"Expected Spirit-Forward template, got: {t['suggested_name']!r}"
    )


def test_highball_template_for_spirit_plus_lengthener():
    """A spirit + carbonated lengthener combination should suggest Highball."""
    t = engine.suggest_template(["gin", "soda_water"])
    assert t is not None
    assert "highball" in t["suggested_name"].lower(), (
        f"Expected Highball template for gin+soda, got: {t['suggested_name']!r}"
    )


def test_template_proportions_sum_to_at_most_one():
    """Ingredient proportions from a template must sum to ≤ 1.0 (may be < 1 if some
    ingredients are unrecognised or in 'other' role)."""
    t = engine.suggest_template(["gin", "lime", "sugar_syrup"])
    assert t is not None
    total = sum(t["ingredient_proportions"].values())
    assert total <= 1.01, f"Ingredient proportions sum to {total}, expected ≤ 1.0"
    assert total > 0.5, f"Ingredient proportions sum to {total}, too low — mapping may be broken"


def test_paper_plane_style_matches_four_way_equal_parts():
    """spirit + aperol (liqueur) + amaro + acid should hit the 4-way equal-parts overlay.

    Aperol is a sweet-bright aperitivo (11% ABV, sweet 0.5/bitter 0.5) — it fills
    the liqueur slot in Paper Plane-style builds, not the amaro slot that Campari fills.
    """
    t = engine.suggest_template(["bourbon", "aperol", "averna", "lemon"])
    assert t is not None
    assert t["id"] == "last_word_style", (
        f"Expected 4-way equal-parts overlay, got: {t['id']!r} ({t['suggested_name']!r})"
    )
    # Proportions should be roughly equal (±10%)
    props = t["ingredient_proportions"]
    vals = list(props.values())
    assert max(vals) - min(vals) < 0.10, (
        f"Expected near-equal proportions for Paper Plane style, got: {props}"
    )


def test_template_in_build_around_output():
    """build_around must include a template field in each suggestion."""
    pantry = ["gin", "lime", "sugar_syrup", "lemon_myrtle"]
    results = engine.build_around(pantry, ["gin", "lime"], n=3)
    assert results
    for result in results:
        assert "template" in result, "Each build_around result must include a template"
        t = result["template"]
        if t is not None:
            assert "id" in t
            assert "ingredient_proportions" in t
