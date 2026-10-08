"""Build the two downloadable PDFs from the site data: python3 tools/pdfs.py -> src/files/"""
import json, html, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parent.parent
E = html.escape
cv = json.load(open(ROOT / 'data/cv.json')); site = json.load(open(ROOT / 'data/site.json')); proj = json.load(open(ROOT / 'data/projects.json'))
FONTS = (ROOT / 'src/fonts').as_uri()
CSS = f"""
@font-face{{font-family:Barlow;font-weight:400;src:url({FONTS}/Barlow-400.woff2)}}
@font-face{{font-family:Barlow;font-weight:500;src:url({FONTS}/Barlow-500.woff2)}}
@font-face{{font-family:Barlow;font-weight:600;src:url({FONTS}/Barlow-600.woff2)}}
@font-face{{font-family:'Barlow Condensed';font-weight:500;src:url({FONTS}/BarlowCondensed-500.woff2)}}
@font-face{{font-family:'Barlow Condensed';font-weight:600;src:url({FONTS}/BarlowCondensed-600.woff2)}}
@page{{size:Letter;margin:0.75in 0.8in}}
*{{box-sizing:border-box}}
body{{margin:0;font:400 10pt/1.4 Barlow,sans-serif;color:#1d1f20}}
h1{{font:600 22pt/1.1 'Barlow Condensed',sans-serif;letter-spacing:.2em;text-transform:uppercase;margin:0 0 4pt}}
.sub{{font:500 9pt 'Barlow Condensed',sans-serif;letter-spacing:.16em;text-transform:uppercase;color:#3d5c7c;margin-bottom:18pt}}
h2{{font:600 9.5pt 'Barlow Condensed',sans-serif;letter-spacing:.22em;text-transform:uppercase;margin:18pt 0 6pt;padding-bottom:3pt;border-bottom:.75pt solid #b9bcbf;break-after:avoid}}
.row{{display:grid;grid-template-columns:62pt 1fr;gap:10pt;padding:2.2pt 0;break-inside:avoid}}
.row .y{{color:#3d5c7c;font-weight:500;font-variant-numeric:tabular-nums}}
.row.nox{{display:block}}
.pl{{border-top:.75pt solid #d4d6d8;padding:7pt 0;break-inside:avoid;display:grid;grid-template-columns:1fr 62pt;gap:10pt}}
.pl .t{{font:600 10.5pt 'Barlow Condensed',sans-serif;letter-spacing:.12em;text-transform:uppercase}}
.pl .m{{color:#4a5055;font-size:9pt}}
.pl .y{{text-align:right;color:#3d5c7c;font-weight:500}}
.foot{{margin-top:20pt;font-size:8pt;color:#6a7075}}
"""
def page(body): return f'<!doctype html><meta charset="utf-8"><style>{CSS}</style>{body}'
def cv_html():
    born = cv['born'].split(' / ')
    secs = ''.join(f'<h2>{E(s["title"])}</h2>' + ''.join((f'<div class="row"><span class="y">{E(y)}</span><span>{E(t)}</span></div>' if y else f'<div class="row nox"><span>{E(t)}</span></div>') for y, t in s['rows']) for s in cv['sections'])
    return page(f'<h1>Kelly Goff</h1><div class="sub">Resume · Born {E(born[-1])}, {E(born[0])} · Lives and works in {E(site["location"])}</div>{secs}'
                f'<div class="foot">kellygoff.net · @kellygoffstudio</div>')
def pl_html():
    order = site.get('continuousLineOrder', [])
    def key(p):
        gi = 0 if p['series'] == 'Continuous Line' else 1
        return (gi, order.index(p['slug']) if p['slug'] in order else 999, -int(p['year'][:4]), p['title'])
    items = ''
    for p in sorted([q for q in proj['public'] if q.get('pdf', True)], key=key):
        meta = [x for x in (p.get('site'), p.get('material'), p.get('size'), p.get('status')) if x]
        items += f'<div class="pl"><div><div class="t">{E(p["title"])}</div><div class="m">{E(" · ".join(meta))}</div></div><div class="y">{E(p["year"])}</div></div>'
    return page(f'<h1>Public Art</h1><div class="sub">Kelly Goff · Project list</div>{items}<div class="foot">kellygoff.net/public-work</div>')
def main():
    out = ROOT / 'src/files'; out.mkdir(exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page()
        for name, h in (('Kelly-Goff-Resume.pdf', cv_html()), ('Kelly-Goff-Public-Art-Project-List.pdf', pl_html())):
            tmp = out / '_t.html'; tmp.write_text(h, encoding='utf8')
            pg.goto(tmp.as_uri()); pg.wait_for_timeout(300)
            pg.pdf(path=str(out / name), prefer_css_page_size=True, print_background=True); tmp.unlink()
        b.close()
    print('ok')
main()
