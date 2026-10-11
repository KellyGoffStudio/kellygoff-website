#!/usr/bin/env python3
"""Builds Kelly Goff Studio proposal sheets (letter portrait PDF) from a project folder in sheets/<slug>/.
Usage: python3 tools/proposal_sheets.py arboreal-line [out.pdf]
Each sheets/<slug>/sheet.json holds the text; images sit beside it (hero.jpg, front.png, left.png, right.png, logo.png)."""
import json, sys, html
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
slug = sys.argv[1]
D = ROOT / 'sheets' / slug
S = json.loads((D / 'sheet.json').read_text(encoding='utf8'))
E = lambda t: html.escape(str(t))
FONTS = (ROOT / 'src/fonts').as_uri()

CSS = f'''
@font-face{{font-family:Barlow;font-weight:400;src:url({FONTS}/Barlow-400.woff2)}}
@font-face{{font-family:Barlow;font-weight:500;src:url({FONTS}/Barlow-500.woff2)}}
@font-face{{font-family:BC;font-weight:400;src:url({FONTS}/BarlowCondensed-400.woff2)}}
@font-face{{font-family:BC;font-weight:500;src:url({FONTS}/BarlowCondensed-500.woff2)}}
@font-face{{font-family:BC;font-weight:600;src:url({FONTS}/BarlowCondensed-600.woff2)}}
@font-face{{font-family:BC;font-weight:700;src:url({FONTS}/BarlowCondensed-700.woff2)}}
@page{{size:612pt 792pt;margin:0}}
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{--ink:#1d1f20;--navy:#3d5c7c;--rule:#b8bcc0;--paper:#f2f2f3;--body:#2a2d2f}}
html,body{{background:var(--paper)}}
body{{font-family:Barlow,sans-serif;color:var(--ink);-webkit-print-color-adjust:exact;print-color-adjust:exact}}
.page{{position:relative;width:612pt;height:792pt;page-break-after:always;overflow:hidden;background:var(--paper)}}
.frame{{position:absolute;left:25pt;top:25pt;right:25pt;bottom:25pt;border:.75pt solid var(--ink)}}
.abs{{position:absolute}}
.lab{{font:500 5.2pt BC;letter-spacing:.14em;text-transform:uppercase;color:var(--navy)}}
.hd{{font:700 8pt BC;letter-spacing:.2em;text-transform:uppercase}}
.hdr{{font:500 5.6pt BC;letter-spacing:.2em;text-transform:uppercase;color:var(--navy)}}
.sec{{font:700 7pt BC;letter-spacing:.18em;text-transform:uppercase;display:flex;align-items:center;gap:8pt}}
.sec:after{{content:"";flex:1;border-top:.5pt solid var(--rule)}}
.body{{font:400 6.9pt/1.5 Barlow;color:var(--body)}}
.body p+p{{margin-top:7pt}}
.val{{font:500 7.4pt BC;letter-spacing:.02em}}
.tb{{position:absolute;right:38pt;bottom:38pt;width:306pt;height:103pt;border:1pt solid var(--ink);background:var(--paper);display:grid;grid-template-columns:70pt 1fr;grid-template-rows:1fr}}
.tb .logo{{border-right:.5pt solid var(--rule);display:flex;align-items:center;justify-content:center}}
.tb .logo img{{width:42pt}}
.tb .r{{display:grid;grid-template-rows:auto 1fr auto}}
.tb .r1{{padding:7pt 9pt 5pt;border-bottom:.5pt solid var(--rule)}}
.tb .ttl{{font:700 10.5pt BC;letter-spacing:.01em;margin-top:2pt;text-transform:uppercase}}
.tb .sub{{font:400 6.4pt BC;letter-spacing:.04em;color:#4b5156;margin-top:1pt;text-transform:uppercase}}
.tb .r2{{display:grid;grid-template-columns:.9fr .8fr 1.2fr 1.1fr;border-bottom:.5pt solid var(--rule)}}
.tb .r2>div{{padding:5pt 7pt}}
.tb .r2>div+div{{border-left:.5pt solid var(--rule)}}
.tb .r3{{display:grid;grid-template-columns:1fr 50pt}}
.tb .r3 .c{{font:400 5pt/1.35 Barlow;color:#4b5156;padding:5pt 8pt}}
.tb .r3 .s{{border-left:.5pt solid var(--rule);padding:4pt 7pt}}
.tb .r3 .s b{{display:block;font:700 12pt BC;margin-top:1pt}}
img{{display:block}}
'''

def titleblock(label, title, sheet, scale):
    p = S['project']
    return f'''<div class="tb"><div class="logo"><img src="logo.png"></div><div class="r">
<div class="r1"><div class="lab">{E(label)}</div><div class="ttl">{E(title)}</div><div class="sub">{E(p["subtitle"])}</div></div>
<div class="r2"><div><div class="lab">Date</div><div class="val">{E(S["date"])}</div></div><div><div class="lab">Scale</div><div class="val">{E(scale)}</div></div>
<div><div class="lab">Overall dims</div><div class="val">{E(p["dims"])}</div></div><div><div class="lab">Materials</div><div class="val">{E(p["materials_short"])}</div></div></div>
<div class="r3"><div class="c">© {S["year"]} Kelly Goff Studio. Concept and drawings remain the property of the artist.</div><div class="s"><div class="lab">Sheet</div><b>{E(sheet)}</b></div></div></div></div>'''

def a1():
    p = S['project']; paras = ''.join(f'<p>{E(t)}</p>' for t in S['statement'])
    return f'''<div class="page"><div class="frame"></div>
<div class="abs hd" style="left:38pt;top:37pt">Kelly Goff Studio</div><div class="abs hdr" style="right:38pt;top:38pt">{E(S["header_right"])}</div>
<div class="abs" style="left:38pt;right:38pt;top:55pt;height:440pt;overflow:hidden;border:.5pt solid var(--rule)"><img src="hero.jpg" style="width:100%;height:100%;object-fit:cover;object-position:{S["hero_pos"]}"></div>
<div class="abs" style="left:38pt;top:508pt;width:92pt"><div class="lab" style="border-bottom:.5pt solid var(--rule);padding-bottom:3pt;margin-bottom:8pt">Concept</div><div style="font:700 11pt/1.1 BC;letter-spacing:.03em;text-transform:uppercase">{E(S["concept_title"])}</div></div>
<div class="abs" style="left:146pt;right:38pt;top:508pt"><div class="lab" style="border-bottom:.5pt solid var(--rule);padding-bottom:3pt;margin-bottom:8pt">Project statement</div><div class="body">{paras}</div></div>
<div class="abs" style="left:38pt;bottom:38pt;width:200pt"><div class="lab">Issued for</div><div class="val" style="margin-bottom:6pt">{E(S["issued_for"])}</div><div class="lab">Site</div><div class="val">{E(p["site"])}</div></div>
{titleblock("Project", p["name"], "A-1", "NTS")}</div>'''

SCALE = '1/4" = 1\'-0"'

def a2():
    p = S['project']; PT = S['pt_per_px']  # layout scale: 1/4" = 1'-0" -> 18 pt per ft
    def view(n, label, w, h, x):
        return f'<div class="abs" style="left:{x}pt;top:88pt;width:{w*PT}pt"><div class="sec">{label}</div><img src="{n}.png" style="margin-top:6pt;width:{w*PT}pt;height:{h*PT}pt"></div>'
    fw, lw, rw, H = S['px']['front'], S['px']['left'], S['px']['right'], S['px']['h']
    gap = (612 - 2*38 - (fw+lw+rw)*PT) / 2
    x1 = 38; x2 = x1 + fw*PT + gap; x3 = x2 + lw*PT + gap
    views = view('front', 'Front', fw, H, x1) + view('left', 'Left', lw, H, x2) + view('right', 'Right', rw, H, x3)
    rows = ''.join(f'<tr><td>{E(a)}</td><td>{E(b)}</td></tr>' for a, b in S['schedule'])
    notes = ''.join(f'<p>{E(t)}</p>' for t in S['notes'])
    ft = 18  # pt per foot
    bar = ''.join(f'<div style="display:inline-block;width:{ft*2}pt;height:5pt;border:.5pt solid var(--ink);margin-left:-.5pt;background:{"var(--ink)" if i % 2 == 0 else "transparent"}"></div>' for i in range(4))
    return f'''<div class="page"><div class="frame"></div>
<div class="abs hd" style="left:38pt;top:37pt">Orthographic Views</div><div class="abs hdr" style="right:38pt;top:38pt">Dimensions in feet and inches</div>
<div class="abs" style="left:38pt;right:38pt;top:52pt;border-top:.5pt solid var(--rule)"></div>
<div class="abs hdr" style="right:38pt;top:70pt;color:var(--ink)">Scale {SCALE}</div>
{views}
<div class="abs" style="left:38pt;top:{88+6+H*PT+22}pt;width:250pt"><div class="sec">Dimension schedule</div><table style="margin-top:5pt;width:100%;border-collapse:collapse;font:500 7.2pt BC;letter-spacing:.03em">{rows}</table></div>
<div class="abs" style="left:38pt;bottom:38pt;width:230pt"><div style="margin-bottom:4pt;white-space:nowrap;font-size:0">{bar}</div>
<div style="display:flex;justify-content:space-between;width:{ft*8}pt;font:400 5.4pt BC;color:var(--navy);margin-bottom:5pt"><span>0</span><span>4'</span><span>8'</span></div><div class="body" style="font-size:5.8pt;line-height:1.4">{notes}</div></div>
{titleblock("Sheet title", S["a2_title"], "A-2", SCALE)}</div>'''

CSS += '''table td{padding:3.2pt 0;border-bottom:.5pt dotted var(--rule)}table td+td{text-align:right}table tr:first-child td{border-top:.5pt dotted var(--rule)}'''
HTML = f'<!doctype html><meta charset=utf-8><style>{CSS}</style>{a1()}{a2()}'
(D / '_sheet.html').write_text(HTML, encoding='utf8')
out = Path(sys.argv[2]) if len(sys.argv) > 2 else D / f'{S["file"]}.pdf'
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page()
    pg.goto((D / '_sheet.html').as_uri()); pg.wait_for_timeout(500)
    pg.pdf(path=str(out), width='8.5in', height='11in', print_background=True, margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'})
    b.close()
print('wrote', out)
