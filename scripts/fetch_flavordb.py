#!/usr/bin/env python3
"""Fetch FlavorDB2 entity records for ingredient-profile enrichment.

FlavorDB2 (Bagler lab, IIIT-Delhi) maps food entities -> flavour molecules, and
each molecule carries a ``flavor_profile`` keyword set. That's two things Cobber
wants: MORE aroma compounds per ingredient, and more descriptor words per
compound. This script pulls the per-entity JSON the maintainers expose (there is
no bulk API) and writes a raw dump for the offline, human-approved enrichment
step (``enrich_from_flavordb.py``).

LICENSE / USE (recorded in the dump's provenance):
  FlavorDB2 is offered for **non-commercial** use with attribution — reported as
  CC BY-NC-SA 3.0 (NC + ShareAlike). Cobber is a non-commercial project and the
  maintainer's non-commercial terms are accepted, so this fetch + a derived,
  attributed enrichment are within scope. Any redistribution stays under the same
  ShareAlike terms and cites the papers below. Commercial use would need written
  permission (bagler+FlavorDB@iiitd.ac.in).

  Cite:
    * Goel, M., Grover, N., Batra, D., Garg, N., Tuwani, R., Sethupathy, A. &
      Bagler, G. (2024). "FlavorDB2: An updated database of flavor molecules."
      J. Food Sci. 89:7076-7082. doi:10.1111/1750-3841.17298
    * Garg, N. et al. (2018). "FlavorDB: a database of flavor molecules."
      Nucleic Acids Research 46(D1):D1210-D1216. doi:10.1093/nar/gkx957

NETWORK NOTE:
  Some environments (including Cobber's CI/agent sandbox) block outbound access to
  cosylab.iiitd.edu.in. This script fails fast and loudly in that case and writes
  NOTHING, rather than committing a partial/empty dump. Run it from an unblocked
  machine. Be polite: it rate-limits and the site 403s bare automated agents, so a
  browser-like User-Agent is sent.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "data" / "raw" / "flavordb_entities.json"

BASE = "https://cosylab.iiitd.edu.in/flavordb"
ENTITY_JSON = BASE + "/entities_json?id={id}"
USER_AGENT = "Mozilla/5.0 (compatible; CobberResearch/1.0; non-commercial food-science use)"

LICENSE = "CC BY-NC-SA 3.0 (non-commercial + ShareAlike; reported, verify on flavordb2/faq)"
CITATION = (
    "Goel et al. 2024, J Food Sci 89:7076 (doi:10.1111/1750-3841.17298); "
    "Garg et al. 2018, NAR 46:D1210 (doi:10.1093/nar/gkx957)"
)


def parse_entity(payload: dict) -> dict | None:
    """Reduce one FlavorDB entity JSON to the fields enrichment needs.

    Tolerant of the two field spellings the endpoint has used across versions.
    Returns ``None`` for an empty/So-Such entity so callers can skip it.
    """
    entity_id = payload.get("entity_id", payload.get("id"))
    alias = payload.get("entity_alias_readable") or payload.get("alias") or payload.get("natural_source_name")
    category = payload.get("category_readable") or payload.get("category")
    molecules_in = payload.get("molecules", []) or []
    if not alias and not molecules_in:
        return None

    molecules = []
    for mol in molecules_in:
        common = mol.get("common_name") or mol.get("common name")
        if not common:
            continue
        profile = mol.get("flavor_profile") or mol.get("flavor profile") or ""
        # flavor_profile is an @-joined string in the raw JSON; normalise to a list.
        if isinstance(profile, str):
            words = [w.strip().lower() for w in profile.replace("@", ",").split(",") if w.strip()]
        else:
            words = [str(w).strip().lower() for w in profile if str(w).strip()]
        molecules.append(
            {
                "common_name": str(common).strip(),
                "pubchem_id": mol.get("pubchem_id") or mol.get("pubchem id"),
                "flavor_profile": sorted(set(words)),
            }
        )

    return {
        "entity_id": entity_id,
        "alias": (alias or "").strip(),
        "category": (category or "").strip(),
        "molecules": molecules,
    }


def _fetch_json(url: str, timeout: int) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8", "replace"))


def fetch(id_start: int, id_end: int, delay: float, timeout: int) -> list[dict]:
    """Fetch entities id_start..id_end inclusive. Fails fast if the host is blocked."""
    entities: list[dict] = []
    for entity_id in range(id_start, id_end + 1):
        url = ENTITY_JSON.format(id=entity_id)
        try:
            payload = _fetch_json(url, timeout)
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                continue  # gap in the id space; keep going
            if entity_id == id_start:
                raise SystemExit(
                    f"FlavorDB returned HTTP {exc.code} on the first request "
                    f"({url}). Likely blocked here — run from an unblocked network. "
                    "Nothing written."
                ) from exc
            print(f"  skip id={entity_id}: HTTP {exc.code}")
            continue
        except (urllib.error.URLError, OSError) as exc:
            if entity_id == id_start:
                raise SystemExit(
                    f"Cannot reach FlavorDB ({url}): {exc}. This environment blocks "
                    "cosylab.iiitd.edu.in — run from an unblocked network. Nothing written."
                ) from exc
            print(f"  skip id={entity_id}: {exc}")
            continue

        parsed = parse_entity(payload)
        if parsed and parsed["molecules"]:
            entities.append(parsed)
            print(f"  id={entity_id} {parsed['alias']!r}: {len(parsed['molecules'])} molecules")
        time.sleep(delay)
    return entities


def _self_test() -> None:
    """Parse a synthetic record so the reduction logic is exercised offline."""
    sample = {
        "entity_id": 1,
        "entity_alias_readable": "Lemon",
        "category_readable": "fruit",
        "molecules": [
            {"common_name": "Limonene", "pubchem_id": 22311, "flavor_profile": "citrus@lemon@fresh"},
            {"common_name": "Citral", "flavor_profile": ["lemon"]},
            {"common_name": ""},  # dropped
        ],
    }
    parsed = parse_entity(sample)
    assert parsed and parsed["alias"] == "Lemon"
    assert len(parsed["molecules"]) == 2
    assert parsed["molecules"][0]["flavor_profile"] == ["citrus", "fresh", "lemon"]
    print("self-test OK")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1, help="first entity id")
    parser.add_argument("--end", type=int, default=1000, help="last entity id (FlavorDB2 ~936 entities)")
    parser.add_argument("--delay", type=float, default=0.5, help="seconds between requests (be polite)")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--self-test", action="store_true", help="run the offline parse self-test and exit")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    entities = fetch(args.start, args.end, args.delay, args.timeout)
    if not entities:
        raise SystemExit("No entities fetched; nothing written.")

    payload = {
        "_meta": {
            "source": "FlavorDB2, cosylab.iiitd.edu.in/flavordb2",
            "license": LICENSE,
            "citation": CITATION,
            "use": "non-commercial (accepted); attribution + ShareAlike on redistribution.",
            "fetched": date.today().isoformat(),
            "id_range": [args.start, args.end],
            "entity_count": len(entities),
        },
        "entities": entities,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"Wrote {len(entities)} entities -> {args.output}")


if __name__ == "__main__":
    main()
