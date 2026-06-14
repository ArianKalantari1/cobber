"""Tests for the MCP tool layer (server.py) — the honesty plumbing.

These pin the behaviours the live tests exposed: the resolver must never
silently coerce a sound-alike name (rose water is not soda water), fuzzy
matches must be disclosed, and proxy substitutions must resolve AND announce.
"""

from cobber import server


def test_sound_alike_names_are_not_coerced():
    """'rose water' must come back unknown, not collapse to soda_water.

    Regression: the second live test showed the old 0.7 fuzzy cutoff silently
    turning rose water into soda water — the never-guess rule broken at runtime.
    """
    result = server.resolve_ingredients(["rose water"])
    assert "rose water" in result["unknown"]
    assert "rose water" not in result["resolved"]


def test_typo_still_fuzzy_matches_and_is_disclosed():
    """A genuine typo resolves, but the approximation is reported, not hidden."""
    result = server.resolve_ingredients(["campar"])
    assert result["resolved"].get("campar") == "campari"
    assert result["fuzzy_matched"].get("campar") == "campari"


def test_exact_matches_are_not_flagged_fuzzy():
    result = server.resolve_ingredients(["gin", "lime"])
    assert result["fuzzy_matched"] == {}
    assert result["resolved"] == {"gin": "gin", "lime": "lime"}


def test_proxy_resolves_to_stand_in_and_announces():
    """Dubonnet resolves to its stand-in with the substitution surfaced."""
    result = server.resolve_ingredients(["dubonnet"])
    assert result["resolved"].get("dubonnet") == "sweet_vermouth"
    assert any(s["input"] == "dubonnet" for s in result["substitutions"])


def test_nearest_by_profile_tool_returns_ranked_neighbours():
    """The tool wraps the engine and returns a non-empty ranked list for a known id."""
    result = server.nearest_by_profile("lime", n=3)
    assert result["nearest"], "a known ingredient should have nearest profiles"
    assert "id" in result["nearest"][0]


def test_nearest_by_profile_tool_is_honest_about_unknowns():
    """An unknown id returns an empty list and a plain note, not a fabricated match."""
    result = server.nearest_by_profile("definitely_not_a_real_ingredient")
    assert result["nearest"] == []
    assert "note" in result


def test_substitution_tool_returns_role_faithful_swap():
    """The substitution tool offers a same-role pantry stand-in."""
    result = server.suggest_substitution("lime", ["gin", "lemon", "sugar_syrup"])
    assert result["substitutes"], "lemon should stand in for lime"
    assert result["substitutes"][0]["id"] == "lemon"


def test_substitution_tool_is_honest_when_nothing_fits():
    """No same-role match returns empty with a plain note, not a forced swap."""
    result = server.suggest_substitution("lime", ["gin", "vodka"])
    assert result["substitutes"] == []
    assert "note" in result


# ---------------------------------------------------------------------------
# get_culinary_affinities
# ---------------------------------------------------------------------------

def test_culinary_affinities_returns_sorted_results():
    """Orange has many mapped culinary affinities; they come back sorted by score."""
    result = server.get_culinary_affinities("orange", n=10)
    affinities = result["affinities"]
    assert affinities, "orange should have culinary affinities"
    scores = [a["affinity_score"] for a in affinities]
    assert scores == sorted(scores, reverse=True), "affinities must be sorted descending"


def test_culinary_affinities_result_shape():
    """Each affinity entry carries the required fields."""
    result = server.get_culinary_affinities("coffee")
    for affinity in result["affinities"]:
        assert "id" in affinity
        assert "display_name" in affinity
        assert "role" in affinity
        assert "affinity_score" in affinity
        assert "cuisine_contexts" in affinity
        assert "note" in affinity


def test_culinary_affinities_with_compound_bridge_includes_harmony():
    """When a compound bridge exists, shared_compounds and harmony are surfaced."""
    # wattleseed + coffee share pyrazine and furfural — strong compound bridge
    result = server.get_culinary_affinities("wattleseed")
    coffee_entry = next((a for a in result["affinities"] if a["id"] == "coffee"), None)
    assert coffee_entry is not None, "wattleseed should list coffee as a culinary affinity"
    assert "shared_compounds" in coffee_entry, "compound bridge should be surfaced"
    assert "harmony" in coffee_entry
    assert coffee_entry["harmony"] > 0


def test_culinary_affinities_no_bridge_omits_harmony():
    """When no compound bridge exists, shared_compounds and harmony are NOT added."""
    # apple + cinnamon: no shared compound in Cobber's aroma DB
    result = server.get_culinary_affinities("apple")
    cinnamon_entry = next((a for a in result["affinities"] if a["id"] == "cinnamon"), None)
    assert cinnamon_entry is not None, "apple should list cinnamon as a culinary affinity"
    assert "shared_compounds" not in cinnamon_entry, "no compound bridge should mean no shared_compounds key"


def test_culinary_affinities_unknown_ingredient_is_honest():
    """An unknown ingredient id returns an empty list with a note, not fabricated pairs."""
    result = server.get_culinary_affinities("not_a_real_ingredient")
    assert result["affinities"] == []
    assert "note" in result


def test_culinary_affinities_unmapped_ingredient_returns_empty_with_note():
    """An ingredient in Cobber's DB but not in the culinary table returns empty + note."""
    # vodka has no culinary pairings mapped — it's an aroma-neutral spirit
    result = server.get_culinary_affinities("vodka")
    assert result["affinities"] == []
    assert "note" in result


def test_culinary_affinities_n_parameter_limits_results():
    """The n parameter caps how many affinities are returned."""
    result = server.get_culinary_affinities("orange", n=3)
    assert len(result["affinities"]) <= 3


def test_culinary_affinities_cherry_almond_compound_confirmed():
    """cherry + almond share benzaldehyde — the harmony should be surfaced."""
    result = server.get_culinary_affinities("cherry")
    almond_entry = next((a for a in result["affinities"] if a["id"] == "almond"), None)
    assert almond_entry is not None
    assert "shared_compounds" in almond_entry
    assert "benzaldehyde" in almond_entry["shared_compounds"]
