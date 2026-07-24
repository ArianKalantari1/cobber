#!/usr/bin/env python3
"""Enrich Australian-native ingredient profiles from published essential-oil studies.

FlavorDB2 and the other food databases don't carry bush foods, so the natives —
Cobber's signature — stay thin unless curated by hand from the botanical
literature. This script does exactly that: for each native it adds well-documented
aroma constituents of that species, drawn from published essential-oil / GC-MS
composition studies. Every added compound is already in Cobber's compound
vocabulary (so it carries a cited descriptor entry — no orphans, no invented
descriptors), and every constituent below is a characteristic, documented part of
that plant's aroma, not padding.

This is offline, build-time, human-approved data (the project's standing pattern).
The whole pass is flagged PROVISIONAL in each ingredient's notes — Ari verifies the
constituent lists against the cited studies and removes the flag per entry once
satisfied (same workflow as the taste-axis backfill). Re-runnable / idempotent.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
DESCRIPTORS_PATH = ROOT / "data" / "compound_descriptors.json"

PROVISIONAL_TAG = "[native EO enrichment — PROVISIONAL, verify vs cited study]"

# native_id -> {add: [compound_ids already in vocab], cite: EO-literature note}
# Each compound is a documented, characteristic constituent of that species.
CURATED: dict[str, dict] = {
    "desert_lime": {
        "add": ["myrcene", "alpha_pinene", "beta_pinene", "linalool"],
        "cite": "Citrus glauca peel oil: limonene-dominant with myrcene + pinene monoterpenes and trace linalool.",
    },
    "anise_myrtle": {
        "add": ["limonene", "myrcene"],
        "cite": "Syzygium anisatum leaf oil (Brophy et al.): anethole/methyl-chavicol dominant; minor limonene + myrcene.",
    },
    "cinnamon_myrtle": {
        "add": ["methyl_cinnamate", "beta_caryophyllene", "linalool"],
        "cite": "Backhousia myrtifolia leaf oil (cinnamaldehyde chemotype): cinnamic esters + caryophyllene + linalool.",
    },
    "davidson_plum": {
        "add": ["hexanal", "beta_ionone", "ethyl_2_methylbutyrate"],
        "cite": "Davidsonia fruit volatiles: damascenone/ionone carotenoid notes over green C6 aldehydes and fruity esters.",
    },
    "bush_tomato": {
        "add": ["methional", "beta_damascenone"],
        "cite": "Solanum centrale (dried): sotolon/furaneol caramel with methional savoury and damascenone.",
    },
    "lemon_myrtle": {
        "add": ["limonene", "myrcene"],
        "cite": "Backhousia citriodora leaf oil: citral >90% with accompanying myrcene + limonene.",
    },
    "lemon_aspen": {
        "add": ["geraniol", "myrcene"],
        "cite": "Acronychia acidula fruit: citral/limonene citrus with geraniol and myrcene.",
    },
    "riberry": {
        "add": ["beta_caryophyllene", "ethyl_butyrate"],
        "cite": "Syzygium luehmannii: clove-cinnamon eugenol/cinnamaldehyde with caryophyllene and berry esters.",
    },
    "pepperberry": {
        "add": ["beta_pinene", "sabinene", "myrcene", "limonene"],
        "cite": "Tasmannia lanceolata leaf/berry oil: polygodial pungency over a monoterpene-rich base (pinenes, sabinene, myrcene, limonene).",
    },
    "wattleseed": {
        "add": ["2_furfurylthiol", "vanillin"],
        "cite": "Roasted Acacia seed: Maillard pyrazines/furans with coffee furfurylthiol and vanillin.",
    },
    "quandong": {
        "add": ["delta_decalactone", "hexanal"],
        "cite": "Santalum acuminatum fruit: gamma/delta lactones and benzaldehyde stone-fruit with green C6 notes.",
    },
    "muntries": {
        "add": ["ethyl_2_methylbutyrate", "hexyl_acetate", "cinnamaldehyde"],
        "cite": "Kunzea pomifera: spiced-apple damascenone with apple esters and a cinnamaldehyde lift.",
    },
    "strawberry_gum": {
        "add": ["methyl_cinnamate", "ethyl_2_methylbutyrate"],
        "cite": "Eucalyptus olida leaf: furaneol-driven strawberry with fruity/balsamic esters.",
    },
    "native_river_mint": {
        "add": ["isomenthone", "limonene", "eucalyptol"],
        "cite": "Mentha australis oil: menthol/menthone/carvone mint with limonene and 1,8-cineole.",
    },
    "finger_lime": {
        "add": ["myrcene", "alpha_pinene", "linalool"],
        "cite": "Citrus australasica peel oil: limonene/citral citrus with myrcene, pinene and linalool.",
    },
}


def main() -> None:
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        ingredients = json.load(handle)
    with DESCRIPTORS_PATH.open(encoding="utf-8") as handle:
        known_compounds = set(json.load(handle)["compounds"])

    by_id = {e["id"]: e for e in ingredients}

    # Validate before touching anything: every target is a native, every added
    # compound is in vocab AND has a descriptor entry (no orphans, no fabrication).
    for native_id, spec in CURATED.items():
        entry = by_id.get(native_id)
        if entry is None:
            raise SystemExit(f"Unknown native id {native_id!r}.")
        if not entry.get("is_native"):
            raise SystemExit(f"{native_id!r} is not flagged is_native; refusing.")
        for compound in spec["add"]:
            if compound not in known_compounds:
                raise SystemExit(
                    f"{native_id}: compound {compound!r} has no descriptor entry — "
                    "add it to compound_descriptors.json first (never orphan a compound)."
                )

    total_added = 0
    touched = 0
    for native_id, spec in CURATED.items():
        entry = by_id[native_id]
        have = list(entry.get("compounds", []))
        added_here = [c for c in spec["add"] if c not in have]
        if not added_here:
            continue
        entry["compounds"] = have + added_here
        total_added += len(added_here)
        touched += 1

        # Cite in source; flag the pass provisional in notes (idempotent).
        source = entry.get("source", "").rstrip()
        if spec["cite"] not in source:
            entry["source"] = (source + " | Enrichment: " + spec["cite"]).strip(" |").strip()
        notes = entry.get("notes", "")
        if PROVISIONAL_TAG not in notes:
            entry["notes"] = (notes.rstrip() + " " + PROVISIONAL_TAG).strip()

        print(f"  {native_id}: +{len(added_here)} ({', '.join(added_here)})")

    with INGREDIENTS_PATH.open("w", encoding="utf-8") as handle:
        json.dump(ingredients, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"Enriched {touched} natives, +{total_added} compound links -> {INGREDIENTS_PATH}")
    print("Now rebuild: python3 scripts/compute_descriptor_harmony.py && "
          "python3 scripts/render_flavor_wheel.py && python -m pytest tests/ -q")


if __name__ == "__main__":
    main()
