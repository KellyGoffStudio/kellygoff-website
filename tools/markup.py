import sys,os,glob,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageFont
D=os.path.abspath(sys.argv[1]); out=sys.argv[2]; W=1100
pages=sorted(glob.glob(D+'/**/index.html',recursive=True))
def key(p):
    r=os.path.relpath(os.path.dirname(p),D); r='' if r=='.' else r
    top=r.split('/')[0]; order=['','public-work','studio','fieldwork','cv','about','contact']
    return (order.index(top) if top in order else 99, r)
pages=sorted([p for p in pages if '/files/' not in p and '/assets/' not in p],key=key)
ims=[];labels=[]
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={'width':W,'height':800})
    for p in pages:
        pg.goto('file://'+p); pg.wait_for_timeout(150)
        pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
        pg.wait_for_timeout(400)
        im=Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert('RGB')
        ims.append(im); r=os.path.relpath(os.path.dirname(p),D); labels.append('/' if r=='.' else '/'+r+'/')
    b.close()
try: f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',22)
except: f=ImageFont.load_default()
pp=[]
for n,(im,l) in enumerate(zip(ims,labels),1):
    bar=44; c=Image.new('RGB',(im.width,im.height+bar),'#1d1f20'); c.paste(im,(0,bar))
    ImageDraw.Draw(c).text((14,9),f'p.{n}   {l}   (Kelly Goff site, markup copy)',fill='white',font=f); pp.append(c)
pp[0].save(out,save_all=True,append_images=pp[1:],resolution=110,quality=45)
print(len(pp),os.path.getsize(out)/1e6,'MB')
open(out+'.txt','w').write('\n'.join(f'p.{i+1} {l}' for i,l in enumerate(labels)))
