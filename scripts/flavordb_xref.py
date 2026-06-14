#!/usr/bin/env python3
"""
scripts/flavordb_xref.py

Offline cross-reference: compares our ingredient compound vocabulary against
FlavorDB2 (via the public CSV mirror at tarek-kerbedj/flavor_db2.0 on GitHub).

For each pantry ingredient, finds the closest FlavorDB entity, then reports:
  - Confirmed:  compound is in FlavorDB AND already in our vocab (corroboration)
  - Candidates: compound is in FlavorDB but NOT in our vocab (review queue)
  - Ours only:  compound we curated that FlavorDB doesn't list (typically OAV-backed)

Outputs  data/flavordb_review.txt  — human-readable, Ari reviews before any
adoption.  NEVER writes to ingredients.json.  All decisions stay with the
bartender.

Usage:
    python3 scripts/flavordb_xref.py            # use cached CSVs if present
    python3 scripts/flavordb_xref.py --download  # force re-fetch from GitHub
"""

import argparse
import ast
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = ROOT / "data" / "raw"
ENTITIES_CSV = RAW / "flavordb_entities.csv"
MOLECULES_CSV = RAW / "flavordb_molecules.csv"
REVIEW_OUT = ROOT / "data" / "flavordb_review.txt"
INGREDIENTS_JSON = ROOT / "data" / "ingredients.json"

ENTITIES_URL = (
    "https://raw.githubusercontent.com/tarek-kerbedj/flavor_db2.0/master/flavordb.csv"
)
MOLECULES_URL = (
    "https://raw.githubusercontent.com/tarek-kerbedj/flavor_db2.0/master/molecules.csv"
)

# ── Manual synonym table: FlavorDB-normalised name → our compound ID ──────────
# Only for compounds where normalise() alone won't produce a match.
# None = "this FlavorDB name does NOT map to any of our IDs — skip it"
SYNONYMS: dict[str, str | None] = {
    # furanones
    "2_5_dimethyl_4_hydroxy_3_2h_furanone": "furaneol",
    "2_5_dimethyl_4_hydroxy_2h_furan_3_one": "furaneol",
    "hdmf": "furaneol",
    "dmhf": "furaneol",
    # raspberry ketone
    "4__4_hydroxyphenyl__2_butanone": "raspberry_ketone",
    "4_4_hydroxyphenyl_butan_2_one": "raspberry_ketone",
    # damascenone
    "e__beta_damascenone": "beta_damascenone",
    "trans_beta_damascenone": "beta_damascenone",
    # methional / 3-methylthiopropanal
    "3_methylthiopropanal": "methional",
    "3_methylthio_propanal": "methional",
    # rose oxide
    "2_2_methyl_6_methylenecyclohexyl_propan_2_ol": "rose_oxide",
    "2__2_methyl_6_methylenecyclohexyl_propan_2_ol": "rose_oxide",
    # 1-octen-3-ol (mushroom note)
    "oct_1_en_3_ol": "1_octen_3_ol",
    # diacetyl
    "butane_2_3_dione": "diacetyl",
    "2_3_butanedione": "diacetyl",
    "2_3_dioxobutane": "diacetyl",
    "acetoin": None,  # different compound, do NOT map
    # sotolon
    "3_hydroxy_4_5_dimethyl_2_5h_furanone": "sotolon",
    "3_hydroxy_4_5_dimethylfuran_2_5h_one": "sotolon",
    # gingerol variants
    "6_gingerol": "gingerol",
    "_6__gingerol": "gingerol",
    # eucalyptol / 1,8-cineole
    "1_8_cineole": "eucalyptol",
    "cineole": "eucalyptol",
    # furfurylthiol / coffee note
    "2_furanmethanethiol": "2_furfurylthiol",
    "furfuryl_mercaptan": "2_furfurylthiol",
    "2_furfuryl_mercaptan": "2_furfurylthiol",
    # ethyl 2-methylbutyrate
    "ethyl_2_methyl_butanoate": "ethyl_2_methylbutyrate",
    "ethyl_2_methylbutanoate": "ethyl_2_methylbutyrate",
    # p-anisaldehyde: smells anise-like but is a different compound to anethole
    "p_anisaldehyde": None,
    "4_methoxybenzaldehyde": None,
    # ionone variants — keep separate IDs
    "alpha_ionone": "ionone",
    "beta_ionone": "beta_ionone",
}

# ── Entity-level name overrides: our ingredient ID → FlavorDB alias ───────────
# Use when automatic matching picks wrong entity, or FlavorDB name differs.
# Set to None to explicitly mark an ingredient as "not in FlavorDB".
ENTITY_OVERRIDES: dict[str, str | None] = {
    # Citrus: FlavorDB only has peel oil, not the whole fruit
    "lime": "lime peel oil",
    "lemon": "lemon peel oil",
    "orange": None,          # FlavorDB has "orange peel oil" (mandarin only) — no direct match
    "grapefruit": "grapefruit peel oil",
    "bergamot": "bergamot peel oil",
    "blood_orange": "blood orange",
    # Berries: FlavorDB spells these with spaces
    "blackcurrant": "black currant",
    # FlavorDB uses plain "pepper" for what we call black_pepper
    "black_pepper": "pepper",
    "white_pepper": "white pepper",
    # FlavorDB has "coriander" covering both leaf and seed
    "coriander_leaf": "coriander",
    "coriander_seed": "coriander",
    # Spirits: FlavorDB has generic base spirit names
    "white_rum": "rum",
    "dark_rum": "rum",
    "spiced_rum": "rum",
    "white_tequila": "tequila",
    "reposado_tequila": "tequila",
    "anejo_tequila": "tequila",
    "london_dry_gin": "gin",
    "old_tom_gin": "gin",
    "navy_gin": "gin",
    # Ingredients genuinely absent from FlavorDB — mark explicitly
    "egg_white": None,     # not in FlavorDB; near-zero aroma anyway (correct)
    "egg_yolk": None,      # not in FlavorDB; needs primary lit for sulfur/fatty volatiles
    "cola": None,          # trade secret formulation
    "orgeat": None,        # processed composite, not a natural ingredient
    "worcestershire": None,  # trade secret
    "shio_koji": None,     # too niche/Japanese
    "pink_peppercorn": None,  # schinus not in FlavorDB (different family from pepper)
    "gentian": None,       # bitter botanical, not in FlavorDB
    "demerara": None,      # sugar, not in FlavorDB
    "lavender": None,
    "juniper": None,
    "lemongrass": None,
    "elderflower": None,
    "lemon_myrtle": None,
    "lemon_aspen": None,
    "anise_myrtle": None,
    "cinnamon_myrtle": None,
    "riberry": None,
    "pepperberry": None,
    "wattleseed": None,
    "davidson_plum": None,
    "quandong": None,
    "muntries": None,
    "bush_tomato": None,
    "strawberry_gum": None,
    "native_river_mint": None,
    "desert_lime": None,
    "finger_lime": None,
    "kokuto": None,
}

# Tokens that flag an entity as an extract/concentrate (not the whole ingredient)
EXTRACT_TOKENS = {"oil", "peel", "extract", "essence", "absolute", "oleoresin",
                  "concentrate", "tincture", "distillate", "absolute"}


def download(url: str, dest: Path) -> None:
    print(f"  downloading {url} …", file=sys.stderr)
    urllib.request.urlretrieve(url, dest)
    print(f"  saved to {dest}", file=sys.stderr)


def parse_set_literal(s: str) -> set[int]:
    """Parse FlavorDB's Python-set-literal CID strings: '{26049, 6949, …}'"""
    if not s or s.strip() in ("", "{}"):
        return set()
    try:
        val = ast.literal_eval(s.strip())
        if isinstance(val, set):
            return {int(x) for x in val}
        if isinstance(val, (int, float)):
            return {int(val)}
    except Exception:
        pass
    # fallback: extract integers
    return {int(m) for m in re.findall(r"\d+", s)}


def parse_str_set(s: str) -> set[str]:
    """Parse FlavorDB's Python-set-literal string sets: "{'fruity', 'sweet'}" """
    if not s or s.strip() in ("", "{}"):
        return set()
    try:
        val = ast.literal_eval(s.strip())
        if isinstance(val, (set, frozenset)):
            return {str(x) for x in val}
    except Exception:
        pass
    return set(re.findall(r"'([^']+)'", s))


def normalise(name: str) -> str:
    """Normalise a compound name to our underscore-style ID convention."""
    n = name.lower()
    n = re.sub(r"[^a-z0-9]+", "_", n)
    return n.strip("_")


def load_csv_raw(path: Path) -> tuple[list[str], list[list[str]]]:
    """Read a CSV robustly into (headers, rows) without pandas."""
    import csv
    with open(path, encoding="utf-8", errors="replace") as fh:
        reader = csv.reader(fh)
        rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def col_idx(headers: list[str], name: str) -> int:
    """Return the column index for a header name (case-insensitive strip)."""
    for i, h in enumerate(headers):
        if h.strip().lower() == name.lower():
            return i
    raise KeyError(f"Column {name!r} not found in {headers}")


def build_molecule_map(path: Path) -> dict[int, dict]:
    """
    CID (int) → {"name": str, "odour": set[str]}

    molecules.csv actual layout (pandas double-index export):
      col 0: pandas row index  (ignore)
      col 1: "Unnamed: 0"      (another sequential index, ignore)
      col 2: "pubchem id"      (the real PubChem CID)
      col 3: "common name"     (compound name)
      col 4: "flavor profile"  (set literal of odour descriptors)
    """
    headers, rows = load_csv_raw(path)
    if not rows:
        raise RuntimeError(f"molecules.csv is empty at {path}")

    cid_col = col_idx(headers, "pubchem id")
    name_col = col_idx(headers, "common name")
    odour_col = col_idx(headers, "flavor profile")

    molecule_map: dict[int, dict] = {}
    for r in rows:
        try:
            cid = int(float(r[cid_col]))
        except (ValueError, IndexError):
            continue
        name = r[name_col].strip() if name_col < len(r) else ""
        odour = (
            parse_str_set(r[odour_col])
            if odour_col < len(r)
            else set()
        )
        molecule_map[cid] = {"name": name, "odour": odour}

    return molecule_map


def build_entity_index(path: Path) -> list[dict]:
    """
    Returns list of entity dicts:
      {entity_id, alias, synonyms, category, cids: set[int]}

    flavordb.csv actual layout (pandas double-index export):
      col 0: pandas row index   (ignore)
      col 1: "entity id"        (integer entity ID)
      col 2: "alias"            (ingredient name)
      col 3: "synonyms"         (set literal of strings)
      col 4: "scientific name"  (ignore for our purposes)
      col 5: "category"
      col 6: "molecules"        (set literal of PubChem CIDs)
    """
    headers, rows = load_csv_raw(path)

    entity_id_col = col_idx(headers, "entity id")
    alias_col = col_idx(headers, "alias")
    synonyms_col = col_idx(headers, "synonyms")
    category_col = col_idx(headers, "category")
    molecules_col = col_idx(headers, "molecules")

    entities = []
    for r in rows:
        try:
            entity_id = int(float(r[entity_id_col])) if entity_id_col < len(r) else -1
        except (ValueError, IndexError):
            continue
        alias = r[alias_col].strip() if alias_col < len(r) else ""
        synonyms = parse_str_set(r[synonyms_col]) if synonyms_col < len(r) else set()
        category = r[category_col].strip() if category_col < len(r) else ""
        cids = parse_set_literal(r[molecules_col]) if molecules_col < len(r) else set()
        if alias:
            entities.append({
                "entity_id": entity_id,
                "alias": alias,
                "synonyms": synonyms,
                "category": category,
                "cids": cids,
            })
    return entities



def match_entity(
    ing_id: str,
    ing_name: str,
    entities: list[dict],
    overrides: dict[str, str | None],
) -> tuple[dict | None, str]:
    """
    Find the best FlavorDB entity for our ingredient.
    Returns (entity_dict | None, match_quality)
    match_quality ∈ {"exact", "partial", "override", "none", "absent"}
    """
    if ing_id in overrides:
        target = overrides[ing_id]
        if target is None:
            return None, "absent"  # explicitly not in FlavorDB
        for ent in entities:
            if ent["alias"].lower() == target.lower():
                return ent, "override"
        return None, "none"

    # Normalise our name for comparison
    our_norm = normalise(ing_id.replace("_", " "))

    best: dict | None = None
    best_quality = "none"

    for ent in entities:
        alias_norm = normalise(ent["alias"])
        syns_norm = {normalise(s) for s in ent["synonyms"]}
        all_names = {alias_norm} | syns_norm

        # Exact match
        if our_norm in all_names:
            return ent, "exact"

        our_tokens = set(our_norm.split("_"))
        alias_tokens = set(alias_norm.split("_"))

        # Our tokens ⊂ theirs: e.g. our "mint" inside their "peppermint"
        if our_tokens and our_tokens.issubset(alias_tokens) and len(our_tokens) >= 1:
            if best_quality not in ("exact", "partial"):
                best, best_quality = ent, "partial"

        # Their tokens ⊂ ours: e.g. their "pepper" inside our "black_pepper"
        # Only match when their name has ≥ 2 tokens OR is an exact single word
        if alias_tokens and alias_tokens.issubset(our_tokens) and len(alias_tokens) >= 1:
            if best_quality not in ("exact", "partial"):
                best, best_quality = ent, "partial"

    return best, best_quality


def cid_to_our_id(cid: int, name: str, synonyms: dict) -> str | None:
    """Map a FlavorDB CID+name to one of our compound IDs. None = no match."""
    norm = normalise(name)
    # Check explicit synonym table first
    if norm in synonyms:
        return synonyms[norm]
    # Direct name match against our vocab
    return norm if norm in OUR_COMPOUNDS else None


def is_extract(entity: dict) -> bool:
    """Return True if the entity is an extract/oil/peel rather than the raw ingredient."""
    tokens = set(entity["alias"].lower().split())
    return bool(tokens & EXTRACT_TOKENS)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--download", action="store_true", help="Force re-fetch CSVs")
    args = parser.parse_args()

    RAW.mkdir(parents=True, exist_ok=True)

    if args.download or not ENTITIES_CSV.exists():
        download(ENTITIES_URL, ENTITIES_CSV)
    else:
        print("Using cached entities CSV (pass --download to refresh)", file=sys.stderr)

    if args.download or not MOLECULES_CSV.exists():
        download(MOLECULES_URL, MOLECULES_CSV)
    else:
        print("Using cached molecules CSV (pass --download to refresh)", file=sys.stderr)

    print("Parsing molecules …", file=sys.stderr)
    mol_map = build_molecule_map(MOLECULES_CSV)
    print(f"  loaded {len(mol_map)} molecules", file=sys.stderr)

    print("Parsing entities …", file=sys.stderr)
    entities = build_entity_index(ENTITIES_CSV)
    print(f"  loaded {len(entities)} entities", file=sys.stderr)

    print("Loading our ingredient data …", file=sys.stderr)
    with open(INGREDIENTS_JSON) as f:
        ingredients = json.load(f)
    print(f"  loaded {len(ingredients)} ingredients", file=sys.stderr)

    lines: list[str] = [
        "FlavorDB cross-reference report",
        "================================",
        "Source: tarek-kerbedj/flavor_db2.0 (mirror of FlavorDB2, IIIT-Delhi)",
        "WARNING: FlavorDB lists ALL detected compounds, not just key odorants.",
        "  Candidates need OAV/GC-O citation before adoption into ingredients.json.",
        "",
    ]

    confirmed_total = 0
    candidate_total = 0
    no_match_total = 0

    for ing in sorted(ingredients, key=lambda x: x["id"]):
        ing_id: str = ing["id"]
        ing_name: str = ing.get("display_name", ing_id)
        our_compounds: set[str] = set(ing.get("compounds", []))

        entity, quality = match_entity(ing_id, ing_name, entities, ENTITY_OVERRIDES)

        lines.append(f"\n{'='*60}")
        lines.append(f"  {ing_id}  ({ing_name})")
        lines.append(f"{'='*60}")

        if quality == "absent":
            lines.append("  [NOT IN FLAVORDB — ingredient is too niche/regional]")
            lines.append("  → Research manually via GC-O/OAV literature.")
            no_match_total += 1
            continue

        if entity is None or quality == "none":
            lines.append("  [NO FLAVORDB MATCH FOUND]")
            lines.append("  → Research manually via GC-O/OAV literature.")
            no_match_total += 1
            continue

        lines.append(f"  FlavorDB entity: \"{entity['alias']}\" (id={entity['entity_id']}, {quality} match)")

        if is_extract(entity):
            lines.append("  ⚠  EXTRACT/OIL match — FlavorDB entity is a concentrate, not the")
            lines.append("     whole ingredient. Compound profile is terpene-heavy / may miss")
            lines.append("     polar acids + non-volatile compounds. Treat candidates cautiously.")

        if not entity["cids"]:
            lines.append("  [FlavorDB has 0 compounds for this entity]")
            continue

        # Map CIDs → names → our IDs
        confirmed: list[dict] = []
        candidates: list[dict] = []
        ours_only = sorted(our_compounds)

        for cid in sorted(entity["cids"]):
            mol = mol_map.get(cid)
            if mol is None:
                continue
            mol_name = mol["name"]
            odour = mol["odour"]
            our_id = cid_to_our_id(cid, mol_name, SYNONYMS)

            if our_id and our_id in our_compounds:
                confirmed.append({"our_id": our_id, "cid": cid, "name": mol_name, "odour": odour})
                if our_id in ours_only:
                    ours_only.remove(our_id)
            elif our_id and our_id in OUR_COMPOUNDS:
                # In our global vocab but not assigned to this ingredient
                candidates.append({
                    "our_id": our_id, "cid": cid, "name": mol_name, "odour": odour,
                    "in_vocab": True,
                })
            else:
                # FlavorDB has it, normalised name not in our vocab
                norm = normalise(mol_name)
                if norm not in {None}:
                    candidates.append({
                        "our_id": None, "cid": cid, "name": mol_name,
                        "norm": norm, "odour": odour, "in_vocab": False,
                    })

        confirmed_total += len(confirmed)
        candidate_total += len(candidates)

        if confirmed:
            lines.append(f"\n  CONFIRMED ({len(confirmed)} compound(s) — FlavorDB corroborates our curation):")
            for c in confirmed:
                odour_str = ", ".join(sorted(c["odour"])[:4]) if c["odour"] else "—"
                lines.append(f"    ✓ {c['our_id']:30s}  CID {c['cid']:>8}  [{odour_str}]")
        else:
            lines.append("\n  CONFIRMED: (none — FlavorDB compounds don't overlap our vocab)")

        # Only show candidates that look plausibly key-odorant (filter pure-trace noise)
        # Heuristic: if the entity has >60 compounds it's a bulk GC-MS list;
        # only show those whose odour set overlaps the ingredient's descriptors
        ing_descriptors: set[str] = set(ing.get("descriptors", []))
        plausible = []
        for c in candidates:
            odour = c["odour"]
            if not ing_descriptors or odour & ing_descriptors:
                plausible.append(c)
            elif len(entity["cids"]) <= 30:
                plausible.append(c)  # small list → show all

        if plausible:
            lines.append(f"\n  CANDIDATES FOR REVIEW ({len(plausible)} shown, {len(candidates)} total):")
            lines.append("  Need OAV/GC-O citation before adoption.")
            for c in plausible[:20]:  # cap at 20 per ingredient
                if c["in_vocab"]:
                    tag = f"[in vocab as {c['our_id']}]"
                else:
                    tag = f"[new — would need id: {c.get('norm', '?')}]"
                odour_str = ", ".join(sorted(c["odour"])[:4]) if c["odour"] else "—"
                lines.append(
                    f"    ?  {c['name']:35s}  CID {c['cid']:>8}  {tag}  [{odour_str}]"
                )
        else:
            lines.append("\n  CANDIDATES: (none overlap descriptors, or all already confirmed)")

        if ours_only:
            lines.append(f"\n  OURS ONLY (not in FlavorDB — likely OAV-backed from primary lit):")
            for cid in sorted(ours_only):
                lines.append(f"    ·  {cid}")

    lines.append("\n" + "="*60)
    lines.append("SUMMARY")
    lines.append("="*60)
    lines.append(f"  Ingredients:  {len(ingredients)}")
    lines.append(f"  No match:     {no_match_total}")
    lines.append(f"  Confirmed:    {confirmed_total}  (FlavorDB corroborates our curated compounds)")
    lines.append(f"  Candidates:   {candidate_total}  (FlavorDB compounds we haven't adopted yet)")
    lines.append("")
    lines.append("Next step: for any Candidate you want to adopt, find the OAV/GC-O")
    lines.append("primary paper, confirm it's a key odorant, then add to ingredients.json")
    lines.append("with the citation in notes. Do not bulk-import.")

    report = "\n".join(lines) + "\n"
    REVIEW_OUT.write_text(report)
    print(f"\nReport written to {REVIEW_OUT}", file=sys.stderr)

    # Quick console summary
    print(f"\nSummary: {confirmed_total} confirmed, {candidate_total} candidates, {no_match_total} no match")


# Loaded at module level so cid_to_our_id() can reference it
with open(INGREDIENTS_JSON) as _f:
    _data = json.load(_f)
OUR_COMPOUNDS: set[str] = set()
for _ing in _data:
    OUR_COMPOUNDS.update(_ing.get("compounds", []))

if __name__ == "__main__":
    main()
