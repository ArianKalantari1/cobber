#!/usr/bin/env python3
"""Enrich ingredient profiles from a fetched FlavorDB2 dump.

Reads ``data/raw/flavordb_entities.json`` (from ``fetch_flavordb.py``) and, per
Cobber ingredient, proposes the extra aroma compounds FlavorDB2 lists for the
matching food — each cited and provisional. Enriching a raw ingredient
automatically enriches every composite built on it (composites derive their
profile from their botanicals), so the common-food core and the spirits both
benefit from one pass.

Two modes:
  * default (no ``--apply``): writes a REVIEW proposal to
    ``data/profile_enrichment.json`` and changes nothing else. Read it, trim it.
  * ``--apply``: writes the kept additions straight into ``ingredients.json`` and
    auto-generates descriptor stubs in ``compound_descriptors.json`` for genuinely
    new compounds. The review gate then becomes the **git diff** — inspect it
    before you commit. Nothing is pushed for you.

Guard-rails, straight from the project principles:
  * **Never coerce a name.** Molecule names that don't normalise to a clean
    compound id, and FlavorDB entities that don't clearly match a Cobber
    ingredient, go to review lists — never forced onto an id. Fuzzy entity
    matches above a high cutoff are accepted but always reported; borderline ones
    are listed, not applied.
  * **Flag everything provisional.** Every added compound and every auto-stub is
    ``provisional`` until you confirm it. Descriptor stubs only claim the
    flavour-profile words that already belong to a Cobber family (so the load-time
    cross-check stays satisfied); the full FlavorDB profile is kept in a note.

Offline self-test: ``--self-test`` runs the whole flow on a synthetic dump.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_PATH = DATA / "raw" / "flavordb_entities.json"
INGREDIENTS_PATH = DATA / "ingredients.json"
DESCRIPTORS_PATH = DATA / "compound_descriptors.json"
FAMILIES_PATH = DATA / "flavor_families.json"
OUTPUT_PATH = DATA / "profile_enrichment.json"

# Curated FlavorDB-alias -> Cobber-id extensions for foods whose common name
# differs from Cobber's display name. Name alignment only (no chemistry); every
# match is echoed for a human to sanity-check. Extend as you review.
ALIAS_TO_ID: dict[str, str] = {
    "sweet orange": "orange",
    "common thyme": "thyme",
    "peppermint": "mint",
    "spearmint": "mint",
    "sweet basil": "basil",
    "star anise": "star_anise",
    "clove": "clove",
    "juniperus communis": "juniper",
    "coriander": "coriander_seed",
}

# difflib cutoff for fuzzy alias->ingredient matching. High on purpose (same
# spirit as the runtime resolver's 0.84): catch "lemons"->"lemon", refuse
# sound-alikes. Anything between REVIEW and ACCEPT is listed, not applied.
FUZZY_ACCEPT = 0.90
FUZZY_REVIEW = 0.80


def _norm_compound(name: str) -> str | None:
    """Normalise a FlavorDB molecule common_name to a Cobber-style compound id."""
    n = name.strip().lower()
    n = n.replace("β", "beta").replace("α", "alpha").replace("γ", "gamma").replace("δ", "delta")
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    n = re.sub(r"_+", "_", n)
    return n or None


def _load_ingredients() -> tuple[list[dict], dict[str, str], dict[str, set[str]]]:
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        entries = json.load(handle)
    name_to_id: dict[str, str] = {}
    existing: dict[str, set[str]] = {}
    for entry in entries:
        name_to_id[entry["id"]] = entry["id"]
        name_to_id[entry["display_name"].strip().lower()] = entry["id"]
        existing[entry["id"]] = set(entry.get("compounds", []))
    return entries, name_to_id, existing


def _match_entity(alias: str, name_to_id: dict[str, str]) -> tuple[str | None, str]:
    """Return (cobber_id or None, how) for one FlavorDB alias. Never coerces."""
    if not alias:
        return None, "empty"
    exact = name_to_id.get(alias) or ALIAS_TO_ID.get(alias)
    if exact:
        return exact, "exact"
    match = difflib.get_close_matches(alias, list(name_to_id), n=1, cutoff=FUZZY_REVIEW)
    if match:
        score = difflib.SequenceMatcher(None, alias, match[0]).ratio()
        if score >= FUZZY_ACCEPT:
            return name_to_id[match[0]], f"fuzzy:{match[0]}({score:.2f})"
        return None, f"review:{match[0]}({score:.2f})"
    return None, "unmatched"


def build_proposal(dump: dict, word_to_family: dict[str, str],
                   name_to_id: dict[str, str], existing: dict[str, set[str]],
                   known_compounds: set[str]) -> dict:
    per_ingredient: dict[str, dict] = {}
    new_compounds: dict[str, dict] = {}
    unmapped_molecules: list[dict] = []
    unmatched_entities: list[dict] = []

    for entity in dump.get("entities", []):
        alias = entity.get("alias", "").strip().lower()
        cobber_id, how = _match_entity(alias, name_to_id)
        if cobber_id is None:
            unmatched_entities.append({"alias": alias, "reason": how})
            continue

        additions: list[dict] = []
        for mol in entity.get("molecules", []):
            compound_id = _norm_compound(mol.get("common_name", ""))
            if compound_id is None:
                unmapped_molecules.append({"entity": alias, "molecule": mol.get("common_name")})
                continue
            if compound_id in existing.get(cobber_id, set()):
                continue
            profile = mol.get("flavor_profile", [])
            additions.append({
                "compound": compound_id,
                "flavordb_common_name": mol.get("common_name"),
                "already_known_compound": compound_id in known_compounds,
                "flavordb_flavor_profile": profile,
                "source": "FlavorDB2 (Goel et al. 2024) — non-commercial, attributed",
                "provisional": True,
            })
            if compound_id not in known_compounds:
                stub = new_compounds.setdefault(compound_id, {
                    "compound": compound_id,
                    "flavordb_common_name": mol.get("common_name"),
                    # only the profile words Cobber already buckets into a family:
                    "mapped_odor": sorted({w for w in profile if w in word_to_family}),
                    "unmapped_profile_words": sorted({w for w in profile if w not in word_to_family}),
                    "source": "FlavorDB2 (Goel et al. 2024); confirm vs Flavornet before de-provisioning",
                    "provisional": True,
                    "seen_in": [],
                })
                if cobber_id not in stub["seen_in"]:
                    stub["seen_in"].append(cobber_id)

        if additions:
            per_ingredient[cobber_id] = {
                "flavordb_alias": alias, "matched_by": how,
                "add_compounds": sorted(additions, key=lambda a: a["compound"]),
            }

    return {
        "_meta": {
            "description": "PROPOSED ingredient-profile enrichment from FlavorDB2.",
            "generated_by": "scripts/enrich_from_flavordb.py",
            "source": dump.get("_meta", {}),
            "ingredients_touched": len(per_ingredient),
            "new_compounds_needing_descriptors": len(new_compounds),
            "unmatched_entities": len(unmatched_entities),
            "unmapped_molecules": len(unmapped_molecules),
            "how_to_apply": (
                "Review, then re-run with --apply to write into ingredients.json + "
                "compound_descriptors.json; inspect the git diff; then rebuild "
                "(compute_descriptor_harmony.py, render_flavor_wheel.py) and run tests."
            ),
        },
        "per_ingredient": dict(sorted(per_ingredient.items())),
        "new_compound_stubs": [new_compounds[c] for c in sorted(new_compounds)],
        "review_unmatched_entities": sorted(unmatched_entities, key=lambda e: e["alias"]),
        "review_unmapped_molecules": unmapped_molecules,
    }


def apply_proposal(proposal: dict) -> tuple[int, int]:
    """Write kept additions into ingredients.json + descriptor stubs. Returns counts.

    The git diff is the review gate — this mutates committed data files in place,
    provisionally and attributed, for a human to inspect before committing.
    """
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        ingredients = json.load(handle)
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        descriptors = json.load(handle)

    by_id = {e["id"]: e for e in ingredients}
    added_compounds = 0
    for cobber_id, block in proposal["per_ingredient"].items():
        entry = by_id.get(cobber_id)
        if entry is None:
            continue
        have = set(entry.get("compounds", []))
        for add in block["add_compounds"]:
            if add["compound"] not in have:
                entry.setdefault("compounds", []).append(add["compound"])
                have.add(add["compound"])
                added_compounds += 1
        note = entry.get("notes", "")
        tag = " [enriched from FlavorDB2 — PROVISIONAL additions]"
        if "FlavorDB2" not in note:
            entry["notes"] = (note + tag).strip()

    new_stubs = 0
    for stub in proposal["new_compound_stubs"]:
        cid = stub["compound"]
        if cid in descriptors["compounds"]:
            continue
        descriptors["compounds"][cid] = {
            "cas": None,
            "odor": stub["mapped_odor"],
            "taste_class": None,
            "provisional": True,
            "source": stub["source"],
            "note": ("Auto-stub from FlavorDB2; full profile: "
                     + ", ".join(stub["mapped_odor"] + stub["unmapped_profile_words"])
                     + ". Confirm odour words + CAS against Flavornet."),
        }
        new_stubs += 1
    descriptors["_meta"]["compound_count"] = len(descriptors["compounds"])

    with INGREDIENTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(ingredients, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    with DESCRIPTORS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(descriptors, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return added_compounds, new_stubs


def _load_word_to_family() -> dict[str, str]:
    with FAMILIES_PATH.open(encoding="utf-8") as handle:
        fams = json.load(handle)["odor_families"]
    return {w: f for f, words in fams.items() for w in words}


def _self_test() -> None:
    """Run build_proposal on a synthetic dump; assert the guard-rails hold."""
    word_to_family = _load_word_to_family()
    name_to_id = {"lemon": "lemon", "lemon": "lemon", "orange": "orange"}
    existing = {"lemon": {"limonene"}, "orange": set()}
    dump = {"entities": [
        {"alias": "lemon", "molecules": [
            {"common_name": "Limonene", "flavor_profile": ["citrus"]},           # already have -> skip
            {"common_name": "Nonanal", "flavor_profile": ["citrus", "waxy", "aldehyde"]},  # new
        ]},
        {"alias": "sweet orange", "molecules": [                                  # alias map -> orange
            {"common_name": "Valencene", "flavor_profile": ["woody", "citrus"]},
        ]},
        {"alias": "moon cheese", "molecules": [{"common_name": "X"}]},            # unmatched entity
    ]}
    prop = build_proposal(dump, word_to_family, name_to_id, existing, known_compounds={"limonene"})
    assert "lemon" in prop["per_ingredient"]
    assert prop["per_ingredient"]["lemon"]["add_compounds"][0]["compound"] == "nonanal"
    assert prop["per_ingredient"]["orange"]["matched_by"].startswith("exact") or "orange" in prop["per_ingredient"]
    stubs = {s["compound"]: s for s in prop["new_compound_stubs"]}
    # 'aldehyde' is not a Cobber family word -> must be shelved, not claimed:
    assert "aldehyde" in stubs["nonanal"]["unmapped_profile_words"]
    assert "citrus" in stubs["nonanal"]["mapped_odor"]
    assert any(e["alias"] == "moon cheese" for e in prop["review_unmatched_entities"])
    print("self-test OK:",
          f"{prop['_meta']['ingredients_touched']} ingredients, "
          f"{prop['_meta']['new_compounds_needing_descriptors']} new compounds, "
          f"{prop['_meta']['unmatched_entities']} unmatched")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write into ingredients.json + descriptors (review via git diff)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    if not RAW_PATH.exists():
        raise SystemExit(
            f"No FlavorDB dump at {RAW_PATH}. Run scripts/fetch_flavordb.py first "
            "(from an unblocked network / your local machine)."
        )
    with RAW_PATH.open(encoding="utf-8") as handle:
        dump = json.load(handle)
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        known_compounds = set(json.load(handle)["compounds"])

    word_to_family = _load_word_to_family()
    _, name_to_id, existing = _load_ingredients()
    proposal = build_proposal(dump, word_to_family, name_to_id, existing, known_compounds)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(proposal, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    m = proposal["_meta"]
    print(f"Proposal -> {args.output}: {m['ingredients_touched']} ingredients, "
          f"{m['new_compounds_needing_descriptors']} new compounds, "
          f"{m['unmatched_entities']} entities + {m['unmapped_molecules']} molecules for review")

    if args.apply:
        added, stubs = apply_proposal(proposal)
        print(f"APPLIED: +{added} compound links across ingredients, +{stubs} descriptor stubs.")
        print("Now inspect `git diff`, then rebuild: python3 scripts/compute_descriptor_harmony.py "
              "&& python3 scripts/render_flavor_wheel.py && python -m pytest tests/ -q")


if __name__ == "__main__":
    main()
