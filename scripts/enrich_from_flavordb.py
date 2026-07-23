#!/usr/bin/env python3
"""Propose ingredient-profile enrichment from a fetched FlavorDB2 dump.

Reads ``data/raw/flavordb_entities.json`` (produced by ``fetch_flavordb.py``) and
proposes, per Cobber ingredient, extra aroma compounds that FlavorDB2 lists for
the matching food — each carrying its provenance. The output is a REVIEW file
(``data/profile_enrichment.json``), never a direct edit to ingredients.json:
build-time data stays human-approved. Ari reads the proposal, keeps what's right,
and applies it by hand (and fills descriptor stubs for any genuinely new compound).

Two guard-rails, straight from the project principles:
  * **Never coerce a name.** A FlavorDB molecule whose name doesn't normalise to a
    clean compound id, or an entity that doesn't clearly match a Cobber
    ingredient, is recorded in a review list — never forced onto an id.
  * **Flag everything provisional.** Proposed additions are provisional until Ari
    approves them; new compounds are listed with the FlavorDB ``flavor_profile``
    words as *candidate* (cited) descriptors, to be confirmed before use.

This script needs no network; run ``fetch_flavordb.py`` first (from an unblocked
machine) to produce the dump it reads.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_PATH = DATA / "raw" / "flavordb_entities.json"
INGREDIENTS_PATH = DATA / "ingredients.json"
DESCRIPTORS_PATH = DATA / "compound_descriptors.json"
OUTPUT_PATH = DATA / "profile_enrichment.json"

# Curated FlavorDB-entity-alias -> Cobber-ingredient-id extensions, for foods whose
# common name differs from Cobber's display name. Extend as Ari reviews. This is
# name alignment only (no chemistry), and every match is echoed in the output for
# a human to sanity-check.
ALIAS_TO_ID: dict[str, str] = {
    "sweet orange": "orange",
    "common thyme": "thyme",
    "peppermint": "mint",
    "spearmint": "mint",
    "sweet basil": "basil",
    "ginger": "ginger",
    "star anise": "star_anise",
}


def _norm_compound(name: str) -> str | None:
    """Normalise a FlavorDB molecule common_name to a Cobber-style compound id.

    Lowercase, Greek letters spelled out already (FlavorDB uses 'beta-'), non
    alphanumerics -> underscore, collapse repeats. Returns ``None`` if nothing
    usable survives (so the caller can shelve it for review rather than coerce).
    """
    n = name.strip().lower()
    n = n.replace("β", "beta").replace("α", "alpha").replace("γ", "gamma").replace("δ", "delta")
    n = re.sub(r"[^a-z0-9]+", "_", n).strip("_")
    n = re.sub(r"_+", "_", n)
    return n or None


def _cobber_ingredients() -> dict[str, str]:
    """Map normalised name/id -> Cobber raw ingredient id (composites derive, skip)."""
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        entries = json.load(handle)
    lookup: dict[str, str] = {}
    for entry in entries:
        lookup[entry["id"]] = entry["id"]
        lookup[entry["display_name"].strip().lower()] = entry["id"]
    return lookup, {e["id"]: set(e.get("compounds", [])) for e in entries}


def build_proposal() -> dict:
    if not RAW_PATH.exists():
        raise SystemExit(
            f"No FlavorDB dump at {RAW_PATH}. Run scripts/fetch_flavordb.py first "
            "(from an unblocked network)."
        )
    with RAW_PATH.open(encoding="utf-8") as handle:
        dump = json.load(handle)
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        known_compounds = set(json.load(handle)["compounds"])

    name_to_id, existing = _cobber_ingredients()

    per_ingredient: dict[str, dict] = {}
    new_compounds: dict[str, dict] = {}
    unmapped_molecules: list[dict] = []
    unmatched_entities: list[str] = []

    for entity in dump.get("entities", []):
        alias = entity.get("alias", "").strip().lower()
        cobber_id = name_to_id.get(alias) or ALIAS_TO_ID.get(alias)
        if cobber_id is None:
            unmatched_entities.append(alias)
            continue

        additions: list[dict] = []
        for mol in entity.get("molecules", []):
            compound_id = _norm_compound(mol.get("common_name", ""))
            if compound_id is None:
                unmapped_molecules.append({"entity": alias, "molecule": mol.get("common_name")})
                continue
            if compound_id in existing.get(cobber_id, set()):
                continue  # already on the ingredient
            addition = {
                "compound": compound_id,
                "flavordb_common_name": mol.get("common_name"),
                "already_known_compound": compound_id in known_compounds,
                "flavordb_flavor_profile": mol.get("flavor_profile", []),
                "source": "FlavorDB2 (Goel et al. 2024) — non-commercial, attributed",
                "provisional": True,
            }
            additions.append(addition)
            if compound_id not in known_compounds:
                # A compound Cobber has no descriptor for yet: capture FlavorDB's
                # flavor_profile words as CANDIDATE (cited) descriptors for review.
                stub = new_compounds.setdefault(
                    compound_id,
                    {
                        "compound": compound_id,
                        "flavordb_common_name": mol.get("common_name"),
                        "candidate_odor": sorted(set(mol.get("flavor_profile", []))),
                        "source": "FlavorDB2 (Goel et al. 2024); confirm against Flavornet before use",
                        "provisional": True,
                        "seen_in": [],
                    },
                )
                stub["seen_in"].append(cobber_id)

        if additions:
            per_ingredient[cobber_id] = {
                "flavordb_alias": alias,
                "add_compounds": sorted(additions, key=lambda a: a["compound"]),
            }

    return {
        "_meta": {
            "description": "PROPOSED ingredient-profile enrichment from FlavorDB2 — human-approved before applying.",
            "generated_by": "scripts/enrich_from_flavordb.py",
            "source": dump.get("_meta", {}),
            "how_to_apply": (
                "Review per-ingredient add_compounds; for each kept compound, add it to that "
                "ingredient's 'compounds' in ingredients.json and note the source. For every "
                "new_compound_stub you keep, add an entry to compound_descriptors.json (confirm "
                "odour words against Flavornet) and re-run compute_descriptor_harmony + render."
            ),
            "ingredients_touched": len(per_ingredient),
            "new_compounds_needing_descriptors": len(new_compounds),
            "unmatched_entities": len(set(unmatched_entities)),
            "unmapped_molecules": len(unmapped_molecules),
        },
        "per_ingredient": dict(sorted(per_ingredient.items())),
        "new_compound_stubs": [new_compounds[c] for c in sorted(new_compounds)],
        "review_unmatched_entities": sorted(set(unmatched_entities)),
        "review_unmapped_molecules": unmapped_molecules,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    proposal = build_proposal()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(proposal, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    meta = proposal["_meta"]
    print(
        f"Proposal written -> {args.output}\n"
        f"  {meta['ingredients_touched']} ingredients get proposed additions\n"
        f"  {meta['new_compounds_needing_descriptors']} new compounds need descriptor stubs\n"
        f"  {meta['unmatched_entities']} FlavorDB entities unmatched, "
        f"{meta['unmapped_molecules']} molecules unmapped (both left for review, never coerced)"
    )


if __name__ == "__main__":
    main()
