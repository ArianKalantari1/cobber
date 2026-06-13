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
