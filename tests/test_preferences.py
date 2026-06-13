"""Tests for the per-install taste-preference layer.

The contract under test: feedback is recorded raw; the learner attributes
verdicts ONLY through verified, taste-curated ingredients (everything else is
quarantined, recorded-but-inert); personal_fit admits cold start instead of
inventing a score; and the shared scoring data is never written.
"""

import pytest

from cobber import preferences


@pytest.fixture()
def prefs_file(tmp_path, monkeypatch):
    """Point the preference document at a throwaway path for each test."""
    path = tmp_path / "preferences.json"
    monkeypatch.setenv("COBBER_PREFS_PATH", str(path))
    return path


def test_feedback_is_recorded_and_persisted(prefs_file):
    result = preferences.record_feedback(
        drink_name="Test Negroni",
        ingredient_ids=["campari", "sweet_vermouth"],
        verdict="loved",
        liked=["the bitter finish"],
    )
    assert prefs_file.exists()
    assert result["recorded"]["verdict"] == "loved"
    assert result["profile"]["feedback_count"] == 1

    prefs = preferences.load_prefs()
    assert len(prefs["feedback"]) == 1
    assert prefs["feedback"][0]["drink"] == "Test Negroni"


def test_invalid_verdict_is_rejected(prefs_file):
    with pytest.raises(ValueError):
        preferences.record_feedback("X", ["lime"], verdict="amazing!!")


def test_provisional_ingredients_are_quarantined_not_learned(prefs_file):
    """miso is provisional: it must be recorded but never teach the profile."""
    result = preferences.record_feedback(
        drink_name="The Broth Decision",
        ingredient_ids=["miso", "lime"],
        verdict="loved",
    )
    entry = result["recorded"]
    assert "miso" in entry["quarantined"]
    assert "lime" in entry["attributed"]

    profile = result["profile"]
    assert "miso" in profile["unattributed"]
    liked_ids = [item["id"] for item in profile["top_likes"]]
    assert "miso" not in liked_ids
    assert "lime" in liked_ids


def test_uncurated_taste_means_no_attribution(prefs_file):
    """gin has no curated taste axes yet, so it must not train the profile."""
    result = preferences.record_feedback(
        drink_name="G&T",
        ingredient_ids=["gin", "lime"],
        verdict="liked",
    )
    assert "gin" in result["recorded"]["quarantined"]


def test_personal_fit_admits_cold_start(prefs_file):
    """Fewer than MIN_FEEDBACK_FOR_FIT verdicts -> None, not a fake score."""
    preferences.record_feedback("One", ["campari"], verdict="loved")
    assert preferences.personal_fit(["campari", "sweet_vermouth"]) is None


def test_personal_fit_leans_toward_liked_axes(prefs_file):
    """Three bitter-loving verdicts should score a bitter build above neutral
    and above a sweet-leaning build."""
    for drink in ("A", "B", "C"):
        preferences.record_feedback(
            drink, ["campari", "sweet_vermouth"], verdict="loved"
        )

    bitter_fit = preferences.personal_fit(["campari", "dry_vermouth"])
    sweet_fit = preferences.personal_fit(["honey", "agave", "sugar_syrup"])
    assert bitter_fit is not None and sweet_fit is not None
    assert bitter_fit["score"] > 0.5
    assert bitter_fit["score"] > sweet_fit["score"]
    assert bitter_fit["based_on_feedback"] == 3


def test_negative_feedback_pushes_fit_below_neutral(prefs_file):
    for drink in ("A", "B", "C"):
        preferences.record_feedback(drink, ["campari"], verdict="hated")
    fit = preferences.personal_fit(["campari", "sweet_vermouth"])
    assert fit is not None
    assert fit["score"] < 0.5
    assert "campari" in fit["known_ingredients"]


def test_personal_fit_refuses_fully_uncurated_combination(prefs_file):
    """If nothing in the combination has curated taste, no number is given."""
    for drink in ("A", "B", "C"):
        preferences.record_feedback(drink, ["lime"], verdict="loved")
    assert preferences.personal_fit(["gin", "vodka"]) is None


def test_profile_recomputes_from_raw_log(prefs_file):
    """The derived profile is a cache over the raw log, order-independent."""
    preferences.record_feedback("A", ["lemon"], verdict="loved")
    preferences.record_feedback("B", ["lemon"], verdict="hated")
    prefs = preferences.load_prefs()
    # loved (+1) and hated (-1) on the same ingredient must cancel to ~0.
    assert prefs["profile"]["ingredient_affinity"]["lemon"]["score"] == 0.0
