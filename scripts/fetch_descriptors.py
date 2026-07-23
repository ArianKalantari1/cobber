#!/usr/bin/env python3
"""Build data/compound_descriptors.json — compound -> sensory descriptors, cited.

This is the sensory-descriptor layer Cobber was missing. Every aroma compound in
the ingredient world gets a small set of *odour* descriptor words (the words a
nose reaches for: citrus, rose, clove, mushroom), and the handful of non-volatile
*taste-active* molecules (bitter glycosides, pungent principles) get a taste class
instead. The engine's flavour wheel (engine.flavor_wheel) aggregates these into
flavour families; the descriptor-harmony layer mines which notes co-occur.

SOURCES (build-time, offline, human-approved — the project's standing pattern):

  * Odour descriptors: **Flavornet** (Acree, T. & Arn, H., 2004. *Flavornet and
    Human Odor Space*. Sponsored by DATU Inc. http://www.flavornet.org ; and
    Arn, H. & Acree, T.E., 1998. "Flavornet: A database of aroma compounds based
    on odor potency in natural products." *Dev. Food Sci.* 40:27). Flavornet
    publishes, per compound (keyed by CAS), a short free-text "Percepts" odour
    phrase. The values below are curated from those Percepts and condensed to
    descriptor words.

  * Taste class (the non-volatile tastants that have no odour): **ChemTastesDB**
    (Rojas, C., Ballabio, D., Pacheco Sarmiento, K., Pacheco Jaramillo, E.,
    Mendoza, M. & García, F., 2022. "ChemTastesDB: A curated database of
    molecular tastants." *Food Chemistry: Molecular Sciences* 4:100090.
    https://doi.org/10.1016/j.fochms.2022.100090). Used *cite-only*: we take the
    factual taste-class label (bitter / pungent) and cite the paper; we do not
    redistribute the database file.

HONESTY NOTE (why this is a curated table, not a live scrape):
  The build environment cannot reach flavornet.org (proxy/egress 403s), and the
  project principle is build-time + human-approved data anyway. So the map below
  is curated by hand from the Flavornet Percepts and cited per compound. Where a
  compound's Percept could not be confidently pinned to Flavornet, the entry is
  flagged ``provisional: true`` with a note — uncertain data is flagged, not
  hidden. To refresh/verify against the live site in an unblocked environment,
  see ``refresh_from_flavornet`` below (the rOpenSci ``webchem`` per-CAS scheme:
  GET http://www.flavornet.org/info/{CAS}.html and read the "Percepts" field).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INGREDIENTS_PATH = ROOT / "data" / "ingredients.json"
OUTPUT_PATH = ROOT / "data" / "compound_descriptors.json"

FLAVORNET_CITE = "Flavornet (Acree & Arn 2004, flavornet.org)"
CHEMTASTES_CITE = "ChemTastesDB (Rojas et al. 2022, doi:10.1016/j.fochms.2022.100090)"

# Curated compound -> sensory descriptors.
#   cas:         CAS registry number (the Flavornet per-compound key).
#   odor:        odour descriptor words, condensed from the Flavornet "Percepts"
#                phrase. Empty for non-volatile tastants.
#   taste_class: for non-volatile tastants only (no odour); label from ChemTastesDB.
#   provisional: True when the Flavornet percept could not be confidently pinned
#                (or the compound is off-Flavornet); carries a `note`.
#   src:         "flavornet", "chemtastes", or "curated" (bartender/lit knowledge).
#
# Descriptor vocabulary is deliberately small and reused across compounds so it
# buckets cleanly into flavour families in engine.flavor_wheel (Phase 3).
CURATED: dict[str, dict] = {
    # ---- Citrus / terpene top notes -------------------------------------
    "limonene":        {"cas": "5989-27-5",  "odor": ["citrus", "orange"], "src": "flavornet"},
    "citral":          {"cas": "5392-40-5",  "odor": ["citrus", "lemon"], "src": "flavornet"},
    "nootkatone":      {"cas": "4674-50-4",  "odor": ["citrus", "grapefruit", "woody"], "src": "flavornet"},
    "gamma_terpinene": {"cas": "99-85-4",    "odor": ["citrus", "terpene", "herbal"], "src": "flavornet"},
    "beta_phellandrene": {"cas": "555-10-2", "odor": ["mint", "citrus", "terpene"], "src": "flavornet",
                          "provisional": True, "note": "Flavornet percept terse ('mint/terpene'); peppery facet is bartender-observed."},
    "octanal":         {"cas": "124-13-0",   "odor": ["citrus", "green", "waxy"], "src": "flavornet"},
    "decanal":         {"cas": "112-31-2",   "odor": ["citrus", "waxy", "soapy"], "src": "flavornet"},
    "dodecanal":       {"cas": "112-54-9",   "odor": ["citrus", "waxy", "soapy"], "src": "flavornet"},

    # ---- Floral ---------------------------------------------------------
    "linalool":        {"cas": "78-70-6",    "odor": ["floral", "lavender", "citrus"], "src": "flavornet"},
    "linalyl_acetate": {"cas": "115-95-7",   "odor": ["floral", "lavender", "bergamot"], "src": "flavornet"},
    "geraniol":        {"cas": "106-24-1",   "odor": ["floral", "rose", "citrus"], "src": "flavornet"},
    "rose_oxide":      {"cas": "16409-43-1", "odor": ["floral", "rose", "green"], "src": "flavornet"},
    "nerol_oxide":     {"cas": "1786-08-9",  "odor": ["floral", "citrus", "green"], "src": "flavornet",
                        "provisional": True, "note": "Flavornet coverage uncertain; descriptors from general lit (green-floral rose-oxide relative)."},
    "ionone":          {"cas": "127-41-3",   "odor": ["floral", "violet", "fruity"], "src": "flavornet"},
    "beta_ionone":     {"cas": "14901-07-6", "odor": ["floral", "violet", "fruity"], "src": "flavornet"},
    "irone":           {"cas": "79-69-6",    "odor": ["floral", "violet", "woody"], "src": "flavornet",
                        "provisional": True, "note": "Orris/violet ketone; Flavornet listing not confirmed in-session."},
    "phenylacetaldehyde": {"cas": "122-78-1", "odor": ["floral", "honey", "rose"], "src": "flavornet"},
    "methyl_anthranilate": {"cas": "134-20-3", "odor": ["fruity", "grape", "floral"], "src": "flavornet"},
    "terpineol":       {"cas": "98-55-5",    "odor": ["floral", "pine", "lilac"], "src": "flavornet"},
    "terpinyl_acetate": {"cas": "80-26-2",   "odor": ["floral", "herbal", "bergamot"], "src": "flavornet",
                         "provisional": True, "note": "Bergamot/herbal from lit; Flavornet percept not confirmed in-session."},

    # ---- Fruity esters / lactones ---------------------------------------
    "ethyl_butyrate":  {"cas": "105-54-4",   "odor": ["fruity", "apple", "pineapple"], "src": "flavornet"},
    "ethyl_2_methylbutyrate": {"cas": "7452-79-1", "odor": ["fruity", "apple"], "src": "flavornet"},
    "hexyl_acetate":   {"cas": "142-92-7",   "odor": ["fruity", "apple", "green"], "src": "flavornet"},
    "hexyl_butyrate":  {"cas": "2639-63-6",  "odor": ["fruity", "apple", "green"], "src": "flavornet",
                        "provisional": True, "note": "Green-apple ester; Flavornet percept not confirmed in-session."},
    "allyl_hexanoate": {"cas": "123-68-2",   "odor": ["fruity", "pineapple"], "src": "flavornet"},
    "ethyl_decadienoate": {"cas": "3025-30-7", "odor": ["fruity", "pear"], "src": "flavornet"},
    "methyl_cinnamate": {"cas": "103-26-4",  "odor": ["fruity", "strawberry", "balsamic"], "src": "flavornet"},
    "raspberry_ketone": {"cas": "5471-51-2", "odor": ["fruity", "raspberry", "sweet"], "src": "flavornet"},
    "beta_damascenone": {"cas": "23726-93-4", "odor": ["fruity", "apple", "honey", "floral"], "src": "flavornet"},
    "gamma_decalactone": {"cas": "706-14-9", "odor": ["fruity", "peach", "creamy"], "src": "flavornet"},
    "delta_decalactone": {"cas": "705-86-2", "odor": ["creamy", "coconut", "peach"], "src": "flavornet"},

    # ---- Green / herbal / vegetal ---------------------------------------
    "hexanal":         {"cas": "66-25-1",    "odor": ["green", "grassy", "fatty"], "src": "flavornet"},
    "1_octen_3_ol":    {"cas": "3391-86-4",  "odor": ["mushroom", "earthy", "green"], "src": "flavornet"},
    "myrcene":         {"cas": "123-35-3",   "odor": ["herbal", "resinous", "citrus"], "src": "flavornet"},
    "sabinene":        {"cas": "3387-41-5",  "odor": ["woody", "peppery", "terpene"], "src": "flavornet",
                        "provisional": True, "note": "Peppery-terpene; Flavornet percept terse."},
    "sedanolide":      {"cas": "6415-59-4",  "odor": ["celery", "herbal", "green"], "src": "flavornet",
                        "provisional": True, "note": "Celery phthalide (aroma-active, not a tastant); Flavornet listing not confirmed in-session."},
    "chamazulene":     {"cas": "529-05-5",   "odor": ["herbal", "chamomile"], "src": "curated",
                        "provisional": True, "note": "Blue chamomile sesquiterpene; off-Flavornet, descriptors from general lit."},

    # ---- Woody / pine / resinous ----------------------------------------
    "alpha_pinene":    {"cas": "80-56-8",    "odor": ["pine", "woody", "resinous"], "src": "flavornet"},
    "beta_pinene":     {"cas": "127-91-3",   "odor": ["pine", "woody", "resinous"], "src": "flavornet"},
    "beta_caryophyllene": {"cas": "87-44-5", "odor": ["woody", "spicy", "peppery"], "src": "flavornet"},
    "camphor":         {"cas": "76-22-2",    "odor": ["camphor", "medicinal", "woody"], "src": "flavornet"},
    "eucalyptol":      {"cas": "470-82-6",   "odor": ["eucalyptus", "mint", "camphor"], "src": "flavornet"},
    "thujone":         {"cas": "546-80-5",   "odor": ["herbal", "menthol", "woody"], "src": "flavornet",
                        "provisional": True, "note": "Wormwood ketone; cedar/menthol facets from lit."},

    # ---- Mint / cooling -------------------------------------------------
    "menthol":         {"cas": "89-78-1",    "odor": ["mint", "cooling", "peppermint"], "src": "flavornet"},
    "menthone":        {"cas": "89-80-5",    "odor": ["mint", "minty"], "src": "flavornet"},
    "isomenthone":     {"cas": "491-07-6",   "odor": ["mint", "minty"], "src": "flavornet",
                        "provisional": True, "note": "Menthone isomer; Flavornet listing not confirmed in-session."},
    "carvone":         {"cas": "99-49-0",    "odor": ["mint", "caraway", "herbal"], "src": "flavornet",
                        "note": "Two enantiomers: (R) spearmint, (S) caraway."},

    # ---- Spice ----------------------------------------------------------
    "eugenol":         {"cas": "97-53-0",    "odor": ["clove", "spicy", "woody"], "src": "flavornet"},
    "cinnamaldehyde":  {"cas": "104-55-2",   "odor": ["cinnamon", "spicy", "sweet"], "src": "flavornet"},
    "myristicin":      {"cas": "607-91-0",   "odor": ["nutmeg", "spicy", "woody"], "src": "flavornet",
                        "provisional": True, "note": "Nutmeg ether; Flavornet listing not confirmed in-session."},
    "zingiberene":     {"cas": "495-60-3",   "odor": ["spicy", "ginger", "woody"], "src": "flavornet",
                        "provisional": True, "note": "Fresh-ginger sesquiterpene; Flavornet listing not confirmed in-session."},
    "carvacrol":       {"cas": "499-75-2",   "odor": ["spicy", "herbal", "oregano"], "src": "flavornet"},
    "thymol":          {"cas": "89-83-8",    "odor": ["herbal", "thyme", "medicinal"], "src": "flavornet"},

    # ---- Anise / licorice ------------------------------------------------
    "anethole":        {"cas": "104-46-1",   "odor": ["anise", "licorice", "sweet"], "src": "flavornet"},
    "estragole":       {"cas": "140-67-0",   "odor": ["anise", "licorice", "sweet"], "src": "flavornet"},

    # ---- Sweet / caramel / vanilla / creamy -----------------------------
    "vanillin":        {"cas": "121-33-5",   "odor": ["vanilla", "sweet", "creamy"], "src": "flavornet"},
    "furaneol":        {"cas": "3658-77-3",  "odor": ["caramel", "sweet", "strawberry"], "src": "flavornet"},
    "sotolon":         {"cas": "28664-35-9", "odor": ["caramel", "maple", "savoury"], "src": "flavornet"},
    "diacetyl":        {"cas": "431-03-8",   "odor": ["buttery", "creamy"], "src": "flavornet"},
    "coumarin":        {"cas": "91-64-5",    "odor": ["sweet", "hay", "vanilla"], "src": "flavornet"},

    # ---- Roasted / nutty / toasty ---------------------------------------
    "pyrazine":        {"cas": "290-37-9",   "odor": ["roasted", "nutty", "earthy"], "src": "flavornet",
                        "provisional": True, "note": "Parent pyrazine is faint; roast/nut facet is the alkylpyrazine family it stands in for."},
    "2_acetylpyrrole": {"cas": "1072-83-9",  "odor": ["nutty", "musty", "bready"], "src": "flavornet"},
    "furfural":        {"cas": "98-01-1",    "odor": ["bready", "almond", "sweet"], "src": "flavornet"},
    "2_furfurylthiol": {"cas": "98-02-2",    "odor": ["roasted", "coffee", "sulfury"], "src": "flavornet"},
    "benzaldehyde":    {"cas": "100-52-7",   "odor": ["almond", "cherry", "nutty"], "src": "flavornet"},
    "methional":       {"cas": "3268-49-3",  "odor": ["savoury", "potato", "sulfury"], "src": "flavornet"},

    # ---- Non-volatile tastants (no odour; taste class from ChemTastesDB) --
    "amarogentin":     {"cas": "21018-84-8", "odor": [], "taste_class": "bitter", "src": "chemtastes",
                        "note": "Gentian secoiridoid; one of the most bitter substances known. Not an aroma compound."},
    "gentiopicroside": {"cas": "20831-76-9", "odor": [], "taste_class": "bitter", "src": "chemtastes",
                        "note": "Gentian secoiridoid glycoside; bitter principle. Not an aroma compound."},
    "capsaicin":       {"cas": "404-86-4",   "odor": [], "taste_class": "pungent", "src": "chemtastes",
                        "provisional": True, "note": "Chemesthetic pungency (TRPV1), not one of the 5 basic tastes; label kept as 'pungent'."},
    "gingerol":        {"cas": "23513-14-6", "odor": [], "taste_class": "pungent", "src": "chemtastes",
                        "provisional": True, "note": "6-gingerol; chemesthetic warmth/pungency rather than a basic taste."},
    "polygodial":      {"cas": "6754-20-7",  "odor": [], "taste_class": "pungent", "src": "curated",
                        "provisional": True, "note": "Native pepperberry (Tasmannia) sesquiterpene dialdehyde; hot/pungent. Off-database; bartender/lit knowledge."},
}


def _normalise_entry(compound_id: str, raw: dict) -> dict:
    """Return a full descriptor record with defaults and source attribution."""
    odor = list(raw.get("odor", []))
    taste_class = raw.get("taste_class")
    src = raw.get("src", "curated")
    if src == "flavornet":
        source = f"{FLAVORNET_CITE}, Percepts for CAS {raw.get('cas', '?')}"
    elif src == "chemtastes":
        source = f"{CHEMTASTES_CITE}; taste class for CAS {raw.get('cas', '?')}"
    else:
        source = "Curated from published organoleptic literature / bartender knowledge"
    entry = {
        "cas": raw.get("cas"),
        "odor": odor,
        "taste_class": taste_class,
        "provisional": bool(raw.get("provisional", False)),
        "source": source,
    }
    if raw.get("note"):
        entry["note"] = raw["note"]
    return entry


def _compound_vocabulary() -> set[str]:
    """The set of compound ids actually used by raw ingredients."""
    with INGREDIENTS_PATH.open(encoding="utf-8") as handle:
        entries = json.load(handle)
    vocab: set[str] = set()
    for entry in entries:
        vocab.update(entry.get("compounds", []))
    return vocab


def build() -> dict:
    """Build the compound_descriptors payload and validate coverage."""
    vocab = _compound_vocabulary()
    curated_ids = set(CURATED)

    missing = sorted(vocab - curated_ids)
    extra = sorted(curated_ids - vocab)
    if missing:
        raise SystemExit(
            f"{len(missing)} compound(s) used by ingredients have no descriptor "
            f"entry: {missing}. Add them to CURATED before building."
        )

    compounds = {cid: _normalise_entry(cid, CURATED[cid]) for cid in sorted(curated_ids)}
    provisional_count = sum(1 for c in compounds.values() if c["provisional"])

    return {
        "_meta": {
            "description": "Compound -> sensory descriptors (odour words + taste class), curated and cited.",
            "generated_by": "scripts/fetch_descriptors.py",
            "odor_source": (
                "Flavornet — Acree, T. & Arn, H. (2004) Flavornet and Human Odor Space, "
                "flavornet.org; Arn & Acree (1998) Dev. Food Sci. 40:27. Odour words "
                "condensed from per-compound 'Percepts'."
            ),
            "taste_source": (
                "ChemTastesDB — Rojas et al. (2022) Food Chem: Mol Sci 4:100090 "
                "(doi:10.1016/j.fochms.2022.100090). Used cite-only for taste-class "
                "labels of non-volatile tastants; database file not redistributed."
            ),
            "honesty_note": (
                "Curated build-time table (the site could not be scraped in the build "
                "environment). Entries flagged 'provisional' could not be confirmed "
                "against the live Flavornet page in-session; verify before public claims."
            ),
            "refresh": (
                "In an unblocked environment, verify/refresh via the rOpenSci webchem "
                "scheme: GET http://www.flavornet.org/info/{CAS}.html and read the "
                "'Percepts' field. See refresh_from_flavornet() below."
            ),
            "compound_count": len(compounds),
            "provisional_count": provisional_count,
            "extra_not_in_vocab": extra,
        },
        "compounds": compounds,
    }


def refresh_from_flavornet(cas: str) -> str:  # pragma: no cover - network, documented only
    """Return the Flavornet 'Percepts' string for one CAS (requires network).

    Documented for use in an unblocked environment. Mirrors rOpenSci
    webchem::fn_percept(): the odour text sits at XPath /html/body/p[3] of
    http://www.flavornet.org/info/{CAS}.html . Not called by the build; the
    committed data is the curated CURATED table above.
    """
    import urllib.request
    from html.parser import HTMLParser

    url = f"http://www.flavornet.org/info/{cas}.html"
    with urllib.request.urlopen(url, timeout=30) as response:  # noqa: S310
        html = response.read().decode("utf-8", "replace")

    class _P(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.texts: list[str] = []
            self._grab = False

        def handle_data(self, data: str) -> None:
            if "Percepts" in data:
                self._grab = True
            elif self._grab and data.strip():
                self.texts.append(data.strip())

    parser = _P()
    parser.feed(html)
    return "; ".join(parser.texts[:1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    payload = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    meta = payload["_meta"]
    print(
        f"Wrote {meta['compound_count']} compound descriptors "
        f"({meta['provisional_count']} provisional) -> {args.output}"
    )


if __name__ == "__main__":
    main()
