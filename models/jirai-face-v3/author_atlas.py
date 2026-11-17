"""Surface-owned face color: crisp iris, clean bangs, fine separate brows."""
from common import *
import numpy as np
import cv2
from PIL import Image

d = np.load(ROOT/'surface.npz'); old=d['old_positions']; p=d['positions']; c=d['components']
uv=d['uv']; lv=d['loop_vertices']; lt=d['loop_triangles']; mt=d['materials']
native_uv=uv.copy();native_uv[:,0]=uv[:,0].astype('<f2').astype(float)
native_uv[:,1]=1-(1-uv[:,1]).astype('<f2').astype(float)
source=REPO/'private/fishnet-v1/T_Jirai_Base.png'
im=np.array(Image.open(source).convert('RGB')); out=im.copy(); H,T=im.shape[:2]
face2=np.array(Image.open(REPO/'private/jirai-face-v2/T_Jirai_Base.png').convert('RGB'))
mask=np.zeros((H,T),np.uint8); counts={}

def smooth(x):
    x=np.clip(x,0,1); return x*x*(3-2*x)

def patches(wanted):
    for ls,material in zip(lt,mt):
        vi=lv[ls]; cid=int(c[vi[0]])
        if cid not in wanted: continue
        pts=old[vi]
        if pts[:,2].max()<170 or pts[:,2].min()>190: continue
        q=native_uv[ls]*[T-1,H-1]; q[:,1]=H-1-q[:,1]
        lo=np.floor(q.min(0)).astype(int).clip(0,[T-1,H-1]); hi=np.ceil(q.max(0)).astype(int).clip(0,[T-1,H-1])
        a=np.column_stack([q[0]-q[2],q[1]-q[2]])
        if abs(np.linalg.det(a))<1e-8: continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(a).T; b=np.dstack([b,1-b.sum(-1)])
        inside=(b>=-1e-5).all(-1)
        original_uv=(b@uv[ls])[inside]
        yield cid,xx[inside],yy[inside],(b@pts)[inside],original_uv

def iris_color(q,cx):
    x=(q[:,0]-cx)/1.67; z=(q[:,2]-177.799362)/1.89
    r=np.sqrt(x*x+z*z); theta=np.arctan2(z,x)
    # Warm orange/red body with darker upper hemisphere and a narrow limbal ring.
    color=np.column_stack([249-76*smooth((z+.1)/.9), 67+118*smooth((-z+.25)/1.2), 68+91*smooth((-z+.15)/1.1)])
    rays=(np.sin(theta*43+.7*np.sin(theta*11))+0.5*np.sin(theta*79+2.3))
    rays*=smooth((r-.25)/.3)*(1-smooth((r-.88)/.11))
    color+=rays[:,None]*np.array([2,4,3])
    gold=np.exp(-((r-.62)/.022)**2)*.45
    color=color*(1-gold[:,None])+np.array([211,94,69])*gold[:,None]
    pupil=np.sqrt((x/.255)**2+((z-.08)/.36)**2)
    a=1-smooth((pupil-.88)/.10)
    color=color*(1-a[:,None])+np.array([222,57,39])*a[:,None]
    ring=np.exp(-((pupil-.91)/.06)**2)*.85
    color=color*(1-ring[:,None])+np.array([112,43,35])*ring[:,None]
    rim=smooth((r-.96)/.035)
    color=color*(1-rim[:,None])+np.array([86,18,32])*rim[:,None]
    # Small painted catchlights, not protruding polygon fragments.
    for hx,hz,rx,rz in [(.38,.47,.19,.105),(-.31,.64,.055,.085),(.43,-.57,.045,.07),(-.47,-.64,.035,.045)]:
        e=np.sqrt(((x-hx)/rx)**2+((z-hz)/rz)**2)
        a=1-smooth((e-.85)/.12)
        color=color*(1-a[:,None])+np.array([255,249,239])*a[:,None]
    return np.clip(color,0,255)

for cid,x,y,q,source_uv in patches({0,19,56,101,102}):
    a=np.zeros(len(x)); rgb=im[y,x].astype(float)
    if cid in [51,52]:
        rgb=iris_color(q,-5.317217 if cid==51 else 4.614422);a[:]=1
    elif cid==19:
        source_xy=np.rint(source_uv*8191).astype(int)
        rgb=face2[8191-source_xy[:,1],source_xy[:,0]].astype(float)
        # Subtle longitudinal silver strand shading across the previously
        # flat repaired lower fringe; retain the existing pink streak.
        phase=q[:,0]*33+.075*(q[:,2]-183)**2
        strand=np.maximum(0,np.cos(phase))**12
        broad=np.sin(q[:,0]*7+.08*(q[:,2]-183))
        amount=(strand*7+broad*2)*smooth((186-q[:,2])/2)
        rgb-=amount[:,None]*np.array([.65,.65,.75]); a[:]=1
    elif cid in [101,102]:
        rgb[:]=[87,61,68];a[:]=1
    elif cid==0:
        # Remove the baked broad brow stamp from forehead skin; the separate
        # narrowed eyebrow geometry supplies the fine line behind the bangs.
        a=smooth((q[:,2]-181.3)/.3)*smooth((182.8-q[:,2])/.3)
        a*=smooth((8.3-np.abs(q[:,0]+.35))/.4)*smooth((np.abs(q[:,0]+.35)-2.1)/.4)
        a*=(q[:,1]<-.5)
        rgb[:]=[247,222,221]
        # Nasal socket backing is skin; remove the thick baked red/black band
        # left beside the new true eye white, with a feathered skin transition.
        for cx,sign in [(-5.317217,1),(4.614422,-1)]:
            dx=(q[:,0]-cx)*sign;dz=q[:,2]-177.65
            a=np.maximum(a,smooth((dx-2.02)/.26)*smooth((2.88-dx)/.22)
                *smooth((1.15-np.abs(dz))/.30)*(q[:,1]<-.3))
        lashes=smooth((q[:,2]-178.0)/.15)*smooth((179.85-q[:,2])/.2)
        lashes*=smooth((8.95-np.abs(q[:,0]+.35))/.25)*smooth((np.abs(q[:,0]+.35)-2.6)/.2)
        lashes*=smooth((174-im[y,x].mean(1))/35)*(q[:,1]<-.5)
        rgb=np.where((lashes>0)[:,None],np.array([39,22,28]),rgb)
        a=np.maximum(a,lashes)
    if cid in [0,56]:
        # Retain lip color but remove near-black fragmented seam texels.
        xmouth=q[:,0]+.35;curve=171.65+.085*xmouth*xmouth
        am=smooth((2.15-np.abs(xmouth))/.3)*smooth((.48-np.abs(q[:,2]-curve))/.15)*(q[:,1]<-2.5)
        if cid==0:
            am=np.maximum(am,smooth((2.65-np.abs(xmouth))/.2)*smooth((q[:,2]-170.4)/.20)*smooth((172.5-q[:,2])/.2)*(q[:,1]<.5))
        if cid==56:am=np.ones(len(x))
        if np.any(am>0):
            line=np.exp(-((q[:,2]-(171.65 if cid==56 else curve))/(.14 if cid==56 else .065))**2)
            lip=np.array([245,205,205])[None]*(1-line[:,None])+np.array([166,103,111])[None]*line[:,None]
            current=rgb.copy();rgb=np.where((am>0)[:,None],lip,current)
            a=np.maximum(a,am)
    ok=a>0
    if not ok.any(): continue
    xx=x[ok];yy=y[ok];alpha=a[ok,None]
    out[yy,xx]=np.rint(im[yy,xx]*(1-alpha)+rgb[ok]*alpha).clip(0,255).astype(np.uint8)
    mask[yy,xx]=255;counts[str(cid)]=counts.get(str(cid),0)+int(ok.sum())

# Pad only into unused UV space so mips do not reintroduce the old rim.
occupied=np.zeros((H,T),np.uint8)
for ls,material in zip(lt,mt):
    if material not in [0,1,18]: continue
    q=native_uv[ls]*[T-1,H-1];q[:,1]=H-1-q[:,1]
    cv2.fillConvexPoly(occupied,np.rint(q).astype(np.int32),255)
edge=(mask>0).astype(np.uint8)
dist,labels=cv2.distanceTransformWithLabels(1-edge,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
pad=(dist<=8)&(occupied==0)&(labels>0)&(mask==0)
out[pad]=out[edge>0][labels[pad]-1];mask[pad]=255
changed=np.any(out!=im,axis=2)
assert np.all(mask[changed]>0)
Image.fromarray(out).save(ROOT/'T_Jirai_Base.png')
Image.new('RGB',(64,64),(255,140,0)).save(ROOT/'T_Face3_EyeMix.png')
# A dedicated planar iris UV avoids the 8K shared atlas's half-float UV
# quantization, which previously distorted the pupil and highlight shapes.
yy,xx=np.meshgrid(np.linspace(1,-1,1024),np.linspace(-1,1,1024),indexing='ij')
points=np.column_stack([xx.ravel()*1.67, np.zeros(xx.size),177.799362+yy.ravel()*1.89])
Image.fromarray(np.rint(iris_color(points,0)).astype(np.uint8).reshape(1024,1024,3)).save(ROOT/'T_Face3_Iris.png')
Image.fromarray(mask).save(ROOT/'repair-mask.png')
write(ROOT/'atlas-report.json',dict(source_sha256=sha(source),output_sha256=sha(ROOT/'T_Jirai_Base.png'),
    changed_pixels=int(changed.sum()),surface_sha256=sha(ROOT/'surface.npz'),samples=counts,
    isolated_material_slots=[0,1,18],shared_original_atlas_not_replaced=True,
    no_face2_white_skin_overlay=True,game_runtime_tested=False))
print('FACE3_ATLAS_AUTHORED',int(changed.sum()))
