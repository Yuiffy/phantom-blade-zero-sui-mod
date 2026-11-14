"""Clear projected shirt/armband colors on the right coat and bag inner panel."""
from pathlib import Path
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='2'
import numpy as np,json,hashlib
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parent;BASE=R.parent/'tripo-refine-v9/textures/sui-jk-albedo-v9.png'
d=np.load(R/'atlas-provenance.npz');co=d['co'];faces=d['faces'];uv=d['uv'];mi=d['mi'];c=d['comp'][faces[:,0]];fc=co[faces].mean(axis=1)
rgb=np.array(Image.open(BASE).convert('RGB'));orig=rgb.copy();H,W=rgb.shape[:2];reports=[]
def surface(mask):
 canvas=Image.new('I',(W,H),0);draw=ImageDraw.Draw(canvas)
 for i in np.flatnonzero(mask&(mi==0)):draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in uv[i]],fill=int(i)+1)
 yy,xx=np.nonzero(np.asarray(canvas));fi=np.asarray(canvas)[yy,xx]-1;t=uv[fi];q=np.column_stack(((xx+.5)/W,1-(yy+.5)/H));a=t[:,0];b=t[:,1]-a;cc=t[:,2]-a;v=q-a;det=b[:,0]*cc[:,1]-b[:,1]*cc[:,0];det=np.where(abs(det)<1e-12,1,det)
 s=(v[:,0]*cc[:,1]-v[:,1]*cc[:,0])/det;r=(b[:,0]*v[:,1]-b[:,1]*v[:,0])/det
 p=co[faces[fi,0]]*(1-s-r)[:,None]+co[faces[fi,1]]*s[:,None]+co[faces[fi,2]]*r[:,None]
 return yy,xx,p
allowed=np.zeros((H,W),bool)
def repair(name,mask,classify,source_filter=None,uniform=False):
 yy,xx,p=surface(mask);col=orig[yy,xx].astype(float);bad=classify(col,p);good=(col[:,0]>130)&(col[:,1]<col[:,0]*.55)&(col[:,1]>col[:,0]*.23)&(col[:,2]>col[:,0]*.4)&(col[:,2]<col[:,0]*.82)&~bad
 if source_filter is not None:good&=source_filter(p)
 assert good.sum()>20
 if bad.sum():
  dist,ii=cKDTree(p[good]).query(p[bad],k=16,workers=1);wt=1/np.maximum(dist,.10)**2;wt/=wt.sum(axis=1,keepdims=True)
  fill=np.tile(np.median(col[good],axis=0),(int(bad.sum()),1)) if uniform else (col[good][ii]*wt[:,:,None]).sum(axis=1)
  rgb[yy[bad],xx[bad]]=np.clip(np.round(fill),0,255).astype('uint8')
 allowed[yy,xx]=True
 reports.append({'region':name,'surface_pixels':len(yy),'repaired_pixels':int(bad.sum()),'bad_3d_bounds':[p[bad].min(axis=0).tolist(),p[bad].max(axis=0).tolist()] if bad.any() else None})
repair('right rear and side cardigan projected shirt/armband patches',(c==0)&(fc[:,0]<-7)&(fc[:,0]>-32)&(fc[:,1]>-8)&(fc[:,2]>125)&(fc[:,2]<149),lambda c,p:((c.min(axis=1)>90)&((c.max(axis=1)-c.min(axis=1))<65))|(c[:,2]>c[:,0]*.80)|(c[:,0]<95))
repair('backpack body-facing panel repainted from clean pink rim',(c==7)&(fc[:,1]<24),lambda c,p:p[:,1]<16.8,lambda p:p[:,1]>18,uniform=True)
changed=np.any(rgb!=orig,axis=2);assert not (changed&~allowed).any()
canvas=Image.new('1',(W,H),0);draw=ImageDraw.Draw(canvas)
for t in uv[mi==0]:draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in t],fill=1)
dist,idx=distance_transform_edt(~changed,return_indices=True);pad=(dist<=4)&~np.asarray(canvas).astype(bool)&~changed
rgb[pad]=rgb[idx[0][pad],idx[1][pad]]
yy,xx,_=surface((fc[:,2]>155)|np.isin(c,[4,5,9,10,100,101]));assert np.array_equal(rgb[yy,xx],orig[yy,xx])
changed=np.any(rgb!=orig,axis=2);assert changed.sum()<800000
out=R/'textures/sui-jk-albedo-v10.png';out.parent.mkdir(exist_ok=True);Image.fromarray(rgb).save(out)
report={'baseline_sha256':hashlib.sha256(BASE.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'changed_pixels':int(changed.sum()),'padding_pixels':int(pad.sum()),'regions':reports,'head_hands_skirt_and_v9_ornaments_UV_interiors_exactly_unchanged':True,'no_claim_of_separate_shirt_layer':True}
(R/'atlas-repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
