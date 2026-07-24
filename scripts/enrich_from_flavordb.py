#!/usr/bin/env python3
"""Enrich ingredient profiles from a fetched FlavorDB2 dump — conservatively.

Reads ``data/raw/flavordb_entities.json`` (from ``fetch_flavordb.py``) and, per
Cobber ingredient, proposes a SMALL set of extra aroma compounds FlavorDB2 lists
for the matching food. Enriching a raw ingredient enriches every composite built
on it too (composites derive from their botanicals).

Why conservative? FlavorDB lists every molecule ever detected in a food — dozens
to hundreds, most of them trace/ubiquitous background. Importing all of them
floods Cobber's curated profiles and drowns the signal (harmony saturates, wheels
turn to mush). Cobber's design is "characteristic compounds only", so this step:

  * **Known-vocabulary only.** It only adds compounds Cobber already tracks (present
    in compound_descriptors.json). That means every addition already has a cited,
    family-mapped descriptor — no orphan compounds, no empty auto-stubs, no foreign
    descriptor vocabulary. Compounds outside the vocab are counted and reported,
    never added.
  * **Least-ubiquitous first, capped.** Candidates are ranked by how FEW FlavorDB
    foods contain them (rarer = more characteristic, the same NPMI intuition as
    tradition), and only the top ``--max-add`` per ingredient are proposed.
  * **DB-sourced, not a guess.** Additions are attributed to FlavorDB2 in the
    ingredient's notes but are NOT flagged provisional — they come from a
    peer-reviewed database, unlike the hand-curated native pass.

Guard-rail kept: **never coerce a name.** Molecule names that don't normalise to a
clean id, and FlavorDB entities that don't match a Cobber ingredient, go to review
lists — never forced onto an id. Fuzzy entity matches above a high cutoff are
accepted but always reported; borderline ones are listed, not applied.

Modes: default writes a REVIEW proposal to ``data/profile_enrichment.json`` and
changes nothing else; ``--apply`` writes the additions into ``ingredients.json``
(git diff is the review gate). Offline ``--self-test`` runs on a synthetic dump.

LICENSE: FlavorDB2 is CC BY-NC-SA 3.0 (non-commercial + ShareAlike). Enriched data
is a derivative — keep it attributed and, if the repo is public, note the license
travels with it. Cite Goel et al. 2024 (doi:10.1111/1750-3841.17298).
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RAW_PATH = DATA / "raw" / "flavordb_entities.json"
INGREDIENTS_PATH = DATA / "ingredients.json"
DESCRIPTORS_PATH = DATA / "compound_descriptors.json"
OUTPUT_PATH = DATA / "profile_enrichment.json"

# Curated FlavorDB-alias -> Cobber-id extensions for foods whose common name
# differs from Cobber's display name. Name alignment only (no chemistry).
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

FUZZY_ACCEPT = 0.90
FUZZY_REVIEW = 0.80
DEFAULT_MAX_ADD = 6          # per ingredient — keep profiles characteristic, not exhaustive
NOTE_TAG = "[+FlavorDB2 constituents]"   # deliberately NOT the word 'provisional'


def _norm_compound(name: str) -> str | None:
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


def _compound_ubiquity(dump: dict, known: set[str]) -> Counter:
    """How many entities each known-vocab compound appears in (for rarity ranking)."""
    freq: Counter = Counter()
    for entity in dump.get("entities", []):
        seen = set()
        for mol in entity.get("molecules", []):
            cid = _norm_compound(mol.get("common_name", ""))
            if cid and cid in known:
                seen.add(cid)
        freq.update(seen)
    return freq


def build_proposal(dump: dict, name_to_id: dict[str, str],
                   existing: dict[str, set[str]], known: set[str],
                   max_add: int) -> dict:
    ubiquity = _compound_ubiquity(dump, known)

    per_ingredient: dict[str, dict] = {}
    unmatched_entities: list[dict] = []
    out_of_vocab: Counter = Counter()
    unmapped_molecules = 0

    for entity in dump.get("entities", []):
        alias = entity.get("alias", "").strip().lower()
        cobber_id, how = _match_entity(alias, name_to_id)
        if cobber_id is None:
            unmatched_entities.append({"alias": alias, "reason": how})
            continue

        have = existing.get(cobber_id, set())
        candidates: dict[str, str] = {}   # compound_id -> flavordb common_name
        for mol in entity.get("molecules", []):
            raw_name = mol.get("common_name", "")
            cid = _norm_compound(raw_name)
            if cid is None:
                unmapped_molecules += 1
                continue
            if cid not in known:
                out_of_vocab[cid] += 1     # tracked, never added (would be noise)
                continue
            if cid in have or cid in candidates:
                continue
            candidates[cid] = raw_name

        if not candidates:
            continue
        # Rarest (most characteristic) first; cap.
        ranked = sorted(candidates, key=lambda c: (ubiquity.get(c, 0), c))[:max_add]
        per_ingredient[cobber_id] = {
            "flavordb_alias": alias,
            "matched_by": how,
            "add_compounds": [
                {"compound": c, "flavordb_common_name": candidates[c],
                 "ubiquity": ubiquity.get(c, 0),
                 "source": "FlavorDB2 (Goel et al. 2024) — non-commercial, attributed"}
                for c in ranked
            ],
        }

    return {
        "_meta": {
            "description": "PROPOSED conservative ingredient enrichment from FlavorDB2 (known-vocab only, capped).",
            "generated_by": "scripts/enrich_from_flavordb.py",
            "policy": {"known_vocab_only": True, "max_add_per_ingredient": max_add,
                       "rank": "least-ubiquitous-first"},
            "source": dump.get("_meta", {}),
            "ingredients_touched": len(per_ingredient),
            "total_additions": sum(len(v["add_compounds"]) for v in per_ingredient.values()),
            "unmatched_entities": len(unmatched_entities),
            "distinct_out_of_vocab_compounds_skipped": len(out_of_vocab),
            "unmapped_molecule_names": unmapped_molecules,
            "how_to_apply": (
                "Review, then re-run with --apply to write into ingredients.json; inspect "
                "the git diff; rebuild (compute_descriptor_harmony.py, render_flavor_wheel.py); "
                "run tests."
            ),
        },
        "per_ingredient": dict(sorted(per_ingredient.items())),
        "review_unmatched_entities": sorted(unmatched_entities, key=lambda e: e["alias"]),
        "review_out_of_vocab_compounds": sorted(out_of_vocab),
    }


def apply_proposal(proposal: dict) -> int:
    """Write the capped additions into ingredients.json. Returns compounds added."""
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        ingredients = json.load(handle)
    by_id = {e["id"]: e for e in ingredients}

    added = 0
    for cobber_id, block in proposal["per_ingredient"].items():
        entry = by_id.get(cobber_id)
        if entry is None:
            continue
        have = set(entry.get("compounds", []))
        for add in block["add_compounds"]:
            if add["compound"] not in have:
                entry.setdefault("compounds", []).append(add["compound"])
                have.add(add["compound"])
                added += 1
        note = entry.get("notes", "")
        if NOTE_TAG not in note:
            entry["notes"] = (note.rstrip() + " " + NOTE_TAG).strip()
        src = entry.get("source", "")
        if "FlavorDB2" not in src:
            entry["source"] = (src.rstrip() + " | Enriched from FlavorDB2 (Goel et al. 2024).").strip(" |").strip()

    with INGREDIENTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(ingredients, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return added


def _self_test() -> None:
    known = {"limonene", "citral", "nonanal", "valencene", "myrcene"}
    name_to_id = {"lemon": "lemon", "orange": "orange"}
    existing = {"lemon": {"limonene"}, "orange": set()}
    dump = {"entities": [
        {"alias": "lemon", "molecules": [
            {"common_name": "Limonene"},                 # already have -> skip
            {"common_name": "Nonanal"},                  # known, new -> add
            {"common_name": "Some-Weird-Molecule 42"},   # not in vocab -> skip (out_of_vocab)
        ]},
        {"alias": "sweet orange", "molecules": [         # alias -> orange
            {"common_name": "Limonene"}, {"common_name": "Valencene"}, {"common_name": "Myrcene"},
        ]},
        {"alias": "moon cheese", "molecules": [{"common_name": "Limonene"}]},  # unmatched
    ]}
    prop = build_proposal(dump, name_to_id, existing, known, max_add=2)
    lemon_adds = [a["compound"] for a in prop["per_ingredient"]["lemon"]["add_compounds"]]
    assert lemon_adds == ["nonanal"], lemon_adds
    assert "some_weird_molecule_42" in prop["review_out_of_vocab_compounds"]
    orange_adds = [a["compound"] for a in prop["per_ingredient"]["orange"]["add_compounds"]]
    assert len(orange_adds) == 2 and all(c in known for c in orange_adds)  # cap + known-only
    assert any(e["alias"] == "moon cheese" for e in prop["review_unmatched_entities"])
    print(f"self-test OK: {prop['_meta']['ingredients_touched']} ingredients, "
          f"{prop['_meta']['total_additions']} additions, "
          f"{prop['_meta']['distinct_out_of_vocab_compounds_skipped']} out-of-vocab skipped")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="write into ingredients.json (review via git diff)")
    parser.add_argument("--max-add", type=int, default=DEFAULT_MAX_ADD, help="max compounds added per ingredient")
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
        known = set(json.load(handle)["compounds"])

    _, name_to_id, existing = _load_ingredients()
    proposal = build_proposal(dump, name_to_id, existing, known, args.max_add)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(proposal, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    m = proposal["_meta"]
    print(f"Proposal -> {args.output}: {m['ingredients_touched']} ingredients, "
          f"{m['total_additions']} additions (known-vocab only, <= {args.max_add} each), "
          f"{m['unmatched_entities']} entities for review, "
          f"{m['distinct_out_of_vocab_compounds_skipped']} out-of-vocab compounds skipped")

    if args.apply:
        added = apply_proposal(proposal)
        print(f"APPLIED: +{added} compound links across ingredients (no new compounds, no stubs).")
        print("Now rebuild: python3 scripts/compute_descriptor_harmony.py "
              "&& python3 scripts/render_flavor_wheel.py && python -m pytest tests/ -q")


if __name__ == "__main__":
    main()
