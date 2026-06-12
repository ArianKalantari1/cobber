#!/usr/bin/env python3
"""Render the ingredient co-occurrence graph as an interactive HTML page.

Build-time diagnostic, like flavor_communities.py: reads the committed data
files and writes ``data/flavor_graph.html`` — a self-contained page (D3 from
CDN; needs internet to view) where ingredients are dots sized by how many
recipes they appear in, coloured by flavour family, and connected by lines
weighted by tradition. Drag, zoom, hover to highlight a node's neighbours,
and use the slider to hide weak edges.

The engine and server never read this file; it exists for human eyes.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECIPES_PATH = ROOT / "data" / "recipes_normalized.json"
TRADITION_PATH = ROOT / "data" / "tradition.json"
COMMUNITIES_PATH = ROOT / "data" / "flavor_communities.json"
OUTPUT_PATH = ROOT / "data" / "flavor_graph.html"

PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cobber — the flavour graph</title>
<script src="https://cdn.jsdelivr.net/npm/d3@7"></script>
<style>
  body { margin: 0; background: #14110f; color: #e8e0d4; font: 14px/1.4 -apple-system, "Segoe UI", sans-serif; }
  #hud { position: fixed; top: 12px; left: 16px; z-index: 2; max-width: 320px; }
  #hud h1 { font-size: 18px; margin: 0 0 2px; }
  #hud p { margin: 2px 0; color: #b8ab97; font-size: 12px; }
  #legend span { display: inline-block; margin: 2px 8px 2px 0; font-size: 12px; white-space: nowrap; }
  #legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 4px; }
  #controls { position: fixed; bottom: 14px; left: 16px; z-index: 2; font-size: 12px; color: #b8ab97; }
  #tip { position: fixed; pointer-events: none; background: #241f1a; border: 1px solid #4a4036;
         padding: 6px 9px; border-radius: 6px; font-size: 12px; display: none; z-index: 3; }
  svg { width: 100vw; height: 100vh; }
  text.label { fill: #e8e0d4; pointer-events: none; font-size: 11px; paint-order: stroke; stroke: #14110f; stroke-width: 3px; }
</style>
</head>
<body>
<div id="hud">
  <h1>Cobber — the flavour graph</h1>
  <p>__N_NODES__ ingredients, __N_EDGES__ traditional pairings from __N_RECIPES__ recipes.</p>
  <p>Dot size = how many recipes use it. Line weight = how classic the pairing is. Colour = flavour family.</p>
  <div id="legend"></div>
</div>
<div id="controls">
  Hide pairings weaker than <input type="range" id="cut" min="0" max="0.9" step="0.05" value="0.3">
  <span id="cutval">0.30</span>
</div>
<div id="tip"></div>
<svg></svg>
<script>
const data = __GRAPH_JSON__;

const color = d3.scaleOrdinal()
  .domain(data.communities.map(c => c.head))
  .range(["#e4b363","#7fb069","#d05f5f","#6fa8dc","#b58ed2","#5fc9c1","#e98ab5",
          "#c9c45f","#8d9c6b","#de9151","#9aa9e0","#74c69d","#c97b84","#bfa46f",
          "#7fc5dc","#d2a0e8","#a3b562","#e0a899","#86b8a2","#cfae5e","#9d8ec9","#dd8866"]);

const legend = d3.select("#legend");
data.communities.filter(c => c.size >= 3).forEach(c => {
  legend.append("span").html(`<i style="background:${color(c.head)}"></i>${c.head} family (${c.size})`);
});

const svg = d3.select("svg"), W = innerWidth, H = innerHeight;
const g = svg.append("g");
svg.call(d3.zoom().scaleExtent([0.25, 5]).on("zoom", e => g.attr("transform", e.transform)));

const sim = d3.forceSimulation(data.nodes)
  .force("link", d3.forceLink(data.links).id(d => d.id)
      .distance(d => 40 + 160 * (1 - d.tradition)).strength(d => 0.2 + 0.8 * d.tradition))
  .force("charge", d3.forceManyBody().strength(-180))
  .force("center", d3.forceCenter(W / 2, H / 2))
  .force("collide", d3.forceCollide().radius(d => r(d) + 4));

function r(d) { return 4 + Math.sqrt(d.count) * 2.2; }

const link = g.append("g").selectAll("line").data(data.links).join("line")
  .attr("stroke", "#8a7a64").attr("stroke-opacity", d => 0.15 + 0.5 * d.tradition)
  .attr("stroke-width", d => 0.5 + 3.5 * d.tradition);

const node = g.append("g").selectAll("circle").data(data.nodes).join("circle")
  .attr("r", r).attr("fill", d => color(d.community)).attr("stroke", "#14110f").attr("stroke-width", 1.2)
  .call(d3.drag()
    .on("start", (e, d) => { if (!e.active) sim.alphaTarget(0.3).restart(); d.fx = d.x; d.fy = d.y; })
    .on("drag", (e, d) => { d.fx = e.x; d.fy = e.y; })
    .on("end", (e, d) => { if (!e.active) sim.alphaTarget(0); d.fx = d.fy = null; }));

const label = g.append("g").selectAll("text").data(data.nodes.filter(d => d.count >= 8)).join("text")
  .attr("class", "label").attr("text-anchor", "middle").text(d => d.id);

const tip = d3.select("#tip");
node.on("mouseover", (e, d) => {
    tip.style("display", "block").html(
      `<b>${d.id}</b><br>${d.count} recipes · ${d.community} family<br>` +
      `top partners: ${d.top.join(", ")}`);
    const nb = new Set(data.links.filter(l => l.source.id === d.id || l.target.id === d.id)
                                 .flatMap(l => [l.source.id, l.target.id]));
    node.attr("opacity", n => nb.has(n.id) || n.id === d.id ? 1 : 0.12);
    link.attr("stroke", l => l.source.id === d.id || l.target.id === d.id ? "#e4b363" : "#8a7a64")
        .attr("stroke-opacity", l => l.source.id === d.id || l.target.id === d.id ? 0.9 : 0.04);
    label.attr("opacity", n => nb.has(n.id) || n.id === d.id ? 1 : 0.15);
  })
  .on("mousemove", e => tip.style("left", (e.clientX + 14) + "px").style("top", (e.clientY + 8) + "px"))
  .on("mouseout", () => { tip.style("display", "none");
    node.attr("opacity", 1); label.attr("opacity", 1); applyCut(+d3.select("#cut").property("value")); });

function applyCut(cut) {
  link.attr("display", d => d.tradition >= cut ? null : "none")
      .attr("stroke", "#8a7a64").attr("stroke-opacity", d => 0.15 + 0.5 * d.tradition);
  d3.select("#cutval").text(cut.toFixed(2));
}
d3.select("#cut").on("input", function () { applyCut(+this.value); });
applyCut(0.3);

sim.on("tick", () => {
  link.attr("x1", d => d.source.x).attr("y1", d => d.source.y)
      .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
  node.attr("cx", d => d.x).attr("cy", d => d.y);
  label.attr("x", d => d.x).attr("y", d => d.y - r(d) - 4);
});
</script>
</body>
</html>
"""


def build_graph_payload(min_count: int, min_pair_count: int) -> tuple[dict, int]:
    recipes = json.loads(RECIPES_PATH.read_text())
    frequencies: Counter[str] = Counter()
    for recipe in recipes:
        frequencies.update(recipe)

    communities = json.loads(COMMUNITIES_PATH.read_text())
    community_of = {m: c["head"] for c in communities for m in c["members"]}

    nodes = {i for i, n in frequencies.items() if n >= min_count and i in community_of}
    rows = [
        r for r in json.loads(TRADITION_PATH.read_text())
        if r["count"] >= min_pair_count and r["pair"][0] in nodes and r["pair"][1] in nodes
    ]

    partners: dict[str, list[tuple[float, str]]] = {}
    for row in rows:
        a, b = row["pair"]
        partners.setdefault(a, []).append((row["tradition"], b))
        partners.setdefault(b, []).append((row["tradition"], a))

    payload = {
        "nodes": [
            {
                "id": i,
                "count": frequencies[i],
                "community": community_of[i],
                "top": [p for _, p in sorted(partners.get(i, []), reverse=True)[:4]],
            }
            for i in sorted(nodes)
        ],
        "links": [
            {"source": r["pair"][0], "target": r["pair"][1],
             "tradition": r["tradition"], "count": r["count"]}
            for r in rows
        ],
        "communities": communities,
    }
    return payload, len(recipes)


def _spring_layout(payload: dict, iterations: int = 800) -> dict[str, tuple[float, float]]:
    """Deterministic Fruchterman-Reingold layout, stdlib only.

    Edges pull proportionally to tradition; all nodes repel; a weak gravity
    keeps stragglers on the canvas. Attraction is degree-normalised — this
    graph is dense (every node averages ~18 edges) and without normalisation
    the hubs crush the whole layout into a blob. Seeded so the same data
    always produces the same picture; coordinates are rescaled to fill the
    frame at the end.
    """
    import math
    import random

    rng = random.Random(7)
    ids = [n["id"] for n in payload["nodes"]]
    pos = {i: (rng.uniform(-1, 1), rng.uniform(-1, 1)) for i in ids}
    edges = [(l["source"], l["target"], l["tradition"]) for l in payload["links"]]
    degree: dict[str, int] = {i: 1 for i in ids}
    for a, b, _ in edges:
        degree[a] += 1
        degree[b] += 1
    k = 2.0 / math.sqrt(len(ids))

    for step in range(iterations):
        temp = 0.35 * (1 - step / iterations) ** 1.5 + 0.002
        disp = {i: [0.0, 0.0] for i in ids}
        for idx, a in enumerate(ids):
            ax, ay = pos[a]
            for b in ids[idx + 1 :]:
                dx, dy = ax - pos[b][0], ay - pos[b][1]
                dist2 = dx * dx + dy * dy + 1e-6
                f = k * k / dist2
                disp[a][0] += dx * f; disp[a][1] += dy * f
                disp[b][0] -= dx * f; disp[b][1] -= dy * f
        for a, b, w in edges:
            dx, dy = pos[a][0] - pos[b][0], pos[a][1] - pos[b][1]
            dist = math.sqrt(dx * dx + dy * dy) + 1e-6
            f = (dist * dist / k) * (0.25 + 0.75 * w) / math.sqrt(degree[a] * degree[b])
            fx, fy = dx / dist * f, dy / dist * f
            disp[a][0] -= fx; disp[a][1] -= fy
            disp[b][0] += fx; disp[b][1] += fy
        for i in ids:
            dx, dy = disp[i]
            # weak gravity toward the centre so loners stay in frame
            dx -= pos[i][0] * 0.02
            dy -= pos[i][1] * 0.02
            d = math.sqrt(dx * dx + dy * dy) + 1e-6
            step_len = min(d, temp)
            pos[i] = (pos[i][0] + dx / d * step_len, pos[i][1] + dy / d * step_len)

    xs = sorted(p[0] for p in pos.values())
    ys = sorted(p[1] for p in pos.values())
    lo_x, hi_x = xs[0], xs[-1]
    lo_y, hi_y = ys[0], ys[-1]
    span_x = (hi_x - lo_x) or 1.0
    span_y = (hi_y - lo_y) or 1.0
    return {
        i: ((x - lo_x) / span_x * 2 - 1, (y - lo_y) / span_y * 2 - 1)
        for i, (x, y) in pos.items()
    }


PALETTE = ["#e4b363", "#7fb069", "#d05f5f", "#6fa8dc", "#b58ed2", "#5fc9c1", "#e98ab5",
           "#c9c45f", "#8d9c6b", "#de9151", "#9aa9e0", "#74c69d", "#c97b84", "#bfa46f",
           "#7fc5dc", "#d2a0e8", "#a3b562", "#e0a899", "#86b8a2", "#cfae5e", "#9d8ec9", "#dd8866"]


def render_static(payload: dict, n_recipes: int, output: Path) -> None:
    """Write a static PNG of the graph (needs matplotlib; build-time only)."""
    import math

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Nodes with no edge at this threshold would drift to the frame edges and
    # squash the real structure; leave them to the interactive view.
    connected = {l["source"] for l in payload["links"]} | {l["target"] for l in payload["links"]}
    payload = {
        **payload,
        "nodes": [n for n in payload["nodes"] if n["id"] in connected],
    }
    pos = _spring_layout(payload)
    head_color = {c["head"]: PALETTE[i % len(PALETTE)] for i, c in enumerate(payload["communities"])}

    fig, ax = plt.subplots(figsize=(16, 12), dpi=150)
    fig.patch.set_facecolor("#14110f"); ax.set_facecolor("#14110f"); ax.axis("off")

    for l in payload["links"]:
        (x1, y1), (x2, y2) = pos[l["source"]], pos[l["target"]]
        ax.plot([x1, x2], [y1, y2], color="#8a7a64",
                alpha=0.08 + 0.55 * l["tradition"], lw=0.4 + 2.6 * l["tradition"], zorder=1)
    for n in payload["nodes"]:
        x, y = pos[n["id"]]
        size = 28 + n["count"] * 5.5
        ax.scatter([x], [y], s=size, color=head_color[n["community"]],
                   edgecolors="#14110f", linewidths=0.8, zorder=2)
        if n["count"] >= 8:
            ax.annotate(n["id"], (x, y), textcoords="offset points",
                        xytext=(0, 5 + math.sqrt(size) / 2), ha="center",
                        color="#e8e0d4", fontsize=7.5, zorder=3,
                        path_effects=None)
    ax.set_title(
        f"Cobber — the flavour graph   ·   {len(payload['nodes'])} ingredients, "
        f"{len(payload['links'])} pairings, {n_recipes} recipes",
        color="#e8e0d4", fontsize=13, pad=14)
    fig.tight_layout()
    fig.savefig(output, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print(f"static image -> {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the flavour graph to interactive HTML.")
    parser.add_argument("--min-count", type=int, default=3,
                        help="Minimum recipe appearances for an ingredient (default: 3).")
    parser.add_argument("--min-pair-count", type=int, default=2,
                        help="Minimum recipe support for an edge (default: 2).")
    parser.add_argument("--png", type=Path, default=None,
                        help="Also write a static PNG snapshot here (requires matplotlib).")
    args = parser.parse_args()

    payload, n_recipes = build_graph_payload(args.min_count, args.min_pair_count)
    html = (
        PAGE_TEMPLATE
        .replace("__GRAPH_JSON__", json.dumps(payload))
        .replace("__N_NODES__", str(len(payload["nodes"])))
        .replace("__N_EDGES__", str(len(payload["links"])))
        .replace("__N_RECIPES__", str(n_recipes))
    )
    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"{len(payload['nodes'])} nodes, {len(payload['links'])} edges -> {OUTPUT_PATH}")

    if args.png is not None:
        render_static(payload, n_recipes, args.png)


if __name__ == "__main__":
    main()
