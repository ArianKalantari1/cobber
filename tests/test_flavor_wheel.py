"""Tests for the sensory-descriptor layer: flavour wheel + harmonious notes.

These pin the behaviours the flavour-wheel spec calls out: that an ingredient's
compounds aggregate into families, that non-volatile tastants land in the taste
overlay rather than a faked odour family, that gaps are reported honestly rather
than invented, and that the corpus-mined harmonious-notes table ranks by
above-chance affinity. Also a data-integrity guard: every descriptor word a
compound carries must belong to exactly one flavour family, and every entry must
be sourced.
"""

import json
from pathlib import Path

import pytest

from cobber import engine
from cobber.data import load_pantry

DATA = Path(__file__).resolve().parents[1] / "data"


# ---------------------------------------------------------------------------
# flavor_wheel
# ---------------------------------------------------------------------------


def test_gin_wheel_is_citrus_and_woody_dominant():
    """London dry gin should read citrus- and woody/resinous-forward (juniper)."""
    wheel = engine.flavor_wheel("gin")
    assert wheel["known"] is True
    assert wheel["coverage"] == "full"
    families = {f["family"] for f in wheel["families"]}
    assert "citrus" in families
    assert "woody_resinous" in families
    # Dominant family carries the most contributing compounds.
    assert wheel["dominant"] == wheel["families"][0]["family"]


def test_wheel_fractions_sum_to_one():
    """Family fractions are a distribution over contributing-compound weight."""
    wheel = engine.flavor_wheel("gin")
    total = sum(f["fraction"] for f in wheel["families"])
    assert total == pytest.approx(1.0, abs=0.02)


def test_wheel_families_sorted_by_weight_desc():
    wheel = engine.flavor_wheel("angostura_bitters")
    weights = [f["weight"] for f in wheel["families"]]
    assert weights == sorted(weights, reverse=True)


def test_bitters_carry_taste_overlay_not_odour_family():
    """Gentian's bitter glycosides belong in the taste overlay, never an odour family."""
    wheel = engine.flavor_wheel("angostura_bitters")
    overlay_classes = {t["class"] for t in wheel["taste_overlay"]}
    assert "bitter" in overlay_classes
    # amarogentin/gentiopicroside must not appear inside any odour family
    for family in wheel["families"]:
        assert "amarogentin" not in family["compounds"]
        assert "gentiopicroside" not in family["compounds"]


def test_unknown_ingredient_is_honest_not_crashed():
    wheel = engine.flavor_wheel("definitely_not_an_ingredient")
    assert wheel["known"] is False
    assert wheel["families"] == []
    assert wheel["dominant"] is None
    assert "Unknown" in wheel["note"]


def test_provisional_compound_flags_the_wheel():
    """A wheel built partly on provisional compounds must say so."""
    wheel = engine.flavor_wheel("gin")  # gin carries provisional beta_phellandrene
    assert wheel["provisional"] is True
    assert wheel["provisional_compounds"]


def test_every_wheel_word_maps_to_its_family():
    """Descriptor words shown on a family must actually belong to that family."""
    pantry = load_pantry()
    wheel = engine.flavor_wheel("mint")
    for family in wheel["families"]:
        for word in family["words"]:
            assert pantry.descriptor_word_to_family[word] == family["family"]


# ---------------------------------------------------------------------------
# harmonious_notes
# ---------------------------------------------------------------------------


def test_harmonious_notes_excludes_own_families():
    notes = engine.harmonious_notes("mint")
    own = set(notes["own_families"])
    suggested = {n["family"] for n in notes["notes"]}
    assert own.isdisjoint(suggested)


def test_mint_family_harmonises_with_spice_above_chance():
    """The corpus should surface mint_cooling<->spice (julep/mojito) as distinctive.

    Asserted at the FAMILY level, not the ingredient level: "mint loves spice" is a
    corpus co-occurrence fact and must hold regardless of how rich any single
    ingredient's profile becomes after enrichment. (harmonious_notes(<ingredient>)
    is deliberately confounded — it excludes the ingredient's own families, so once
    mint the ingredient carries a spice facet, spice correctly drops out of *its*
    suggestions while the underlying family affinity is unchanged.)
    """
    partners = {p["family"]: p for p in engine.harmonious_families("mint_cooling", limit=10)}
    assert "spice" in partners
    assert partners["spice"]["above_chance"] is True


def test_harmonious_notes_unknown_is_empty_honest():
    notes = engine.harmonious_notes("definitely_not_an_ingredient")
    assert notes["notes"] == []
    assert notes["note"]


def test_harmonious_families_ranked_by_npmi():
    partners = engine.harmonious_families("citrus")
    npmis = [p["npmi"] for p in partners]
    assert npmis == sorted(npmis, reverse=True)


# ---------------------------------------------------------------------------
# data integrity
# ---------------------------------------------------------------------------


def test_all_compounds_have_descriptor_entries():
    """Every compound used by an ingredient must have a descriptor record."""
    pantry = load_pantry()
    used: set[str] = set()
    for ingredient in pantry.ingredients.values():
        used |= set(ingredient.compounds)
    missing = used - set(pantry.compound_descriptors)
    assert not missing, f"compounds without descriptors: {sorted(missing)}"


def test_every_descriptor_entry_is_sourced():
    """Cite-every-source rule: each descriptor record names its provenance."""
    with (DATA / "compound_descriptors.json").open(encoding="utf-8") as handle:
        compounds = json.load(handle)["compounds"]
    for cid, record in compounds.items():
        assert record.get("source"), f"{cid} has no source"


def test_taste_actives_have_no_odour_words():
    """A non-volatile tastant must not also claim odour descriptors."""
    with (DATA / "compound_descriptors.json").open(encoding="utf-8") as handle:
        compounds = json.load(handle)["compounds"]
    for cid, record in compounds.items():
        if record.get("taste_class"):
            assert record.get("odor") == [], f"{cid} is a tastant but has odour words"


def test_family_map_covers_every_descriptor_word():
    """No orphan words: every odour word used by a compound has a family."""
    pantry = load_pantry()
    for record in pantry.compound_descriptors.values():
        for word in record.get("odor", []):
            assert word in pantry.descriptor_word_to_family


# ---------------------------------------------------------------------------
# taste_provenance (the taste "why" layer)
# ---------------------------------------------------------------------------


def test_lemon_sourness_traces_to_acids():
    prov = engine.taste_provenance("lemon")
    assert prov["known"] is True
    assert set(prov["provenance"]["sour"]) == {"citric_acid", "malic_acid"}
    assert prov["gaps"] == []


def test_campari_bitterness_traces_to_gentian_via_botanicals():
    """A composite inherits its botanicals' tastants: Campari's bitter <- gentian."""
    prov = engine.taste_provenance("campari")
    assert "gentiopicroside" in prov["provenance"]["bitter"]
    assert prov["provenance"]["sweet"] == ["sucrose"]


def test_provenance_gap_is_reported_not_faked():
    """miso is sweet (koji) with no recorded sugar -> honest gap, not invented."""
    prov = engine.taste_provenance("miso")
    assert prov["provenance"]["umami"] == ["glutamic_acid"]
    assert "sweet" in prov["gaps"]


def test_fat_and_funk_are_never_provenance_gaps():
    """Texture/microbial axes have no single-molecule cause by design."""
    for iid in ("cream", "butter", "mezcal"):
        prov = engine.taste_provenance(iid)
        assert "fat" not in prov["gaps"]
        assert "funk" not in prov["gaps"]


def test_provenance_flags_provisional_tastant():
    """absinthe's bitterness traces to absinthin, which is provisional."""
    prov = engine.taste_provenance("absinthe")
    assert "absinthin" in prov["provenance"].get("bitter", [])
    assert prov["provisional"] is True


def test_unknown_ingredient_provenance_is_honest():
    prov = engine.taste_provenance("definitely_not_an_ingredient")
    assert prov["known"] is False
    assert prov["provenance"] == {}


def test_tastants_do_not_pollute_aroma_harmony():
    """Tastants live in a separate field; they must never enter the aroma profile."""
    # lemon and lime are both sour via citric_acid, but that must NOT show up as a
    # shared *aroma* compound (harmony is chemistry of smell, not taste).
    assert "citric_acid" not in engine.profile("lemon")
    assert "citric_acid" not in engine.profile("lime")
    _, shared = engine.harmony("lemon", "lime")
    assert "citric_acid" not in shared


def test_every_tastant_has_a_taste_class_descriptor():
    """Data integrity: no ingredient may reference a tastant without a taste class."""
    pantry = load_pantry()
    for ingredient in pantry.ingredients.values():
        for tastant in ingredient.tastants:
            record = pantry.compound_descriptors.get(tastant)
            assert record is not None, f"{ingredient.id}: {tastant} missing"
            assert record.get("taste_class"), f"{tastant} has no taste_class"
