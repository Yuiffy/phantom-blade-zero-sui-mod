"""Compare front, oblique and rear coverage under motion and the same lift input."""
import runpy
import sys
import numba
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
rear=Path(__file__).resolve().parents[1]/'jk-skirt-rear-v1'
sys.path.insert(0,str(rear))
render=runpy.run_path(str(rear/'coverage.py'))
from skirt import CODE,WORK,PERF,read,write,decode,common,sha

def review():
    textures=[]
    texroot=PERF.parent/'outfit-patterns-v1'
    from pathlib import Path
    for material in read(texroot/'preview-materials.json')['jk']:
        path=Path(material['path'])
        if path.name=='jk-before.png':
            path=texroot/'jk-after.png'
        with Image.open(path) as im:
            textures.append(np.array(im.convert('RGB').resize((1024,1024))))
    uv=np.load(PERF.parent/'jk-face-shape-v1/final.npz')['uv'][:,0]
    out=WORK/'preview'
    out.mkdir(exist_ok=True)
    stats={}
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    sheet=Image.new('RGB',(340*4,355*2),'white')
    draw=ImageDraw.Draw(sheet)
    for j,(label,src,doc) in enumerate([('上版',PERF/'reduced-full','before'),('修正版',WORK/'replay','final')]):
        s=decode(read(WORK/'native'/f'{doc}.json'))[3]['sections'][14]
        alpha=1-np.array(s['cloth_maps'][0]['source'])[:,3]/65535
        with np.load(src/'jog-60-surface.npz') as d:
            frames,times=d['frames'],d['times']
            ids=np.searchsorted(d['ids'],np.arange(s['base_vertex'],s['base_vertex']+len(alpha)))
            uvpart=uv[d['ids']]
            for i,(t,lift,angle,title) in enumerate([(0,32,180,'正面上拉'),(0,32,145,'斜前上拉'),(2.67,0,180,'跑步'),(15.5,0,180,'停下后')]):
                frame=frames[np.argmin(abs(times-t))].copy()
                frame[ids,2]+=lift*alpha
                panel=render['picture'](d,frame,angle,98,textures,uvpart)
                sheet.paste(panel.crop((0,5,340,332)),(340*i,355*j+28))
                draw.text((340*i+8,355*j+2),label+' · '+title,font=font,fill='black')
                if lift:
                    stats[f'{doc}-{angle}']=render['view'](frame,d['faces'],d['materials'],angle,200,98)[2]
                    if angle==180:
                        for a in [0,38,-145]:
                            stats[f'{doc}-{a}']=render['view'](frame,d['faces'],d['materials'],a,200,98)[2]
    sheet.save(out/'front-comparison.jpg',quality=92)
    write(WORK/'coverage.json',dict(visible_shorts_pixels=stats,artificial_lift_cm=32,preview_sha256=sha(out/'front-comparison.jpg')))
    print(stats)

if __name__=='__main__':
    review()
