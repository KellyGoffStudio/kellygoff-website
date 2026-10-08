import sys,os,glob,io
from playwright.sync_api import sync_playwright
from PIL import Image,ImageDraw,ImageFont
D=os.path.abspath(sys.argv[1]); out=sys.argv[2]; VW=900; SC=1.5
DPI=200; SW,SH=11*DPI,int(8.5*DPI); M=int(.45*DPI); G=int(.5*DPI); HB=int(.3*DPI)
CW=(SW-2*M-G)//2; CH=SH-2*M-HB
pages=[p for p in glob.glob(D+'/**/index.html',recursive=True) if '/files/' not in p and '/assets/' not in p]
order=['','public-work','studio','fieldwork','cv','about','contact']
def key(p):
    r=os.path.relpath(os.path.dirname(p),D); r='' if r=='.' else r; t=r.split('/')[0]
    return (order.index(t) if t in order else 99,r)
pages.sort(key=key)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',30)
fs=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',22)
slices=[]  # (label, image)
with sync_playwright() as pw:
    b=pw.chromium.launch(); pg=b.new_page(viewport={'width':VW,'height':800},device_scale_factor=SC)
    for n,p in enumerate(pages,1):
        pg.goto('file://'+p); pg.wait_for_timeout(150)
        pg.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')"); pg.wait_for_timeout(400)
        im=Image.open(io.BytesIO(pg.screenshot(full_page=True))).convert('RGB')
        s=CW/im.width; im=im.resize((CW,int(im.height*s)),Image.LANCZOS)
        r=os.path.relpath(os.path.dirname(p),D); r='/' if r=='.' else '/'+r+'/'
        k=max(1,-(-im.height//CH)); step=-(-im.height//k)
        for j in range(k):
            sl=im.crop((0,j*step,CW,min(im.height,(j+1)*step)))
            slices.append((f'p.{n}{"" if k==1 else f" ({j+1}/{k})"}   {r}',sl))
    b.close()
sheets=[]
for a in range(0,len(slices),2):
    S=Image.new('RGB',(SW,SH),'white'); d=ImageDraw.Draw(S)
    for c,(lab,sl) in enumerate(slices[a:a+2]):
        x=M+c*(CW+G); d.text((x,M-4),lab,fill='#1d1f20',font=f)
        S.paste(sl,(x,M+HB)); d.rectangle([x-1,M+HB-1,x+CW,M+HB+sl.height],outline='#999')
    d.text((SW//2-120,SH-M+8),f'sheet {a//2+1}',fill='#888',font=fs)
    sheets.append(S)
sheets[0].save(out,save_all=True,append_images=sheets[1:],resolution=DPI,quality=55)
print(len(pages),'pages',len(slices),'slices',len(sheets),'sheets',os.path.getsize(out)/1e6,'MB')
