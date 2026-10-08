import re
#!/usr/bin/env python3
"""Build kellygoff.net as a static site.

  python3 tools/build.py            -> dist/          (production: root-absolute links, redirects, sitemap)
  python3 tools/build.py --preview  -> dist-preview/  (relative links, works from any folder or file://)

Edit data/*.json, drop photos in images/<slug>/, run tools/images.py, then build.
"""
import json, math, random, shutil, sys, html, re, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MODE = 'preview' if '--preview' in sys.argv else 'prod'
OUT = ROOT / ('dist-preview' if MODE == 'preview' else 'dist')
E = html.escape

site = json.loads((ROOT / 'data/site.json').read_text(encoding='utf8'))
proj = json.loads((ROOT / 'data/projects.json').read_text(encoding='utf8'))
cv = json.loads((ROOT / 'data/cv.json').read_text(encoding='utf8'))
fw = json.loads((ROOT / 'data/fieldwork.json').read_text(encoding='utf8'))
RD = json.loads((ROOT / 'data/renderings.json').read_text(encoding='utf8'))
for _r in RD: _r.update({'year': '', 'status': 'Rendering, not built', 'uncropped': True, 'img_key': 'rdo-' + _r['slug'], 'back': 'public-work', 'series_label': 'Drawings & Renderings'})
PUB, STU = proj['public'], proj['studio']
manifest = {}
mp = ROOT / 'processed/manifest.json'
if mp.exists(): manifest = json.loads(mp.read_text())
PLACEHOLDERS_USED = set()

# ---------------------------------------------------------------- urls
CUR = ''   # path of the page being rendered, '' for home, 'public-work/' etc.

def depth(p): return len([x for x in p.split('/') if x])

def link(p):
    """URL of page p ('' | 'cv/' | 'public-work/slug/') seen from the current page."""
    if MODE == 'prod': return '/' + p
    rel = '../' * depth(CUR)
    return rel + (p + 'index.html')

def LW(t):
    """Escape text and hyperlink the first LineWorks to its page."""
    return E(t).replace('LineWorks', f'<a href="{link("fieldwork/lineworks/")}">LineWorks</a>', 1)

def asset(p):
    if MODE == 'prod': return '/' + p
    return '../' * depth(CUR) + p

# ---------------------------------------------------------------- placeholders
def squiggle(w, h, seed):
    r = random.Random(seed); n = r.randint(9, 12); pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + r.uniform(-.25, .25); rr = r.uniform(.12, .44)
        pts.append((w / 2 + math.cos(a) * rr * w + r.uniform(-.06, .06) * w, h / 2 + math.sin(a) * rr * h * 1.35 + r.uniform(-.06, .06) * h))
    order = list(range(n)); r.shuffle(order); p = [pts[i] for i in order]
    p = [(min(max(x, w * .08), w * .92), min(max(y, h * .12), h * .88)) for x, y in p]
    d = 'M%.1f %.1f' % p[0]
    for i in range(n):
        p0, p1, p2, p3 = p[(i - 1) % n], p[i], p[(i + 1) % n], p[(i + 2) % n]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6); c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += ' C%.1f %.1f %.1f %.1f %.1f %.1f' % (c1 + c2 + p2)
    return d

def write_placeholder(key, n, w, h, label):
    d = OUT / 'img' / key; d.mkdir(parents=True, exist_ok=True)
    seed = sum(ord(c) for c in key) * 7 + n * 13
    bg = ['#d9dcdf', '#cfd3d7', '#e1e3e5'][(seed + n) % 3]
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{bg}"/>'
           f'<path d="{squiggle(w, h, seed)}" fill="none" stroke="#72889f" stroke-width="{w / 520:.2f}" stroke-linecap="round" stroke-linejoin="round" opacity=".75"/>'
           f'<text x="{w * .08:.0f}" y="{h - h * .07:.0f}" font-family="Arial Narrow,Arial,sans-serif" font-size="{w / 62:.0f}" letter-spacing="{w / 400:.1f}" fill="#5f7288">PLACEHOLDER — {E(label.upper())}</text></svg>')
    f = f'ph-{n}.svg'; (d / f).write_text(svg, encoding='utf8')
    return f

def images_for(key, title, alt_base, nph=3):
    """List of image dicts for a project folder key. Real photos if processed, else placeholders."""
    meta = {}
    mf = ROOT / 'images' / key / 'meta.json'
    if mf.exists(): meta = json.loads(mf.read_text(encoding='utf8'))
    out = []
    if key in manifest:
        (OUT / 'img' / key).mkdir(parents=True, exist_ok=True)
        for i, m in enumerate(manifest[key]):
            for wd in m['widths']:
                shutil.copy(ROOT / 'processed' / key / f"{m['name']}-{wd}.webp", OUT / 'img' / key / f"{m['name']}-{wd}.webp")
            mt = meta.get(m['name']) or next((v for k, v in meta.items() if Path(k).stem == m['name']), {})
            ws = m['widths']
            out.append({'srcset': ', '.join(f"img/{key}/{m['name']}-{wd}.webp {wd}w" for wd in ws),
                        'src': f"img/{key}/{m['name']}-{ws[min(2, len(ws) - 1)]}.webp", 'full': f"img/{key}/{m['name']}-{ws[-1]}.webp",
                        'w': m['w'], 'h': m['h'], 'alt': mt.get('alt') or f'{alt_base}' + (f', view {i + 1}' if i else ''),
                        'cap': mt.get('caption', ''), 'ph': False, 'wide': mt.get('wide', False)})
    else:
        PLACEHOLDERS_USED.add(key)
        for i in range(nph):
            w, h = (1600, 1200) if i == 0 else (1200, 900)
            f = write_placeholder(key, i + 1, w, h, title if i == 0 else f'{title} ({i + 1})')
            out.append({'srcset': '', 'src': f'img/{key}/{f}', 'full': f'img/{key}/{f}', 'w': w, 'h': h, 'alt': f'Placeholder image for {title}', 'cap': '', 'ph': True, 'wide': False})
    return out

def img_tag(im, sizes='100vw', eager=False, cls=''):
    srcset = ''
    if im['srcset']:
        srcset = ' srcset="' + ', '.join(asset(x.split(' ')[0]) + ' ' + x.split(' ')[1] for x in im['srcset'].split(', ')) + f'" sizes="{sizes}"'
    return (f'<img src="{asset(im["src"])}"{srcset} width="{im["w"]}" height="{im["h"]}" alt="{E(im["alt"])}"'
            f'{"" if eager else " loading=lazy"} decoding=async{(" class=" + cls) if cls else ""}>')

# ---------------------------------------------------------------- layout
NAV = [('Public work', 'public-work/'), ('Studio', 'studio/'), ('Fieldwork', 'fieldwork/'), ('About', 'about/'), ('Resume', 'resume/'), ('Contact', 'contact/')]
PAGES = []   # (path, lastmod-less) for sitemap

def layout(title, body, desc='', active=None, og=None, ld=None, noindex=False, home=False):
    full_title = site['name'] if home else f'{title} — {site["name"]}'
    nav = ''.join(f'<li><a href="{link(p)}"{" aria-current=page" if p == active else ""}>{n}</a></li>' for n, p in NAV)
    desc = desc or site['description']
    canon = f'<link rel="canonical" href="{site["baseUrl"]}/{CUR}">' if MODE == 'prod' else ''
    robots = '<meta name="robots" content="noindex">' if (MODE == 'preview' or noindex) else ''
    ogimg = f'<meta property="og:image" content="{site["baseUrl"]}/{og}">' if (og and MODE == 'prod') else ''
    ldj = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>' if ld else ''
    preload = f'<link rel="preload" href="{asset("assets/fonts/BarlowCondensed-600.woff2")}" as="font" type="font/woff2" crossorigin>' if MODE == 'prod' else ''
    foot_ig = f'<a href="{E(site["instagram"])}" rel="me noopener">Instagram · @kellygoffstudio</a>'
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full_title)}</title><meta name="description" content="{E(desc)}">{canon}{robots}
<meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:type" content="website"><meta property="og:site_name" content="{E(site['name'])}">{ogimg}
<meta name="theme-color" content="#f2f2f3">
{preload}
<link rel="stylesheet" href="{asset('assets/css/site.css')}">{ldj}</head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-head"><div class="wrap"><a class="brand" href="{link('')}">Kelly Goff</a>
<button class="menu-btn" aria-expanded="false" aria-controls="nav">Menu</button>
<ul class="nav" id="nav">{nav}</ul></div></header>
<main id="main">{body}</main>
<footer class="site-foot"><div class="wrap"><span>{E(site['copyright'])}</span><span>{E(site['location'])}</span>{foot_ig}</div></footer>
<script src="{asset('assets/js/site.js')}" defer></script></body></html>'''

def emit(path, content):
    f = OUT / path / 'index.html' if path else OUT / 'index.html'
    f.parent.mkdir(parents=True, exist_ok=True); f.write_text(content, encoding='utf8')
    PAGES.append(path)

def page(path, fn):
    global CUR
    CUR = path
    emit(path, fn())

# ---------------------------------------------------------------- helpers
def sec(t, n='', note=''):
    return f'<h2 class="sec">{f"<span class=n>{n}</span>" if n else ""}{E(t)}{f"<span class=nt>{E(note)}</span>" if note else ""}</h2>'

def sentence_site(p):
    return p.get('site', '')

def capline(p, folder, status=False):
    sub = ' · '.join(x for x in [p.get('site') or '', p['year']] if x)
    st = f'<div class="m st">{E(p["status"])}</div>' if (status and p.get('status')) else ''
    return f'<div class="cap"><div class="t">{E(p["title"])}</div><div class="m">{E(sub)}</div>{st}</div>'

IMGS = {}
def get_imgs(p, folder):
    key = p.get('img_key', p['slug'])
    if key not in IMGS:
        IMGS[key] = images_for(key, p['title'], f'{p["title"]}' + (f', {p["site"]}' if p.get('site') else ''))
    return IMGS[key]

def tile(p, folder, extra='', status=False, sizes='(max-width:860px) 50vw, 33vw', eager=False):
    im = get_imgs(p, folder)[min(max(int(p.get('thumb', 1)), 1), len(get_imgs(p, folder))) - 1]
    return (f'<a class="tile" title="{E(p["title"])}" href="{link(f"{folder}/{p["slug"]}/")}"{extra}><div class="im">{img_tag(im, sizes, eager=eager).replace("<img ", f'<img style="object-position:{p["thumb_pos"]}" ', 1) if p.get("thumb_pos") else img_tag(im, sizes, eager=eager)}{'' if site.get('showTileCaptions', True) else f'<span class="hov">{E(p["title"])}</span>'}</div>'
            + (f'{capline(p, folder, status)}' if site.get('showTileCaptions', True) else '') + '</a>')

# ---------------------------------------------------------------- pages
def home():
    im = images_for('home', 'Continuous Line XI (Yellow), Wheaton College', 'Continuous Line XI (Yellow) by Kelly Goff, Wheaton College, Norton, MA', nph=1)[0]
    body = f'<div class="wrap hero-wrap"><div class="hero">{img_tag(im, "100vw", eager=True)}</div></div>'
    return layout('Home', body, site['description'], home=True)

GROUPS = [('Continuous Line', 'continuous-line', '2020 – present', 'Line works'), ('Place-based and collaborative', 'place-based', '2014 – 2021', 'Place-based / collaborative')]
SERIES_LABEL = {g[0]: g[3] for g in GROUPS}
def _grid_key(p):
    gi = [g[0] for g in GROUPS].index(p['series']) if p['series'] in [g[0] for g in GROUPS] else 99
    ol = site.get('continuousLineOrder', [])
    oi = ol.index(p['slug']) if (p['series'] == 'Continuous Line' and p['slug'] in ol) else 999
    return (gi, oi, -int(p['year'][:4]), p['title'])
PUB.sort(key=_grid_key)
def secd(k):
    t = site.get('publicSections', {}).get(k)
    return f'<p class="sec-d">{E(t)}</p>' if t else ''

def public_index():
    secs = ''
    for i, (g, gid, note, gname) in enumerate(GROUPS):
        items = sorted([p for p in PUB if p['series'] == g], key=lambda p: (-int(p['year'][:4]), p['title']))
        if g == 'Continuous Line' and site.get('continuousLineOrder'):
            ol = site['continuousLineOrder']; items.sort(key=lambda p: ol.index(p['slug']) if p['slug'] in ol else len(ol))
        ts = ''.join(tile(p, 'public-work') for p in items)
        secs += (f'<div>{sec(gname, f"{i + 1:02d}", note)}</div>{secd(gid)}<div class="grid" id="grid-{gid}">{ts}</div>')
    rt = ''
    for r_ in RD:
        im = images_for('rd-' + r_['slug'], r_['title'], r_['title'])[0]
        rt += (f'<a class="tile" title="{E(r_["title"])}" href="{link(f"public-work/renderings/{r_["slug"]}/")}"><div class="im">{img_tag(im, "(max-width:860px) 50vw, 33vw")}</div></a>')
    if RD: secs += f'<div>{sec("Drawings & Renderings", "03", "Unbuilt")}</div>{secd("renderings")}<div class="grid" id="grid-renderings">{rt}</div>'
    body = (f'<div class="wrap page-top"><div class="row-head"><div><h1>Public work</h1></div>'
            f'<a class="btn" href="{asset("files/Kelly-Goff-Public-Art-Project-List.pdf")}">Project list (PDF) ↓</a></div>'
            f'{secs}</div>')
    return layout('Public work', body, 'Public sculpture by Kelly Goff: Continuous Line and place-based work, with materials, sizes and sites.', active='public-work/')

def facts_html(p):
    rows = [('Year', p['year']), ('Series', p.get('series', '') if p.get('series') == 'Continuous Line' else ''), ('Material', p.get('material', '')), ('Size', p.get('size', '')), ('Site', p.get('site', '')),
            ('Status', p.get('status', '')), ('Commissioner', p.get('commissioner', '')), ('Fabrication', p.get('fabricator', '')), ('Budget', p.get('budget', ''))]
    return ''.join(f'<div class="fact"><div class="k">{k}</div><div class="v">{E(v)}</div></div>' for k, v in rows if v)

FW_BY_SLUG = {}
for f_ in fw:
    for s in f_.get('related_public', []) + f_.get('related_studio', []): FW_BY_SLUG.setdefault(s, []).append(f_)

def project_page(p, folder, label, lst):
    ims = get_imgs(p, folder)
    figl = []
    for i, im in enumerate(ims):
        cls = ''
        ct = ' class="ct"' if (p.get('uncropped') or im['w'] / im['h'] < 1.1) else ''
        fl = '<div class="ph-flag">Placeholder image</div>' if im['ph'] else ''
        cap = f'<figcaption>{E(im["cap"])}</figcaption>' if im['cap'] else ''
        figl.append(f'<figure{cls}><button type="button" data-lb="{asset(im["full"])}" data-alt="{E(im["alt"])}" data-cap="{E(p["title"])}" aria-label="Enlarge image {i + 1} of {len(ims)}"{ct}>'
                 f'{img_tag(im, "(max-width:860px) 100vw, 60vw", eager=(i == 0))}</button>{fl}{cap}</figure>')
    v = p.get('video')
    if v:
        figl.insert(v.get('at', len(figl)), f'<figure><div class="video vm"><iframe src="https://player.vimeo.com/video/{E(v["vimeo"])}?dnt=1" title="{E(v["label"])}" loading="lazy" '
                 f'allow="fullscreen; picture-in-picture" allowfullscreen></iframe></div></figure>')
    figs = ''.join(figl)
    note = f'<p class="note">{LW(p.get("text") or p.get("summary") or "")}</p>' if (p.get('text') or p.get('summary')) else ''
    lk = ''.join(f'<div class="fact"><div class="k">Link</div><div class="v"><a href="{E(l["url"])}" rel="noopener">{E(l["label"])}</a></div></div>' for l in p.get('links', []))
    note += lk
    au = p.get('audio')
    if au: note += f'<div class="fact"><div class="k">Audio</div><div class="v"><audio controls preload="none" src="{asset("assets/media/" + au["file"])}" aria-label="{E(au["label"])}"></audio><div class="m">{E(au["label"])}</div></div></div>'
    rel = ''
    if p['slug'] in FW_BY_SLUG:
        rel = '<div class="related">' + ''.join(f'<div class="fact"><div class="k">Fieldwork</div><div class="v"><a href="{link(f"fieldwork/{f_["slug"]}/")}">{E(f_["title"])}, {f_["date"][-4:]}</a></div></div>' for f_ in FW_BY_SLUG[p['slug']]) + '</div>'
    idx = lst.index(p); prv = lst[idx - 1] if idx > 0 else None; nxt = lst[idx + 1] if idx < len(lst) - 1 else None
    pager = (f'<nav class="pager" aria-label="More projects"><span>{f"<a href={chr(34)}{link(f"{folder}/{prv["slug"]}/")}{chr(34)}>← {E(prv["title"])}</a>" if prv else ""}</span>'
             f'<a href="{link(p.get('back', folder) + "/")}">All {label.lower()}</a><span>{f"<a href={chr(34)}{link(f"{folder}/{nxt["slug"]}/")}{chr(34)}>{E(nxt["title"])} →</a>" if nxt else ""}</span></nav>')
    series_c = f' / {E(SERIES_LABEL.get(p["series"], p["series"]))}' if p.get('series') == 'Continuous Line' else (f' / {E(p["series_label"])}' if p.get('series_label') else '')
    body = (f'<div class="wrap page-top"><div class="crumb"><a href="{link(p.get('back', folder) + "/")}">{label}</a>{series_c}</div>'
            f'<h1 style="margin-top:10px">{E(p["title"])}</h1>'
            f'<div class="proj"><div class="gal">{figs}</div><aside class="facts" aria-label="Project details">{facts_html(p)}{note}{rel}'
            f'</aside></div>{pager}</div>'
            f'<dialog class="lb" id="lb" aria-label="Image viewer"><div class="lb-in"><div class="stage"><img alt=""></div><div class="lb-cap"></div></div>'
            f'<button class="x" type="button">Close</button><button class="pv" type="button" aria-label="Previous image">←</button><button class="nx" type="button" aria-label="Next image">→</button></dialog>')
    ld = {'@context': 'https://schema.org', '@type': 'VisualArtwork', 'name': p['title'], 'creator': {'@type': 'Person', 'name': 'Kelly Goff'},
          'dateCreated': p['year'], 'artMedium': p.get('material', ''), 'url': f'{site["baseUrl"]}/{CUR}'}
    desc = f'{p["title"]}, {p["year"]}. ' if p['year'] else f'{p["title"]}. Rendering, not built. ' + ' '.join(x + '.' for x in [p.get('material', '').rstrip('.'), p.get('site', '').rstrip('.')] if x)
    og = ims[0]['src'] if not ims[0]['ph'] else None
    return layout(p['title'], body, desc, active=f'{p.get("back", folder)}/', og=og, ld=ld if p['year'] else None)

def studio_index():
    feat = [p for p in STU if p.get('featured')]; rest = sorted([p for p in STU if not p.get('featured')], key=lambda p: -int(p['year'] or 0))
    yrs = [int(p['year']) for p in rest if p['year']]
    ts = ''.join(tile(p, 'studio') for p in feat)
    more = ''
    if rest:
        more = sec('Selected early works', '', f'{min(yrs)} – {max(yrs)}' if yrs else '') + f'<div class="grid">{"".join(tile(p, "studio") for p in rest)}</div>'
    body = (f'<div class="wrap page-top"><h1>Studio work</h1>'
            f'<p class="lead" style="margin-top:22px">{E(site["studioIntro"])}</p><div class="grid" style="margin-top:40px">{ts}</div>{more}</div>')
    return layout('Studio work', body, 'Studio work by Kelly Goff: research and place-driven sculpture, video and installation.', active='studio/')

def fieldwork_index():
    ts = ''
    for f_ in fw:
        key = f'fw-{f_["slug"]}'
        _l = images_for(key, f_['title'], f'{f_["title"]}, {f_["place"]}')
        im = _l[min(f_.get('thumb', 1), len(_l)) - 1]
        ts += (f'<a class="tile" href="{link(f"fieldwork/{f_["slug"]}/")}"><div class="im">{img_tag(im)}</div>'
               f'<div class="cap"><div class="t">{E(f_["title"])}</div></div></a>')
    intro = ''.join(f'<p class="lead" style="margin-top:{22 if i == 0 else 14}px">{E(t).replace("LineWorks", f"<a href={chr(34)}{link("fieldwork/lineworks/")}{chr(34)}>LineWorks</a>", 1)}</p>' for i, t in enumerate(site["fieldworkIntro"].split("\n\n")))
    body = (f'<div class="wrap page-top"><h1>Fieldwork</h1>{intro}<p class="lead" style="margin-top:14px">I share day-to-day process material on <a href="{E(site["instagram"])}" rel="me noopener">Instagram</a>.</p>'
            f'<div class="grid" style="margin-top:40px">{ts}</div></div>')
    return layout('Fieldwork', body, 'Fieldwork: travel, site research, drawing and rendering, and custom tools. South Korea, Northern France, Bhutan, Nepal, Curaçao, the Ecuadorian Amazon, Alaska, and LineWorks.', active='fieldwork/')

def fieldwork_page(f_, i):
    key = f'fw-{f_["slug"]}'
    ims = images_for(key, f_['title'], f'{f_["title"]}' + (f', {f_["place"]}' if f_['place'] else ''), nph=5)
    hero = ims[0]
    gal = ''.join(f'<figure><button type="button" data-lb="{asset(im["full"])}" data-alt="{E(im["alt"])}" data-cap="{E(f_["title"])}">{img_tag(im, "(max-width:860px) 50vw, 25vw")}</button></figure>' for im in ims)
    rel = ''
    for s in f_.get('related_public', []):
        p = next(x for x in PUB if x['slug'] == s); rel += f'<div class="fact"><div class="k">Related work</div><div class="v"><a href="{link(f"public-work/{s}/")}">{E(p["title"])}, {p["year"]}</a></div></div>'
    for s in f_.get('related_studio', []):
        p = next(x for x in STU if x['slug'] == s); rel += f'<div class="fact"><div class="k">Related work</div><div class="v"><a href="{link(f"studio/{s}/")}">{E(p["title"])}, {p["year"]}</a></div></div>'
    lk = ''.join(f'<div class="fact"><div class="k">Link</div><div class="v"><a href="{E(l["url"])}" rel="noopener">{E(l["label"])}</a></div></div>' for l in f_.get('links', []))
    text = ''.join(f'<p>{re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", lambda m: f"<a href={chr(34)}{m.group(2)}{chr(34)} rel=noopener>{m.group(1)}</a>", E(t))}</p>' for t in f_['text'])
    nxt = fw[i - 1] if i > 0 else None; prv = fw[i + 1] if i < len(fw) - 1 else None
    pager = (f'<nav class="pager" aria-label="More fieldwork"><span>{f"<a href={chr(34)}{link(f"fieldwork/{prv["slug"]}/")}{chr(34)}>← {E(prv["title"])}</a>" if prv else ""}</span>'
             f'<a href="{link("fieldwork/")}">All fieldwork</a><span>{f"<a href={chr(34)}{link(f"fieldwork/{nxt["slug"]}/")}{chr(34)}>{E(nxt["title"])} →</a>" if nxt else ""}</span></nav>')
    if f_.get('layout') == 'project':
        figs = ''.join(f'<figure><button type="button" data-lb="{asset(im["full"])}" data-alt="{E(im["alt"])}" data-cap="{E(f_["title"])}" aria-label="Enlarge image {k + 1} of {len(ims)}" class="ct">{img_tag(im, "(max-width:860px) 100vw, 60vw", eager=(k == 0))}</button></figure>' for k, im in enumerate(ims))
        yr = f'<div class="fact"><div class="k">Year</div><div class="v">{E(f_["date"])}</div></div>' if f_['date'] else ''
        body = (f'<div class="wrap page-top"><div class="crumb"><a href="{link("fieldwork/")}">Fieldwork</a></div><h1 style="margin-top:10px">{E(f_["title"])}</h1>'
                f'<div class="proj"><div class="gal">{figs}</div><aside class="facts" aria-label="Details">{yr}<div class="note">{text}</div>{rel}{lk}</aside></div>{pager}</div>'
                f'<dialog class="lb" id="lb" aria-label="Image viewer"><div class="lb-in"><div class="stage"><img alt=""></div><div class="lb-cap"></div></div>'
                f'<button class="x" type="button">Close</button><button class="pv" type="button" aria-label="Previous image">←</button><button class="nx" type="button" aria-label="Next image">→</button></dialog>')
        return layout(f_['title'], body, f_['text'][0][:155].rsplit(' ', 1)[0] + '…', active='fieldwork/', og=None)
    body = (f'<div class="wrap page-top"><div class="crumb"><a href="{link("fieldwork/")}">Fieldwork</a></div>'
            f'<div class="row-head" style="margin-top:10px"><h1>{E(f_["title"])}</h1><span class="kicker" style="margin:0">{E(f_["date"])}</span></div>'
            f'<div class="twocol" style="margin-top:30px"><div class="prose">{text}</div><div>{('<div class="fact"><div class="k">Place</div><div class="v">' + E(f_["place"]) + '</div></div>') if f_["place"] else ''}{rel}{lk}</div></div>'
            f'<div class="grid" style="margin-top:36px;gap:16px">{gal}</div>{pager}</div>'
            f'<dialog class="lb" id="lb" aria-label="Image viewer"><div class="lb-in"><div class="stage"><img alt=""></div><div class="lb-cap"></div></div>'
            f'<button class="x" type="button">Close</button><button class="pv" type="button" aria-label="Previous image">←</button><button class="nx" type="button" aria-label="Next image">→</button></dialog>')
    return layout(f_['title'], body, f_['text'][0][:155].rsplit(' ', 1)[0] + '…', active='fieldwork/', og=None)

def cv_block(s):
    rows = ''.join(f'<div class="cvrow{"" if y else " nox"}">' + (f'<span class="y">{E(y)}</span>' if y else '') + f'<span>{E(t)}</span></div>' for y, t in s['rows'])
    return f'{sec(s["title"])}{rows}'

def cv_page():
    S = {s['title']: s for s in cv['sections']}
    left = ['Public art', 'Solo and two-person exhibitions', 'Selected group exhibitions', 'Community public art facilitated', 'Awards, grants, and residencies']
    right = ['Education', 'Teaching roles', 'Academic service at Wheaton College', 'Selected professional endeavors', 'Languages']
    body = (f'<div class="wrap page-top"><div class="row-head"><div><h1>Resume</h1><div class="kicker">Born {E(cv["born"].split(" / ")[-1])}, {E(cv["born"].split(" / ")[0])} · Lives and works in {E(site["location"])}</div></div>'
            f'<div class="btns"><a class="btn solid" href="{asset("files/Kelly-Goff-Resume.pdf")}">Resume (PDF) ↓</a><a class="btn" href="{asset("files/Kelly-Goff-Public-Art-Project-List.pdf")}">Public-art project list (PDF) ↓</a></div></div>'
            f'<div class="cv-grid"><div>{"".join(cv_block(S[t]) for t in left)}</div><div>{"".join(cv_block(S[t]) for t in right)}</div></div>'
            f'<div class="cv-press">{cv_block(S["Selected press and bibliography"])}</div></div>')
    return layout('Resume', body, 'Resume of Kelly Goff: public art, exhibitions, awards, education, teaching, and press.', active='resume/')

def about_page():
    vid_id, vid_t = site.get('aboutVideoId', ''), site.get('aboutVideoStart', 0)
    vid = (f'<div class="video yt" data-id="{E(vid_id)}" data-start="{vid_t}"><a href="https://www.youtube.com/watch?v={E(vid_id)}&t={vid_t}s" rel="noopener" aria-label="Play video: public work and process">'
           f'<img src="https://i.ytimg.com/vi/{E(vid_id)}/hqdefault.jpg" alt="" width="480" height="360" loading=lazy><span class="play" aria-hidden="true"></span><span class="yt-note">Watch on YouTube</span></a></div>'
           if vid_id else '<div class="video">Video placeholder — public work and process</div>')
    wi = images_for('wheaton-program', 'Beyond the Rain', site['wheatonProgramImage']['alt'], nph=1)[0]
    wfig2 = f'<figure class="smallfig" style="margin-top:0">{img_tag(wi, "(max-width:860px) 100vw, 40vw")}<figcaption>{E(site["wheatonProgramImage"]["caption"])}</figcaption></figure>'
    paras = ''.join(f'<p>{LW(t)}</p>' for t in site['about'])
    how = f'<div>{sec("How I work")}<div class="prose"><p>{E(site["howIWork"])}</p></div></div>' if site.get('howIWork') else ''
    body = (f'<div class="wrap page-top"><h1>About</h1><div class="twocol" style="margin-top:30px;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr)"><div>{vid}</div><div class="prose">{paras}</div></div>'
            f'<div class="twocol" style="margin-top:56px;grid-template-columns:minmax(0,220px) minmax(0,1fr)"><div>{wfig2}</div>'
            f'<div class="col-first">{how}{sec("Public Art at Wheaton")}<div class="prose"><p>{E(site["wheatonProgram"])}</p></div>'
            f'<div class="btns" style="margin-top:26px"><a class="btn" href="{link("resume/")}">Resume →</a><a class="btn" href="{link("contact/")}">Contact →</a></div></div></div></div>')
    return layout('About', body, ' '.join(site['about'][:1]), active='about/')

def contact_page():
    email = f'<div class="fact"><div class="k">Email</div><div class="v"><a href="mailto:{E(site["email"])}">{E(site["email"])}</a></div></div>' if site.get('email') else ''
    form = (f'<form name="contact" method="POST" action="{link("contact/thanks/")}" data-netlify="true" netlify-honeypot="bot-field">'
            f'<input type="hidden" name="form-name" value="contact"><p class="hp"><label>Leave this empty <input name="bot-field"></label></p>'
            f'<div class="field"><label for="n">Name</label><input id="n" name="name" required autocomplete="name"></div>'
            f'<div class="field"><label for="e">Email</label><input id="e" name="email" type="email" required autocomplete="email"></div>'
            f'<div class="field"><label for="o">Organization / call</label><input id="o" name="organization"></div>'
            f'<div class="field"><label for="m">Message</label><textarea id="m" name="message" required></textarea></div>'
            f'<div style="margin-top:20px"><button class="btn solid" type="submit">Send</button></div></form>')
    body = (f'<div class="wrap page-top"><h1>Contact</h1><div class="twocol" style="margin-top:30px;gap:80px"><div><p class="lead">{E(site["contactIntro"])}</p>'
            f'<div style="margin-top:34px">{email}<div class="fact"><div class="k">Instagram</div><div class="v"><a href="{E(site["instagram"])}" rel="me noopener">@kellygoffstudio</a></div></div>'
            f'<div class="fact"><div class="k">Studio</div><div class="v">{E(site["location"])}</div></div>'
            f'<div class="fact"><div class="k">Downloads</div><div class="v"><a href="{asset("files/Kelly-Goff-Public-Art-Project-List.pdf")}">Public-art project list (PDF)</a> · <a href="{asset("files/Kelly-Goff-Resume.pdf")}">Resume (PDF)</a></div></div></div></div>'
            f'<div>{form}</div></div></div>')
    return layout('Contact', body, site['contactIntro'], active='contact/')

def thanks_page():
    body = (f'<div class="wrap page-top"><h1>Thank you</h1><p class="lead" style="margin-top:22px">Your message was sent. I’ll reply as soon as I can.</p>'
            f'<div class="btns" style="margin-top:30px"><a class="btn solid" href="{link("")}">Back to the work</a></div></div>')
    return layout('Thank you', body, noindex=True, active='contact/')

def notfound_page():
    body = (f'<div class="wrap page-top"><h1>Page not found</h1><p class="lead" style="margin-top:22px">That page has moved or never existed.</p>'
            f'<div class="btns" style="margin-top:30px"><a class="btn solid" href="{link("public-work/")}">Public work</a><a class="btn" href="{link("")}">Home</a></div></div>')
    return layout('Page not found', body, noindex=True)

# ---------------------------------------------------------------- build
def main():
    global CUR
    if OUT.exists(): shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    shutil.copytree(ROOT / 'src/css', OUT / 'assets/css'); shutil.copytree(ROOT / 'src/js', OUT / 'assets/js'); shutil.copytree(ROOT / 'src/fonts', OUT / 'assets/fonts'); shutil.copytree(ROOT / 'src/media', OUT / 'assets/media')
    page('', home)
    page('public-work/', public_index)
    pl = sorted(PUB, key=lambda p: (-int(p['year'][:4]), p['title']))
    for p in pl: page(f'public-work/{p["slug"]}/', lambda p=p: project_page(p, 'public-work', 'Public work', pl))
    for p in RD: page(f'public-work/renderings/{p["slug"]}/', lambda p=p: project_page(p, 'public-work/renderings', 'Public work', RD))
    page('studio/', studio_index)
    sl = [p for p in STU if p.get('featured')] + [p for p in STU if not p.get('featured')]
    for p in sl: page(f'studio/{p["slug"]}/', lambda p=p: project_page(p, 'studio', 'Studio work', sl))
    page('fieldwork/', fieldwork_index)
    for i, f_ in enumerate(fw): page(f'fieldwork/{f_["slug"]}/', lambda f_=f_, i=i: fieldwork_page(f_, i))
    page('resume/', cv_page); page('about/', about_page); page('contact/', contact_page); page('contact/thanks/', thanks_page)
    CUR = ''
    if MODE == 'prod':
        (OUT / '404.html').write_text(notfound_page(), encoding='utf8')
        urls = ''.join(f'<url><loc>{site["baseUrl"]}/{p}</loc></url>' for p in PAGES if p != 'contact/thanks/')
        (OUT / 'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
        (OUT / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {site["baseUrl"]}/sitemap.xml\n')
        red = ['/outdoors  /public-work/  301', '/indoors  /studio/  301', '/about  /about/  301', '/process  /fieldwork/  301', '/process/*  /fieldwork/:splat  301', '/research  /fieldwork/  301', '/research/*  /fieldwork/:splat  301', '/passage  /studio/crates/  301', '/cv  /resume/  301']
        old = {'sandbags': 'sandbags', 'waters': 'waters', 'reef': 'reef', 'drum': 'drum', 'coconuts': 'coconuts-2019', 'barrel': 'barrel', 'souvenir-1': 'souvenir-1',
               'beacon': None, 'two-views': 'two-views', 'crates': 'crates', 'dumpster': 'dumpster', 'muffler': 'muffler', 'containers': 'containers', 'accident': 'accident',
               'ghost': 'ghost', 'hole': 'hole', 'tree': 'tree', 'coconuts-1': 'coconuts-2016'}
        for o, n in old.items(): red.append(f'/{o}/  /{"public-work/beacon" if n is None else "studio/" + n}/  301')
        (OUT / '_redirects').write_text('\n'.join(red) + '\n')
        (OUT / '_headers').write_text('/assets/*\n  Cache-Control: public, max-age=31536000, immutable\n/img/*\n  Cache-Control: public, max-age=31536000, immutable\n')
    (OUT / 'files').mkdir(exist_ok=True)
    for f in (ROOT / 'src/files').glob('*.pdf'): shutil.copy(f, OUT / 'files' / f.name)
    print(f'{MODE}: {len(PAGES)} pages -> {OUT}')
    if PLACEHOLDERS_USED: print('placeholders for', len(PLACEHOLDERS_USED), 'image folders')

if __name__ == '__main__':
    main()
