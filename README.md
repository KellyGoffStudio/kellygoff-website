# kellygoff.net — static site

Everything on the site is generated from the files in `data/`. No database, no plugins.

## Edit content
- `data/projects.json` — public work (`public`) and studio work (`studio`). Empty fields are hidden on the page.
- `data/fieldwork.json`, `data/cv.json`, `data/site.json` (tagline, About text, email, Instagram, intros).
- Add a project: copy an existing entry, give it a new `slug`, fill in the fields.

## Add photos
1. Put photos in `images/<slug>/` named so they sort in order (`01-hero.jpg`, `02-detail.jpg`…). First = hero.
   Fieldwork uses `images/fw-<slug>/`, About uses `images/about/`.
2. Optional `images/<slug>/meta.json`: `{"02-detail.jpg": {"alt": "...", "caption": "..."}}`
3. `python3 tools/images.py` (makes WebP sizes in `processed/`; needs Pillow).

## Build
- Preview (works from any folder, noindex): `python3 tools/build.py --preview` → `dist-preview/`
- Production: `python3 tools/build.py` → `dist/` (sitemap, robots, redirects from the old Squarespace URLs, 404, contact form)
- PDFs (CV, project list): `python3 tools/pdfs.py dist/files` (needs Playwright + Chromium)
Needs Python 3.12+.

## Deploy
Drag `dist/` into Netlify (or connect the folder to Cloudflare Pages). The contact form uses Netlify Forms; add your email in `data/site.json`.
Point the domain at the host only when you are happy; the Squarespace site stays live until then.
