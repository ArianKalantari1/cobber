"""Render the Apéritif & Co cocktail menu (menu.json) to a self-contained HTML file and an A4 PDF.

Usage:  python3 docs/menu/build_menu.py
Needs:  curl (to fetch the two OFL Google Fonts once) and a Chromium/Chrome binary for the PDF
        (set CHROME=/path/to/chrome if it isn't found automatically).
Fonts are embedded in the HTML as base64, which the SIL Open Font Licence allows for documents.
Static (per-weight) font files are requested on purpose: Chrome embeds variable fonts in the PDF as
Type 3, which print-shop preflight checks often flag; static fonts embed as TrueType.
"""
import base64
import html
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_HTML = HERE / "aperitif-co-cocktail-menu.html"
OUT_PDF = HERE / "aperitif-co-cocktail-menu.pdf"
FONT_CACHE = Path(os.environ.get("MENU_FONT_CACHE", Path.home() / ".cache" / "aperitif-menu-fonts"))
FONTS_CSS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,600;1,500"
             "&family=Raleway:wght@400;600&display=swap")
DAGGER_CSS = FONTS_CSS + "&text=%E2%80%A0"  # the latin subsets have no dagger (†); this adds just that glyph
# A browser too old for variable fonts, so Google Fonts serves static per-weight files.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"


def fetch_fonts() -> list[dict]:
    """Download the latin subset of each family/style/weight, then the dagger-only subsets, once each.

    Returns @font-face descriptors in declaration order. The dagger faces come last so the browser
    checks them first for U+2020 (the latin faces claim that range but have no glyph for it).
    """
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    fonts = []
    for css_url, kind in ((FONTS_CSS, "latin"), (DAGGER_CSS, "dagger")):
        css = subprocess.run(["curl", "-sS", "-m", "30", "-A", UA, css_url],
                             check=True, capture_output=True, text=True).stdout
        for subset, body in re.findall(r"(?:/\*\s*(\S+)\s*\*/\s*)?@font-face\s*{([^}]*)}", css):
            if subset and subset != "latin":
                continue
            face = {key: re.search(rf"{key}:\s*([^;]+);", body).group(1).strip()
                    for key in ("font-family", "font-style", "font-weight", "unicode-range")}
            url = re.search(r"url\((\S+?)\)", body).group(1)
            family = face["font-family"].strip("'").replace(" ", "")
            path = FONT_CACHE / f"{family}-{face['font-weight']}-{face['font-style']}-{kind}.woff2"
            if not path.exists():
                subprocess.run(["curl", "-sS", "-m", "30", "-o", str(path), url], check=True)
            fonts.append({**face, "path": path})
    return fonts


def font_faces(fonts: list[dict]) -> str:
    rules = []
    for f in fonts:
        data = base64.b64encode(f["path"].read_bytes()).decode()
        rules.append(f"@font-face{{font-family:{f['font-family']};font-style:{f['font-style']};"
                     f"font-weight:{f['font-weight']};unicode-range:{f['unicode-range']};"
                     f"src:url(data:font/woff2;base64,{data}) format('woff2');}}")
    return "\n".join(rules)


# Drawn as inline SVG: neither font has a four-point star, so ✦ would fall back to a system font.
STAR = '<svg class="star" viewBox="0 0 10 10" aria-hidden="true"><path d="M5 0l1.1 3.9L10 5 6.1 6.1 5 10 3.9 6.1 0 5l3.9-1.1z"/></svg>'


def esc(text: str) -> str:
    return html.escape(text.replace("'", "\u2019"), quote=False)  # typographic apostrophes


def item_html(item: dict) -> str:
    price = f'<span class="pr">{item["price"]}</span>' if item.get("price") else '<span class="pr tbc">TBC</span>'
    egg = '<sup class="egg">†</sup>' if item.get("egg") else ""
    tag = f'<span class="tag">{esc(item["tag"])}</span>' if item.get("tag") else ""
    return (f'<div class="item"><div class="head"><span class="nm">{esc(item["name"])}{egg}</span>'
            f'{price}{tag}</div><div class="ing">{esc(item["ing"])}</div>'
            f'<div class="desc">{esc(item["desc"])}</div></div>')


def section_html(section: dict) -> str:
    items = "".join(item_html(i) for i in section.get("items", []))
    note = f'<p class="note">{esc(section["note"])}</p>' if section.get("note") else ""
    cls = "section boxed" if section.get("boxed") else "section"
    gap = f' style="--gap:{section["gap"]}mm"' if section.get("gap") else ""  # spacing between drinks
    return (f'<section class="{cls}"{gap}><h2>{esc(section["title"])}</h2>'
            f'<p class="intro">{esc(section["intro"])}</p>'
            f'{f"<div class=cols>{items}</div>" if items else ""}{note}</section>')


CSS = """
@page { size: A4; margin: 0; }
:root { --cream:#F6F0E2; --ink:#1E2A1D; --green:#22301F; --burgundy:#6E1C27; --gold:#B08D57;
        --muted:#5E6258; --box:#EFE6D2; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--cream); color: var(--ink); }
body { font-family: 'Raleway', sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { width: 210mm; height: 297mm; padding: 17mm 18mm 15mm; position: relative; overflow: hidden;
        display: flex; flex-direction: column; page-break-after: always; }
.page:last-child { page-break-after: auto; }
.page { background: var(--cream); }
@media screen {  /* viewing the HTML in a browser: show the pages as sheets */
  html, body { background: #D8D2C4; }
  body { padding: 8mm 0; }
  .page { margin: 0 auto 8mm; box-shadow: 0 1mm 5mm rgba(0,0,0,.18); }
}
.frame { position: absolute; inset: 7mm; border: 0.45mm solid var(--gold); }
.frame::after { content: ''; position: absolute; inset: 1.3mm; border: 0.2mm solid rgba(176,141,87,.6); }
.brand { text-align: center; margin-bottom: 6mm; position: relative; }
.brand .name { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 25pt;
               letter-spacing: .3em; text-transform: uppercase; color: var(--green); padding-left: .3em; }
.brand .amp { font-style: italic; font-weight: 500; text-transform: none; letter-spacing: 0;
              color: var(--gold); margin: 0 .18em 0 -.05em; }
.brand .sub { font-size: 7.6pt; letter-spacing: .6em; text-transform: uppercase; color: var(--muted);
              margin-top: 1mm; padding-left: .6em; }
.brand .rule { width: 52mm; margin: 3.2mm auto 0; display: flex; align-items: center; gap: 2.5mm; }
.brand .rule::before, .brand .rule::after { content: ''; flex: 1; height: .3mm; background: var(--gold); }
.star { width: 2.4mm; height: 2.4mm; fill: var(--gold); }
.brand.small .name { font-size: 15pt; }
.brand.small { margin-bottom: 5mm; }
.section { position: relative; }
h2 { text-align: center; font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 16.5pt;
     letter-spacing: .26em; text-transform: uppercase; color: var(--green); margin: 0; padding-left: .26em; }
.intro { text-align: center; font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 500;
         font-size: 11.5pt; color: var(--muted); margin: .6mm 0 5.2mm; }
.cols { columns: 2; column-gap: 13mm; }
.item { break-inside: avoid; margin-bottom: var(--gap, 4.4mm); }
.head { display: flex; align-items: baseline; flex-wrap: wrap; column-gap: 2.4mm; row-gap: .6mm; }
.nm { font-weight: 600; font-size: 9.2pt; letter-spacing: .13em; text-transform: uppercase; color: var(--green); }
.egg { color: var(--gold); font-size: 8pt; margin-left: .6mm; font-weight: 600; line-height: 0; }
.pr { font-family: 'Cormorant Garamond', serif; font-weight: 600; font-size: 12pt; color: var(--burgundy);
      font-variant-numeric: lining-nums; }
.pr.tbc { font-size: 8.5pt; letter-spacing: .1em; }
.tag { font-size: 6.2pt; letter-spacing: .15em; text-transform: uppercase; color: var(--gold);
       border: .25mm solid var(--gold); padding: .25mm 1.5mm; border-radius: 3mm; white-space: nowrap;
       position: relative; top: -.3mm; }
.ing { font-size: 8.5pt; line-height: 1.4; margin-top: .9mm; text-wrap: pretty; }
.desc { font-family: 'Cormorant Garamond', serif; font-style: italic; font-weight: 500; font-size: 11pt;
        color: var(--burgundy); margin-top: .3mm; }
.boxed { margin-top: 3mm; background: var(--box); border: .3mm solid var(--gold); padding: 5.5mm 8mm 1.5mm; }
.boxed h2 { font-size: 13.5pt; }
.boxed .intro { margin-bottom: 4.2mm; }
.note { text-align: center; font-size: 7.8pt; color: var(--muted); margin: 0 0 4mm; letter-spacing: .03em; }
.boxed .note { margin-top: -1mm; }
main { margin: auto 0; }
footer { text-align: center; font-size: 7.4pt; color: var(--muted); letter-spacing: .04em; }
footer .sep { color: var(--gold); margin: 0 2mm; }
"""


def build_html(menu: dict, faces: str) -> str:
    pages = {}
    for section in menu["sections"]:
        pages.setdefault(section["page"], []).append(section_html(section))
    venue = esc(menu["venue"]).replace("&amp;", '<span class="amp">&amp;</span>')
    out = []
    for n in sorted(pages):
        brand_cls = "brand" if n == 1 else "brand small"
        sub = f'<div class="sub">{esc(menu["title"])}</div><div class="rule">{STAR}</div>' if n == 1 else ""
        footer = ""
        if n == max(pages):
            footer = "<footer>" + '<span class="sep">·</span>'.join(esc(f) for f in menu["footnotes"]) + "</footer>"
        out.append(f'<div class="page"><div class="frame"></div><header class="{brand_cls}">'
                   f'<div class="name">{venue}</div>{sub}</header><main>{"".join(pages[n])}</main>{footer}</div>')
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<title>{esc(menu["venue"])} Cocktails</title><style>{faces}\n{CSS}</style></head>'
            f'<body>{"".join(out)}</body></html>')


def find_chrome() -> str | None:
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for path in sorted(Path("/opt/pw-browsers").glob("chromium-*/chrome-linux/chrome"), reverse=True):
        return str(path)
    for name in ("chromium", "chromium-browser", "google-chrome"):
        if shutil.which(name):
            return shutil.which(name)
    return None


def main() -> None:
    menu = json.loads((HERE / "menu.json").read_text(encoding="utf-8"))
    OUT_HTML.write_text(build_html(menu, font_faces(fetch_fonts())), encoding="utf-8")
    print(f"wrote {OUT_HTML}")
    chrome = find_chrome()
    if not chrome:
        print("no Chromium found: open the HTML and print it to PDF (A4, no margins, background graphics on)")
        return
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={OUT_PDF}", OUT_HTML.as_uri()], check=True, capture_output=True)
    print(f"wrote {OUT_PDF}")


if __name__ == "__main__":
    main()
