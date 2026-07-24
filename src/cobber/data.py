"""Data layer for Cobber the Mixologist.

Loads the flat JSON files, validates them, and derives the compound profile of
every composite (spirit / liqueur / bitters) as the union of its botanicals'
compounds. Everything downstream — the engine and the MCP tools — reads the
world through the :class:`Pantry` object built here. There is no database and no
network access: this module only ever touches the bundled JSON files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# The data files live in <repo>/data, two parents up from this file
# (src/cobber/data.py -> src/cobber -> src -> <repo>).
DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# The role tags a single ingredient or composite may carry. Used by the balance
# heuristic in the engine, so keep this list and that logic in sync.
VALID_ROLES = {
    "spirit",
    "sour",
    "sweet",
    "bitter",
    "aromatic",
    "fruit",
    "herb",
    "dairy",
    "mixer",
    "seasoning",
}
VALID_CONFIDENCE = {"solid", "moderate", "sparse"}

# The taste axes (design notes §4): what aroma compounds can't capture.
# Values are 0..1 per axis; an entry's `taste` is optional — the engine falls
# back to a coarse role-derived prior when it is absent, so explicit taste
# data stays honest (curated where present, derived where not).
VALID_TASTE_AXES = {"sweet", "sour", "bitter", "salty", "umami", "fat", "funk"}


@dataclass(frozen=True)
class Ingredient:
    """One entry from the data files (either a raw ingredient or a composite).

    ``compounds`` holds the *effective* compound set: for raw ingredients it is
    taken verbatim from ``ingredients.json``; for composites it is derived as the
    union of the botanicals' compounds (see :func:`_derive_composite_compounds`).
    """

    id: str
    display_name: str
    type: str  # "raw" or "composite"
    role: str
    compounds: frozenset[str]
    descriptors: tuple[str, ...]
    is_native: bool
    notes: str
    source: str
    botanicals: tuple[str, ...] = ()  # empty for raw ingredients
    # Non-volatile tastant compound ids (the taste "why" layer): the molecules
    # that CAUSE this ingredient's taste axes (citric_acid -> sour, sucrose ->
    # sweet, quinine -> bitter). Kept separate from `compounds` (aroma) on
    # purpose — tastants must never enter the aroma-harmony Jaccard.
    tastants: tuple[str, ...] = ()
    season: str | None = None  # reserved for a future feature; always None in V1
    # Explicit taste-axis values (0..1 per axis in VALID_TASTE_AXES), stored as
    # a tuple of (axis, value) pairs to keep the dataclass safely immutable.
    # Empty means "not curated yet" — the engine derives a coarse prior from
    # the role instead. A deliberately neutral entry (egg white: texture, not
    # taste) declares an axis at 0.0, which is explicit and blocks fallback.
    taste: tuple[tuple[str, float], ...] = ()
    # True when the entry's notes flag it as unverified (PROVISIONAL /
    # TODO: verify). Surfaced by every tool so Cobber announces when his
    # grounding is a guess instead of relying on the host model to notice.
    provisional: bool = False


@dataclass
class Pantry:
    """The validated, in-memory view of all known ingredients and pairings."""

    ingredients: dict[str, Ingredient] = field(default_factory=dict)
    tradition: dict[frozenset[str], float] = field(default_factory=dict)
    # Frontier evidence: pairings seen in the craft/competition corpora, with
    # attribution. Deliberately separate from tradition — "a champion did it"
    # is validation for a novel pairing, not canon.
    frontier: dict[frozenset[str], dict] = field(default_factory=dict)
    # Proportion templates: structural shapes discovered from ~8k cocktail recipes
    # (sour, old fashioned, negroni-style, highball, ...). Build-time derived,
    # committed to data/proportion_templates.json. Naming is PROVISIONAL — Ari
    # reviews and renames before the engine treats these as canonical.
    templates: list[dict] = field(default_factory=list)
    # Technique rules: priority-ordered preparation rules derived from TheCocktailDB
    # + IBA instruction text mining. Each rule maps an ingredient signal (has_acid,
    # has_egg_white, ...) to a method (shake/stir/build), service style, glass, and
    # optional pre-steps (dry_shake, muddle). PROVISIONAL — Ari to review.
    technique_rules: list[dict] = field(default_factory=list)
    # Sensory-descriptor layer (build-time, cited). compound_descriptors maps each
    # aroma compound id -> {"odor": [...words], "taste_class": str|None,
    # "provisional": bool, "source": str, ...}. descriptor_word_to_family and
    # taste_overlay come from the approved flavour-family map. See
    # data/compound_descriptors.json and data/flavor_families.json.
    compound_descriptors: dict[str, dict] = field(default_factory=dict)
    odor_families: dict[str, list[str]] = field(default_factory=dict)
    descriptor_word_to_family: dict[str, str] = field(default_factory=dict)
    taste_overlay_classes: tuple[str, ...] = ()
    # Descriptor-family co-occurrence, mined from the recipe corpus with the same
    # NPMI/log-prevalence machinery as tradition. Keyed by an unordered family
    # pair -> {"count", "npmi", "harmony"}. See data/descriptor_harmony.json.
    descriptor_harmony: dict[frozenset[str], dict] = field(default_factory=dict)

    def get(self, ingredient_id: str) -> Ingredient | None:
        """Return the ingredient with this id, or ``None`` if it is unknown."""
        return self.ingredients.get(ingredient_id)

    def all_ids(self) -> list[str]:
        """Return every known ingredient id, sorted for stable output."""
        return sorted(self.ingredients)

    def natives(self) -> list[str]:
        """Return the ids of every Australian native ingredient, sorted."""
        return sorted(i.id for i in self.ingredients.values() if i.is_native)


def _load_json(filename: str) -> object:
    """Read and parse one JSON file from the data directory."""
    path = DATA_DIR / filename
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _derive_composite_compounds(
    botanicals: list[str], raw_compounds: dict[str, frozenset[str]]
) -> frozenset[str]:
    """Union the compounds of a composite's botanicals into one set.

    Composites do not carry their own compound list; their flavour profile is
    exactly the union of the compounds of the raw botanicals on their bill. A
    botanical with no known compounds simply contributes nothing.
    """
    derived: set[str] = set()
    for botanical_id in botanicals:
        derived |= raw_compounds.get(botanical_id, frozenset())
    return frozenset(derived)


def load_pantry() -> Pantry:
    """Load, validate, and return the full :class:`Pantry`.

    Raises ``ValueError`` on any structural problem in the data files: duplicate
    ids, an unknown ``role``, or a composite that references a botanical that is
    not a known raw ingredient. Failing loudly here keeps bad data from silently
    producing wrong chemistry downstream.
    """
    raw_entries = _load_json("ingredients.json")
    composite_entries = _load_json("composites.json")
    tradition_entries = _load_json("tradition.json")

    pantry = Pantry()

    # Pass 1: raw ingredients. We need their compounds before we can derive any
    # composite profile, so they are loaded first.
    raw_compounds: dict[str, frozenset[str]] = {}
    for entry in raw_entries:
        _validate_role(entry)
        ingredient_id = entry["id"]
        if ingredient_id in pantry.ingredients:
            raise ValueError(f"Duplicate ingredient id: {ingredient_id!r}")
        compounds = frozenset(entry["compounds"])
        raw_compounds[ingredient_id] = compounds
        pantry.ingredients[ingredient_id] = Ingredient(
            id=ingredient_id,
            display_name=entry["display_name"],
            type=entry["type"],
            role=entry["role"],
            compounds=compounds,
            descriptors=tuple(entry["descriptors"]),
            is_native=bool(entry.get("is_native", False)),
            notes=entry.get("notes", ""),
            source=entry.get("source", ""),
            season=entry.get("season"),
            taste=_validate_taste(entry),
            tastants=tuple(entry.get("tastants", [])),
            provisional=_is_provisional(entry),
        )

    # Pass 2: composites. Their compound profile is derived, not declared.
    for entry in composite_entries:
        _validate_role(entry)
        composite_id = entry["id"]
        if composite_id in pantry.ingredients:
            raise ValueError(f"Duplicate ingredient id: {composite_id!r}")
        botanicals = entry.get("botanicals", [])
        for botanical_id in botanicals:
            if botanical_id not in raw_compounds:
                raise ValueError(
                    f"Composite {composite_id!r} references unknown botanical "
                    f"{botanical_id!r}; add it to ingredients.json first."
                )
        pantry.ingredients[composite_id] = Ingredient(
            id=composite_id,
            display_name=entry["display_name"],
            type=entry["type"],
            role=entry["role"],
            compounds=_derive_composite_compounds(botanicals, raw_compounds),
            descriptors=tuple(entry["descriptors"]),
            is_native=bool(entry.get("is_native", False)),
            notes=entry.get("notes", ""),
            source=entry.get("source", ""),
            botanicals=tuple(botanicals),
            season=entry.get("season"),
            taste=_validate_taste(entry),
            tastants=tuple(entry.get("tastants", [])),
            provisional=_is_provisional(entry),
        )

    # Pass 3: the tradition table. Stored keyed by an unordered pair so a lookup
    # works regardless of argument order. Unknown ids here are tolerated (the
    # default tradition is 0 anyway), so this table never blocks a load.
    for row in tradition_entries:
        _validate_tradition_row(row)
        a, b = row["pair"]
        pantry.tradition[frozenset((a, b))] = float(row["tradition"])

    # Pass 4: frontier evidence, if the file exists. Same tolerance as
    # tradition: unknown ids never block a load.
    frontier_path = DATA_DIR / "frontier_evidence.json"
    if frontier_path.exists():
        with frontier_path.open(encoding="utf-8") as handle:
            for row in json.load(handle):
                pair = row.get("pair")
                if isinstance(pair, list) and len(pair) == 2:
                    pantry.frontier[frozenset(pair)] = {
                        "count": int(row.get("count", 0)),
                        "examples": list(row.get("examples", [])),
                    }

    # Pass 5: proportion templates, if the file exists. PROVISIONAL names until
    # Ari's bartender review; the engine reads the centroids and recipe counts.
    templates_path = DATA_DIR / "proportion_templates.json"
    if templates_path.exists():
        with templates_path.open(encoding="utf-8") as handle:
            templates_data = json.load(handle)
        pantry.templates = templates_data.get("templates", [])

    # Pass 6: technique rules, if the file exists. Mined from TheCocktailDB + IBA
    # instruction text; priority-ordered rules for shake/stir/build/blend dispatch.
    technique_path = DATA_DIR / "technique_associations.json"
    if technique_path.exists():
        with technique_path.open(encoding="utf-8") as handle:
            technique_data = json.load(handle)
        pantry.technique_rules = technique_data.get("rules", [])

    # Pass 7: compound descriptors + flavour families (the sensory layer). Loaded
    # together and cross-checked: every descriptor word a compound carries must
    # belong to a known family, or the wheel would silently drop it.
    _load_descriptor_layer(pantry)

    # Pass 8: descriptor-family co-occurrence, if the build script has run.
    harmony_path = DATA_DIR / "descriptor_harmony.json"
    if harmony_path.exists():
        with harmony_path.open(encoding="utf-8") as handle:
            for row in json.load(handle).get("pairs", []):
                pair = row.get("pair")
                if isinstance(pair, list) and len(pair) == 2:
                    pantry.descriptor_harmony[frozenset(pair)] = {
                        "count": int(row.get("count", 0)),
                        "npmi": float(row.get("npmi", 0.0)),
                        "harmony": float(row.get("harmony", 0.0)),
                    }

    return pantry


def _load_descriptor_layer(pantry: Pantry) -> None:
    """Load compound_descriptors.json + flavor_families.json into the pantry.

    Both are optional (older data snapshots predate the sensory layer), but if
    the families file is present, every descriptor word used by a compound must
    map to a family — an unmapped word is a data error, not something to drop
    silently, so we raise. Descriptor entries for compounds no ingredient uses
    are tolerated.
    """
    families_path = DATA_DIR / "flavor_families.json"
    descriptors_path = DATA_DIR / "compound_descriptors.json"

    if families_path.exists():
        with families_path.open(encoding="utf-8") as handle:
            families_data = json.load(handle)
        odor_families = families_data.get("odor_families", {})
        word_to_family: dict[str, str] = {}
        for family, words in odor_families.items():
            for word in words:
                if word in word_to_family and word_to_family[word] != family:
                    raise ValueError(
                        f"Descriptor word {word!r} is assigned to two families "
                        f"({word_to_family[word]!r} and {family!r}); each word "
                        "must map to exactly one family."
                    )
                word_to_family[word] = family
        pantry.odor_families = odor_families
        pantry.descriptor_word_to_family = word_to_family
        pantry.taste_overlay_classes = tuple(
            families_data.get("taste_overlay", {}).get("classes", [])
        )

    if descriptors_path.exists():
        with descriptors_path.open(encoding="utf-8") as handle:
            descriptors_data = json.load(handle)
        pantry.compound_descriptors = descriptors_data.get("compounds", {})

        # Cross-check: every odour word a compound carries must have a family.
        if pantry.descriptor_word_to_family:
            unmapped: set[str] = set()
            for record in pantry.compound_descriptors.values():
                for word in record.get("odor", []):
                    if word not in pantry.descriptor_word_to_family:
                        unmapped.add(word)
            if unmapped:
                raise ValueError(
                    f"{len(unmapped)} descriptor word(s) used by compounds are not "
                    f"in any flavour family: {sorted(unmapped)}. Add them to "
                    "data/flavor_families.json."
                )

        # Cross-check the taste "why" layer: every tastant an ingredient names
        # must have a descriptor entry with a taste_class (never a dangling ref).
        dangling: set[str] = set()
        for ingredient in pantry.ingredients.values():
            for tastant in ingredient.tastants:
                record = pantry.compound_descriptors.get(tastant)
                if record is None or not record.get("taste_class"):
                    dangling.add(tastant)
        if dangling:
            raise ValueError(
                f"{len(dangling)} tastant(s) referenced by ingredients lack a "
                f"descriptor entry with a taste_class: {sorted(dangling)}. Add them "
                "to compound_descriptors.json (via fetch_descriptors.py)."
            )


def _is_provisional(entry: dict) -> bool:
    notes = str(entry.get("notes", "")).lower()
    return "provisional" in notes or "todo: verify" in notes


def _validate_taste(entry: dict) -> tuple[tuple[str, float], ...]:
    """Validate an entry's optional ``taste`` object and return it as pairs.

    Raises ``ValueError`` on an unknown axis or an out-of-range value; returns
    an empty tuple when the field is absent (engine falls back to a role prior).
    """
    taste = entry.get("taste")
    if taste is None:
        return ()
    if not isinstance(taste, dict):
        raise ValueError(f"Ingredient {entry.get('id')!r}: 'taste' must be an object.")
    pairs: list[tuple[str, float]] = []
    for axis, value in sorted(taste.items()):
        if axis not in VALID_TASTE_AXES:
            raise ValueError(
                f"Ingredient {entry.get('id')!r} has unknown taste axis {axis!r}; "
                f"valid axes are {sorted(VALID_TASTE_AXES)}."
            )
        if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
            raise ValueError(
                f"Ingredient {entry.get('id')!r}: taste axis {axis!r} must be a "
                f"number in [0.0, 1.0], got {value!r}."
            )
        pairs.append((axis, float(value)))
    return tuple(pairs)


def _validate_role(entry: dict) -> None:
    """Raise ``ValueError`` if an entry carries a role we do not recognise."""
    role = entry.get("role")
    if role not in VALID_ROLES:
        raise ValueError(
            f"Ingredient {entry.get('id')!r} has invalid role {role!r}; "
            f"valid roles are {sorted(VALID_ROLES)}."
        )


def _validate_tradition_row(row: dict) -> None:
    """Raise ``ValueError`` if one tradition row is structurally invalid."""
    pair = row.get("pair")
    if not isinstance(pair, list) or len(pair) != 2:
        raise ValueError("Each tradition row must include pair: [a, b].")

    a, b = pair
    if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
        raise ValueError("Tradition pair ids must be non-empty strings.")
    if a == b:
        raise ValueError("Tradition pair ids must contain two distinct ingredients.")

    try:
        tradition_value = float(row["tradition"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Each tradition row must include numeric 'tradition'.") from error
    if not 0.0 <= tradition_value <= 1.0:
        raise ValueError("Tradition score must be in [0.0, 1.0].")

    if "count" in row:
        count = row["count"]
        if not isinstance(count, int) or count < 1:
            raise ValueError("Tradition row 'count' must be an integer >= 1.")

    if "confidence" in row:
        confidence = row["confidence"]
        if confidence not in VALID_CONFIDENCE:
            raise ValueError(
                f"Tradition row confidence {confidence!r} is invalid; "
                f"must be one of {sorted(VALID_CONFIDENCE)}."
            )
