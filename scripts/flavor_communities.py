#!/usr/bin/env python3
"""Detect flavour-family communities in the ingredient co-occurrence graph.

Build-time diagnostic: groups ingredients that keep appearing together across
the corpus (a citrus-sour family, a creamy-coffee family, ...) so we can see
what flavour structures real cocktails organise around — and spot data
problems (a junk cluster usually means alias/coverage work is needed).

Nodes are ingredients with at least ``--min-count`` recipe appearances. Edges
are pairs with NPMI above ``--min-npmi``, weighted by ``npmi * log(1 + count)``
so that genuine affinity matters but one-off pairs don't dominate. The graph is
then sparsified to *mutual* top-k edges per node — without this, hub
ingredients (lemon, sugar) glue the whole corpus into one giant community.
Communities come from weighted label propagation run in sorted order with
alphabetical tie-breaks, so the output is deterministic.

Writes ``data/flavor_communities.json``; engine/server never read this file.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES_PATH = ROOT / "data" / "recipes_normalized.json"
NPMI_PATH = ROOT / "data" / "tradition_npmi.json"
OUTPUT_PATH = ROOT / "data" / "flavor_communities.json"


def _load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def build_graph(
    min_count: int, min_npmi: float, top_k: int
) -> tuple[dict[str, dict[str, float]], Counter[str]]:
    recipes = _load_json(RECIPES_PATH)
    frequencies: Counter[str] = Counter()
    for recipe in recipes:
        frequencies.update(recipe)

    nodes = {ingredient for ingredient, count in frequencies.items() if count >= min_count}
    dense: dict[str, dict[str, float]] = defaultdict(dict)
    for row in _load_json(NPMI_PATH):
        a, b = row["pair"]
        npmi = float(row["npmi"])
        if npmi <= min_npmi or a not in nodes or b not in nodes:
            continue
        weight = npmi * math.log1p(int(row["count"]))
        dense[a][b] = weight
        dense[b][a] = weight

    # Keep an edge only if each endpoint ranks the other among its top-k
    # strongest neighbours; this strips the hub-ingredient glue.
    strongest = {
        node: set(sorted(neighbours, key=lambda n: -neighbours[n])[:top_k])
        for node, neighbours in dense.items()
    }
    edges: dict[str, dict[str, float]] = defaultdict(dict)
    for node, neighbours in dense.items():
        for neighbour, weight in neighbours.items():
            if neighbour in strongest[node] and node in strongest[neighbour]:
                edges[node][neighbour] = weight
    return edges, frequencies


def propagate_labels(edges: dict[str, dict[str, float]], sweeps: int) -> dict[str, str]:
    """Weighted label propagation, deterministic via sorted iteration order."""
    labels = {node: node for node in edges}
    for _ in range(sweeps):
        changed = False
        for node in sorted(edges):
            tally: dict[str, float] = defaultdict(float)
            for neighbour, weight in edges[node].items():
                tally[labels[neighbour]] += weight
            if not tally:
                continue
            # Highest total weight wins; ties break alphabetically for determinism.
            best = min(tally, key=lambda label: (-tally[label], label))
            if best != labels[node]:
                labels[node] = best
                changed = True
        if not changed:
            break
    return labels


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect flavour-family communities.")
    parser.add_argument("--min-count", type=int, default=3,
                        help="Minimum recipe appearances for an ingredient node (default: 3).")
    parser.add_argument("--min-npmi", type=float, default=0.05,
                        help="Minimum NPMI for an edge to exist (default: 0.05).")
    parser.add_argument("--top-k", type=int, default=3,
                        help="Mutual top-k edges kept per node (default: 3).")
    parser.add_argument("--sweeps", type=int, default=20,
                        help="Maximum label-propagation sweeps (default: 20).")
    args = parser.parse_args()

    edges, frequencies = build_graph(args.min_count, args.min_npmi, args.top_k)
    labels = propagate_labels(edges, args.sweeps)

    members: dict[str, list[str]] = defaultdict(list)
    for node, label in labels.items():
        members[label].append(node)

    communities = []
    for group in members.values():
        # Most frequent member fronts the group; it names the family well enough.
        ordered = sorted(group, key=lambda node: (-frequencies[node], node))
        communities.append({"head": ordered[0], "size": len(ordered), "members": ordered})
    communities.sort(key=lambda item: (-item["size"], item["head"]))

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(communities, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    print(f"{len(edges)} nodes -> {len(communities)} communities -> {OUTPUT_PATH}")
    for community in communities:
        print(f"  [{community['size']:>2}] {', '.join(community['members'])}")


if __name__ == "__main__":
    main()
