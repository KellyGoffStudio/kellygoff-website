import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
R=Path(sys.argv[1]).resolve(); pages=sys.argv[2:]
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for spec in pages:
        name,w=spec.split('@') if '@' in spec else (spec,'1440')
        p=R/name/'index.html' if name else R/'index.html'
        pg=b.new_page(viewport={'width':int(w),'height':900}); msgs=[]
        pg.on('console',lambda m: msgs.append(m.text) if m.type in('error','warning') else None)
        pg.on('pageerror',lambda e: msgs.append(str(e)))
        pg.goto('file://'+str(p)); pg.wait_for_timeout(400)
        out=Path('/tmp/shots'); out.mkdir(exist_ok=True)
        fn=out/(((name or 'home').replace('/','_'))+f'_{w}.png'); pg.screenshot(path=str(fn),full_page=True); print(fn,msgs)
        pg.close()
    b.close()
