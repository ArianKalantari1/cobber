#!/usr/bin/env python3
"""Render the sensory-descriptor layer as a self-contained HTML page.

Reads the committed data files, computes every ingredient's flavour wheel and
harmonious notes through the engine, and writes ``data/flavor_wheel.html`` — a
single file with ALL data and code embedded (no CDN, no server, no network). Open
it in a browser and pick an ingredient: you get its aroma broken into the ten
flavour families as a donut, a taste overlay for bitter/pungent tastants, and the
complementary "harmonious notes" mined from Cobber's own corpus. Every descriptor
traces back to a cited compound; provisional data is flagged on the page.

The engine and server never read this file; it exists for human eyes, like
flavor_graph.html and flavor_communities.py.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cobber import engine  # noqa: E402  (after sys.path shim, on purpose)

OUTPUT_PATH = ROOT / "data" / "flavor_wheel.html"

# Fixed, reasonably distinct family colours. Kept in the page too (legend).
FAMILY_COLORS = {
    "citrus":         "#f2c14e",
    "floral":         "#e08bbf",
    "fruity":         "#e5573f",
    "green_herbal":   "#7bb661",
    "woody_resinous": "#9c6b3f",
    "spice":          "#d1732f",
    "mint_cooling":   "#57c4ad",
    "sweet_creamy":   "#e8d5a3",
    "roasted_nutty":  "#7a5230",
    "savoury":        "#8a8f5c",
}
TASTE_COLORS = {"bitter": "#6b4e9e", "pungent": "#c0392b"}


def build_payload() -> dict:
    """Precompute wheel + harmonious notes for every known ingredient."""
    pantry = engine.PANTRY
    ingredients: dict[str, dict] = {}
    for iid in pantry.all_ids():
        wheel = engine.flavor_wheel(iid)
        notes = engine.harmonious_notes(iid)
        prov = engine.taste_provenance(iid)
        ingredient = pantry.get(iid)
        ingredients[iid] = {
            "id": iid,
            "display_name": wheel.get("display_name", iid),
            "role": ingredient.role if ingredient else None,
            "is_native": bool(ingredient.is_native) if ingredient else False,
            "coverage": wheel.get("coverage"),
            "dominant": wheel.get("dominant"),
            "provisional": wheel.get("provisional", False),
            "provisional_compounds": wheel.get("provisional_compounds", []),
            "n_compounds": wheel.get("n_compounds", 0),
            "note": wheel.get("note"),
            "families": wheel.get("families", []),
            "taste_overlay": wheel.get("taste_overlay", []),
            "harmonious": notes.get("notes", []),
            "taste_axes": prov.get("taste_axes", {}),
            "taste_provenance": prov.get("provenance", {}),
            "taste_gaps": prov.get("gaps", []),
        }

    # Compound -> descriptor sources, so the page can show a citation on hover.
    compound_sources = {
        cid: {
            "odor": rec.get("odor", []),
            "taste_class": rec.get("taste_class"),
            "source": rec.get("source", ""),
            "provisional": rec.get("provisional", False),
        }
        for cid, rec in pantry.compound_descriptors.items()
    }

    return {
        "ingredients": ingredients,
        "family_colors": FAMILY_COLORS,
        "taste_colors": TASTE_COLORS,
        "family_order": list(FAMILY_COLORS),
        "compounds": compound_sources,
        "meta": {
            "odor_source": "Flavornet (Acree & Arn 2004, flavornet.org)",
            "taste_source": "ChemTastesDB (Rojas et al. 2022, doi:10.1016/j.fochms.2022.100090)",
            "harmony_source": "Cobber's own recipe corpus (NPMI over flavour families)",
        },
    }


PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cobber — flavour wheels</title>
<style>
  :root { --bg:#14110f; --panel:#241f1a; --line:#4a4036; --ink:#e8e0d4; --muted:#b8ab97; }
  * { box-sizing: border-box; }
  body { margin:0; background:var(--bg); color:var(--ink);
         font:15px/1.5 -apple-system,"Segoe UI",Roboto,sans-serif; }
  header { padding:18px 22px 8px; }
  h1 { font-size:22px; margin:0 0 2px; }
  header p { margin:2px 0; color:var(--muted); font-size:13px; }
  .wrap { display:flex; flex-wrap:wrap; gap:22px; padding:12px 22px 40px; align-items:flex-start; }
  .controls { display:flex; gap:10px; align-items:center; padding:0 22px 4px; flex-wrap:wrap; }
  select, input { background:var(--panel); color:var(--ink); border:1px solid var(--line);
                  border-radius:7px; padding:8px 10px; font-size:14px; }
  .card { background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:16px 18px; }
  #wheelCard { width:420px; max-width:100%; text-align:center; }
  #sideCard { flex:1; min-width:280px; }
  svg { max-width:100%; height:auto; }
  .dom { font-size:14px; color:var(--muted); margin-top:6px; }
  .chips { display:flex; flex-wrap:wrap; gap:6px; margin:6px 0 2px; }
  .chip { border-radius:20px; padding:3px 10px; font-size:12px; border:1px solid var(--line);
          display:inline-flex; align-items:center; gap:6px; }
  .chip i { width:10px; height:10px; border-radius:50%; display:inline-block; }
  h2 { font-size:15px; margin:2px 0 8px; letter-spacing:.02em; text-transform:uppercase; color:var(--muted); }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  th,td { text-align:left; padding:5px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
  th { color:var(--muted); font-weight:600; }
  .bar { height:8px; border-radius:5px; background:#3a322a; overflow:hidden; min-width:60px; }
  .bar > span { display:block; height:100%; }
  .flag { color:#e8b04b; font-size:12px; }
  .muted { color:var(--muted); }
  .legend { display:flex; flex-wrap:wrap; gap:8px; padding:2px 22px 6px; }
  .legend .chip { background:transparent; }
  footer { padding:14px 22px 40px; color:var(--muted); font-size:12px; border-top:1px solid var(--line); }
  code { color:#d8c8a8; }
  .note { color:#e8b04b; font-size:13px; margin-top:8px; }
  a.compound { color:var(--ink); text-decoration:underline dotted; cursor:help; }
</style>
</head>
<body>
<header>
  <h1>Cobber — flavour wheels</h1>
  <p>Each ingredient's aroma, broken into ten flavour families and the complementary
     notes that join it in real drinks. Everything traces to a cited compound.</p>
</header>
<div class="controls">
  <label for="pick">Ingredient</label>
  <input id="search" placeholder="filter…" size="14">
  <select id="pick"></select>
  <label><input type="checkbox" id="nativeOnly"> natives only</label>
</div>
<div class="legend" id="legend"></div>
<div class="wrap">
  <div class="card" id="wheelCard">
    <div id="wheel"></div>
    <div class="dom" id="dom"></div>
    <div id="taste"></div>
    <div class="note" id="note"></div>
  </div>
  <div class="card" id="sideCard">
    <h2>Flavour families</h2>
    <table id="famTable"><tbody></tbody></table>
    <h2 style="margin-top:18px">Taste — why <span class="muted" style="text-transform:none">— the molecules behind each taste</span></h2>
    <table id="tasteTable"><tbody></tbody></table>
    <h2 style="margin-top:18px">Harmonious notes <span class="muted" style="text-transform:none">— complementary families from the corpus</span></h2>
    <table id="harmTable"><tbody></tbody></table>
  </div>
</div>
<footer id="foot"></footer>
<script id="data" type="application/json">__DATA__</script>
<script>
const DB = JSON.parse(document.getElementById('data').textContent);
const FC = DB.family_colors, TC = DB.taste_colors;
const pick = document.getElementById('pick'), search = document.getElementById('search');
const nativeOnly = document.getElementById('nativeOnly');

function famColor(f){ return FC[f] || '#888'; }
function titleCase(s){ return (s||'').replace(/_/g,' '); }

function options(){
  const q = search.value.trim().toLowerCase();
  const only = nativeOnly.checked;
  const ids = Object.keys(DB.ingredients).sort((a,b)=>
    DB.ingredients[a].display_name.localeCompare(DB.ingredients[b].display_name));
  pick.innerHTML='';
  for(const id of ids){
    const ing = DB.ingredients[id];
    if(only && !ing.is_native) continue;
    if(q && !ing.display_name.toLowerCase().includes(q) && !id.includes(q)) continue;
    const o=document.createElement('option'); o.value=id; o.textContent=ing.display_name + (ing.is_native?' ✦':'');
    pick.appendChild(o);
  }
  if(pick.options.length) render(pick.value);
}

function donut(fams){
  const size=320, cx=size/2, cy=size/2, rOuter=140, rInner=78;
  if(!fams.length){
    return `<svg viewBox="0 0 ${size} ${size}"><circle cx="${cx}" cy="${cy}" r="${rOuter}" fill="none" stroke="#3a322a" stroke-width="2"/>`+
           `<text x="${cx}" y="${cy}" fill="#b8ab97" text-anchor="middle" dominant-baseline="middle">no wheel</text></svg>`;
  }
  let a0=-Math.PI/2, paths='';
  for(const f of fams){
    const a1=a0 + f.fraction*2*Math.PI;
    const x0=cx+rOuter*Math.cos(a0), y0=cy+rOuter*Math.sin(a0);
    const x1=cx+rOuter*Math.cos(a1), y1=cy+rOuter*Math.sin(a1);
    const xi1=cx+rInner*Math.cos(a1), yi1=cy+rInner*Math.sin(a1);
    const xi0=cx+rInner*Math.cos(a0), yi0=cy+rInner*Math.sin(a0);
    const large = (a1-a0)>Math.PI?1:0;
    paths += `<path d="M${x0} ${y0} A${rOuter} ${rOuter} 0 ${large} 1 ${x1} ${y1} L${xi1} ${yi1} A${rInner} ${rInner} 0 ${large} 0 ${xi0} ${yi0} Z" `+
             `fill="${famColor(f.family)}" stroke="#14110f" stroke-width="1.5"><title>${titleCase(f.family)} — ${(f.fraction*100).toFixed(0)}% (${f.words.join(', ')})</title></path>`;
    // label for wedges >= 8%
    if(f.fraction>=0.08){
      const am=(a0+a1)/2, rl=(rOuter+rInner)/2;
      const lx=cx+rl*Math.cos(am), ly=cy+rl*Math.sin(am);
      paths += `<text x="${lx}" y="${ly}" fill="#14110f" font-size="10" font-weight="700" text-anchor="middle" dominant-baseline="middle">${titleCase(f.family).split(' ')[0]}</text>`;
    }
    a0=a1;
  }
  return `<svg viewBox="0 0 ${size} ${size}">${paths}</svg>`;
}

function render(id){
  const ing = DB.ingredients[id]; if(!ing) return;
  document.getElementById('wheel').innerHTML = donut(ing.families);
  document.getElementById('dom').innerHTML = ing.dominant
    ? `Dominant: <b style="color:${famColor(ing.dominant)}">${titleCase(ing.dominant)}</b> · ${ing.n_compounds} compounds · coverage ${ing.coverage}`
    : `${ing.n_compounds} compounds · coverage ${ing.coverage}`;

  // taste overlay chips
  const t = document.getElementById('taste');
  if(ing.taste_overlay && ing.taste_overlay.length){
    t.innerHTML = '<div class="chips">' + ing.taste_overlay.map(o=>
      `<span class="chip"><i style="background:${TC[o.class]||'#888'}"></i>${o.class} <span class="muted">(${o.compounds.join(', ')})</span></span>`).join('') + '</div>';
  } else t.innerHTML='';

  const note = document.getElementById('note');
  let n = ing.note ? ing.note : '';
  if(ing.provisional) n += (n?' ':'') + '⚠ Some grounding is provisional: ' + ing.provisional_compounds.join(', ') + '.';
  note.textContent = n;

  // family table
  const fam = document.querySelector('#famTable tbody'); fam.innerHTML='';
  if(!ing.families.length){ fam.innerHTML='<tr><td class="muted">No described compounds — nothing to draw honestly.</td></tr>'; }
  for(const f of ing.families){
    const pct=(f.fraction*100).toFixed(0);
    fam.insertAdjacentHTML('beforeend',
      `<tr><td><span class="chip"><i style="background:${famColor(f.family)}"></i>${titleCase(f.family)}</span></td>`+
      `<td style="width:120px"><div class="bar"><span style="width:${pct}%;background:${famColor(f.family)}"></span></div></td>`+
      `<td class="muted">${pct}%</td>`+
      `<td class="muted">${f.words.map(w=>compoundTip(w,f.compounds)).join(', ')}</td></tr>`);
  }

  // taste — why (provenance)
  const tt = document.querySelector('#tasteTable tbody'); tt.innerHTML='';
  const axes = ing.taste_axes || {}, prov = ing.taste_provenance || {}, gaps = ing.taste_gaps || [];
  const axisKeys = Object.keys(axes);
  if(!axisKeys.length && !Object.keys(prov).length){
    tt.innerHTML='<tr><td class="muted">No curated taste for this ingredient.</td></tr>';
  } else {
    // one row per taste class we can explain, plus gap rows
    const classes = new Set([...Object.keys(prov), ...axisKeys]);
    for(const cls of classes){
      const cause = prov[cls];
      const val = axes[cls];
      let causeCell;
      if(cause && cause.length) causeCell = cause.join(', ');
      else if(gaps.includes(cls)) causeCell = '<span class="flag">cause not recorded (provenance gap)</span>';
      else causeCell = '<span class="muted">—</span>';
      tt.insertAdjacentHTML('beforeend',
        `<tr><td>${titleCase(cls)}${val!=null?` <span class="muted">${val}</span>`:''}</td>`+
        `<td class="muted">${causeCell}</td></tr>`);
    }
  }

  // harmonious notes
  const h = document.querySelector('#harmTable tbody'); h.innerHTML='';
  if(!ing.harmonious.length){ h.innerHTML='<tr><td class="muted">No complementary notes in the corpus.</td></tr>'; }
  for(const n2 of ing.harmonious){
    h.insertAdjacentHTML('beforeend',
      `<tr><td><span class="chip"><i style="background:${famColor(n2.family)}"></i>${titleCase(n2.family)}</span></td>`+
      `<td class="muted">npmi ${n2.npmi>=0?'+':''}${n2.npmi.toFixed(2)}${n2.above_chance?'':' <span class="flag">(below chance)</span>'}</td>`+
      `<td class="muted">common ${n2.harmony.toFixed(2)}</td>`+
      `<td class="muted">with ${n2.with.map(titleCase).join(', ')}</td></tr>`);
  }
}

function compoundTip(word){ return `<span>${word}</span>`; }

function legend(){
  const el=document.getElementById('legend');
  el.innerHTML = DB.family_order.map(f=>`<span class="chip"><i style="background:${famColor(f)}"></i>${titleCase(f)}</span>`).join('')
    + Object.keys(TC).map(t=>`<span class="chip"><i style="background:${TC[t]}"></i>${t} (taste)</span>`).join('');
}

document.getElementById('foot').innerHTML =
  `Odour descriptors: <b>${DB.meta.odor_source}</b>. Taste classes: <b>${DB.meta.taste_source}</b>. `+
  `Harmonious notes: <b>${DB.meta.harmony_source}</b>. Self-contained — no network, generated by scripts/render_flavor_wheel.py.`;

search.addEventListener('input', options);
nativeOnly.addEventListener('change', options);
pick.addEventListener('change', e=>render(e.target.value));
legend(); options();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()

    payload = build_payload()
    # Escape "</" so no data string can close the embedded <script> tag early.
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    html = PAGE.replace("__DATA__", data_json)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")

    n = len(payload["ingredients"])
    print(f"Wrote flavour-wheel page for {n} ingredients -> {args.output}")


if __name__ == "__main__":
    main()
