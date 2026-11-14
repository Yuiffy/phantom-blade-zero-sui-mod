"""Same-height reference/v7/v8 comparison; no independent width rescaling."""
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
import numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'delivery';OUT.mkdir(exist_ok=True)
ART=ROOT.parent/'single-image-trial-v1/sui-front-input.png'
def foreground(im,bg,tol):
 a=np.asarray(im.convert('RGB')).astype(int);near=np.max(np.abs(a-np.array(bg)),axis=2)<=tol
 work=Image.fromarray((near*255).astype('uint8')).copy();ImageDraw.floodfill(work,(0,0),128)
 mask=np.asarray(work)!=128
 labs,n=label(mask);sizes=np.bincount(labs.ravel());sizes[0]=0
 return labs==sizes.argmax()
def landmarks(mask):
 ys,xs=np.where(mask);top=int(ys.min());bottom=int(ys.max())
 band=mask[top+int(.6*(bottom-top)):top+int(.8*(bottom-top))]
 bx=np.where(band.any(axis=0))[0];cx=float((bx.min()+bx.max())/2)
 return {'hair_top':top,'sole':bottom,'axis_x':cx,'height_px':bottom-top}
font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
panels=[];land={};profiles={}
for tag,path,bg,tol in [('参考立绘',ART,(255,255,255),18),('v7',ROOT/'shots/v7-front.png',(98,102,109),15),('v8',ROOT/'shots/v8-front.png',(98,102,109),15)]:
 im=Image.open(path).convert('RGB');mask=foreground(im,bg,tol);lm=landmarks(mask);land[tag]=lm
 scale=900/lm['height_px'];size=(round(im.width*scale),round(im.height*scale))
 rgb=im.resize(size,Image.Resampling.LANCZOS);alpha=Image.fromarray((mask*255).astype('uint8')).resize(size,Image.Resampling.LANCZOS)
 panel=Image.new('RGB',(660,1035),(122,124,130));panel.paste(rgb,(round(330-lm['axis_x']*scale),round(80-lm['hair_top']*scale)),alpha)
 d=ImageDraw.Draw(panel);d.text((18,15),tag,font=font,fill='white')
 for frac,lab in [(0,'发顶'),(.20,'上身 20%'),(.45,'45%'),(1,'脚底')]:
  y=80+round(900*frac);d.line((0,y,659,y),fill=(175,178,185));d.text((8,y+3),lab,font=small,fill=(235,235,235))
 profiles[tag]={}
 for frac in [.20,.23,.27,.35,.42]:
  row=mask[lm['hair_top']+round(lm['height_px']*frac)];xs=np.flatnonzero(row)
  profiles[tag][str(frac)]=float((xs.max()-xs.min()+1)/lm['height_px'])
 panels.append(panel)
sheet=Image.new('RGB',(1996,1035),(25,27,32))
for i,p in enumerate(panels):sheet.paste(p,(668*i,0))
sheet.save(OUT/'reference-v7-v8-proportions.jpg',quality=95)
upper=Image.new('RGB',(1528,820),(25,27,32));d=ImageDraw.Draw(upper)
for i,tag in enumerate(['v7','v8']):
 im=Image.open(ROOT/f'shots/{tag}-upper.png');upper.paste(im,(i*768,55));d.text((i*768+18,10),tag+' · 同镜头、同尺寸',font=font,fill='white')
upper.save(OUT/'v7-v8-collar-shoulders.jpg',quality=95)
(ROOT/'art-comparison.json').write_text(json.dumps({'landmarks':land,'width_over_height_profiles_including_sleeves_bag':profiles,'method':'largest connected foreground component; one uniform scale per panel, hair-top/sole aligned; widths never independently scaled; halo omitted'},indent=2,ensure_ascii=False),encoding='utf8')
print(json.dumps(profiles))
