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
}
VALID_CONFIDENCE = {"solid", "moderate", "sparse"}


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
    season: str | None = None  # reserved for a future feature; always None in V1


@dataclass
class Pantry:
    """The validated, in-memory view of all known ingredients and pairings."""

    ingredients: dict[str, Ingredient] = field(default_factory=dict)
    tradition: dict[frozenset[str], float] = field(default_factory=dict)

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
        )

    # Pass 3: the tradition table. Stored keyed by an unordered pair so a lookup
    # works regardless of argument order. Unknown ids here are tolerated (the
    # default tradition is 0 anyway), so this table never blocks a load.
    for row in tradition_entries:
        _validate_tradition_row(row)
        a, b = row["pair"]
        pantry.tradition[frozenset((a, b))] = float(row["tradition"])

    return pantry


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
