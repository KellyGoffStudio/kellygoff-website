#!/usr/bin/env python3
"""Turn the photos in images/<slug>/ into web-ready WebP files in processed/<slug>/.

Usage:  python3 tools/images.py

Put photos for a project in images/<slug>/ (the slug is in data/projects.json), named so they sort in the
order you want: 01-hero.jpg, 02-detail.jpg, 03-context.jpg ...  The first one is the hero image.
Fieldwork entries use images/fw-<slug>/ (for example images/fw-alaska/), About uses images/about/.
Optional: images/<slug>/meta.json  {"02-detail.jpg": {"alt": "...", "caption": "..."}}
"""
import json, os, sys
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw, ImageFont

FONT = Path(__file__).resolve().parent / 'fonts' / 'BarlowCondensed-600.ttf'

def overlay(im, text='RENDERING'):
    """Bake a large white label at 30% opacity into the lower-left corner (Barlow Condensed SemiBold).
    Sized from the image width so it reads the same at every size: text spans ~31% of the width."""
    w, h = im.size
    target = 0.31 * w
    size = 100
    f = ImageFont.truetype(str(FONT), size)
    bb = f.getbbox(text)
    size = max(8, round(size * target / (bb[2] - bb[0])))
    f = ImageFont.truetype(str(FONT), size)
    bb = f.getbbox(text)
    x = round(0.023 * w) - bb[0]
    y = h - round(0.04 * h) - bb[3]
    lay = Image.new('RGBA', im.size, (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((x, y), text, font=f, fill=(255, 255, 255, round(255 * 0.30)))
    return Image.alpha_composite(im.convert('RGBA'), lay).convert('RGB')

ROOT = Path(__file__).resolve().parent.parent
SRC, DST = ROOT / 'images', ROOT / 'processed'
WIDTHS = [int(x) for x in os.environ.get('KG_WIDTHS', '480,960,1600,2400').split(',')]
EXT = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}

def main():
    manifest = {}
    if not SRC.exists():
        print('no images/ folder yet'); return
    jobs = []
    for d in sorted(p for p in SRC.iterdir() if p.is_dir() and not p.name.startswith('.')):
        jobs.append((d, d.name, False))
        if d.name.startswith('rd-'): jobs.append((d, 'rdo-' + d.name[3:], True))   # renderings: clean set for thumbnails, labeled set for pages
    for d, outname, label in jobs:
        files = sorted(f for f in d.iterdir() if f.suffix.lower() in EXT)
        out = []
        for f in files:
            try:
                im = Image.open(f); im = ImageOps.exif_transpose(im)
            except Exception as e:
                print('skip', f, e); continue
            if im.mode not in ('RGB', 'L'): im = im.convert('RGB')
            w, h = im.size
            WS = [900, 1500, 2000] if d.name == 'home' else WIDTHS
            ws = [x for x in WS if x < w] + [w if w <= WS[-1] else WS[-1]]
            ws = sorted(set(ws))
            od = DST / outname; od.mkdir(parents=True, exist_ok=True)
            for tw in ws:
                target = od / f'{f.stem}-{tw}.webp'
                if target.exists() and target.stat().st_mtime >= max(f.stat().st_mtime, Path(__file__).stat().st_mtime if label else 0): continue
                th = round(h * tw / w)
                r = im.resize((tw, th), Image.LANCZOS)
                if label: r = overlay(r)
                r.save(target, 'WEBP', quality=int(os.environ.get('KG_Q', '82')), method=6)
            out.append({'name': f.stem, 'w': w, 'h': h, 'widths': ws})
        if out:
            manifest[outname] = out
            print(f'{outname}: {len(out)} images')
    DST.mkdir(exist_ok=True)
    (DST / 'manifest.json').write_text(json.dumps(manifest, indent=1))
    print('done:', sum(len(v) for v in manifest.values()), 'images in', len(manifest), 'folders')

if __name__ == '__main__':
    main()
