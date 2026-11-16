"""Geometry-scoped deterministic UV restoration; preserve all other pixels."""
from pathlib import Path
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='2'
import numpy as np,json,hashlib
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
from scipy.ndimage import binary_dilation,distance_transform_edt
ROOT=Path(__file__).resolve().parent
D=np.load(ROOT/'inspect-data.npz');co,faces,uv,comp=D['co'],D['faces'],D['uv'],D['comp']
SRC=next((ROOT.parent/'tripo-refine-v8/source').rglob('*.jpg'))
im=Image.open(SRC).convert('RGB');rgb=np.array(im);original=rgb.copy();H,W=rgb.shape[:2]
fc=co[faces].mean(axis=1);c=comp[faces[:,0]]
reports=[]
# Rasterize surface ownership before editing. Nearest clean samples are queried
# in 3D so disconnected UV islands do not borrow colors from unrelated parts.
def surface(mask):
 ids=np.flatnonzero(mask & (D['mi']==0));canvas=Image.new('I',(W,H),0);draw=ImageDraw.Draw(canvas)
 for i in ids:draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in uv[i]],fill=int(i)+1)
 own=np.asarray(canvas);yy,xx=np.nonzero(own);fi=own[yy,xx]-1
 q=np.column_stack(((xx+.5)/W,1-(yy+.5)/H));tri=uv[fi];a=tri[:,0];v0=tri[:,1]-a;v1=tri[:,2]-a;v2=q-a
 den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];safe=np.where(abs(den)<1e-12,1,den)
 b=(v2[:,0]*v1[:,1]-v2[:,1]*v1[:,0])/safe;cc=(v0[:,0]*v2[:,1]-v0[:,1]*v2[:,0])/safe
 pos=co[faces[fi,0]]*(1-b-cc)[:,None]+co[faces[fi,1]]*b[:,None]+co[faces[fi,2]]*cc[:,None]
 return yy,xx,pos

def replace(label,mask,classify,clean_filter,extent=None):
 yy,xx,p=surface(mask);col=original[yy,xx].astype(float)
 bad=classify(col,p);good=clean_filter(col,p)
 if extent is not None:bad &= extent(p)
 assert bad.sum() and good.sum(),(label,bad.sum(),good.sum())
 if label.startswith('cardigan'):
  center=p.mean(axis=0);q=(p-center)/20
  def features(q):return np.column_stack((np.ones(len(q)),q[:,0],q[:,1],q[:,2],q[:,0]*q[:,2],q[:,0]**2,q[:,2]**2))
  X=features(q);fitgood=good.copy()
  for iteration in range(3):
   coef=np.linalg.lstsq(X[fitgood],col[fitgood],rcond=None)[0];res=np.linalg.norm(X@coef-col,axis=1);limit=max(8.,float(np.quantile(res[fitgood],.85)));fitgood=good&(res<limit)
  fill=np.clip(X@coef,[130,70,110],[250,210,225])
  distance,_=cKDTree(p[bad]).query(p,k=1,workers=1)
  alpha=np.exp(-distance**2/(2*1.35**2))
  def smooth(t):
   t=np.clip(t,0,1);return t*t*(3-2*t)
  alpha*=smooth(p[:,1]/8.)*smooth((p[:,2]-103)/4.)*smooth((149-p[:,2])/6.)*smooth((30-abs(p[:,0]))/5.)
  alpha[alpha<.01]=0
  rgb[yy,xx]=np.clip(np.round(col*(1-alpha[:,None])+fill*alpha[:,None]),0,255).astype('uint8')
  dist=np.array([0.])
 else:
  tree=cKDTree(p[good]);dist,indices=tree.query(p[bad],k=min(16,int(good.sum())),workers=1)
  if dist.ndim==1:dist=dist[:,None];indices=indices[:,None]
  weights=1/np.maximum(dist,.03)**2;weights/=weights.sum(axis=1,keepdims=True)
  fill=(col[good][indices]*weights[:,:,None]).sum(axis=1)
  rgb[yy[bad],xx[bad]]=np.clip(np.round(fill),0,255).astype('uint8')
 repair=np.zeros((H,W),bool);repair[yy[bad],xx[bad]]=True
 # Gutter padding is applied once below, using the full atlas ownership map.
 reports.append({'region':label,'surface_pixels':len(yy),'repaired_pixels':int(bad.sum()),'clean_samples':int(good.sum()),'max_neighbor_distance_cm':float(dist.max())})
 return repair
# Navy pleats retain the original white stripe and clean fold shading.
skirt=replace('rear/front skirt pink contamination',c==10,
 lambda c,p:(c[:,0]>c[:,2]*.90)&((c.mean(axis=1)<135)|(p[:,2]>102.5)),
 lambda c,p:(c[:,2]>c[:,0]*1.14)&(c[:,2]>c[:,1]*1.04)&(c.mean(axis=1)<105))
# The backpack stain is a saturated magenta silhouette on cardigan component 0.
coatmask=(c==0)&(fc[:,1]>0)&(fc[:,2]>103)&(fc[:,2]<149)&(abs(fc[:,0])<30)
coat=replace('cardigan rear baked backpack-color silhouette',coatmask,
 lambda c,p:(c[:,1]<c[:,0]*.53)&(c[:,0]>55)&(c[:,2]>c[:,1]*1.25),
 lambda c,p:(c[:,0]>130)&(c[:,1]>c[:,0]*.58)&(c[:,1]<c[:,0]*.82)&(c[:,2]>c[:,0]*.65)&(c[:,2]<c[:,0]*.95))
# Restore the left stocking rim. Keep its pink belt/strap; the wing is a separate
# mesh and untouched. The opposite cat-shaped stocking edge is untouched.
legmask=(c==1)&(fc[:,0]>3)&(fc[:,2]>74)&(fc[:,2]<87)
stock=replace('left stocking missing dark area above wing',legmask,
 lambda c,p:~((c[:,0]>c[:,1]*1.8)&(c[:,0]>c[:,2]*1.18)),
 lambda c,p:(p[:,2]<80)&(c.max(axis=1)<115)&(c[:,0]<c[:,1]*1.55)&(c[:,2]<c[:,1]*1.5),
 lambda p:(p[:,2]>81.5)&(p[:,2]<85.8))
# Rebuild one continuous pink strap directly on the deforming left thigh.
# Clear the jagged baked strap above the wing before painting a single straight
# band. The pink horizontal garter below it stays intact.
yy,xx,p=surface((c==1)&(fc[:,0]>3)&(fc[:,2]>81.3)&(fc[:,2]<106))
col=rgb[yy,xx].astype(float)
front=(p[:,1]<1.0)&(p[:,2]>84)&(p[:,2]<104)
magenta=(col[:,1]<col[:,0]*.52)&(col[:,0]>90)&(col[:,0]>col[:,2]*1.1)
skin=(col[:,0]>160)&(col[:,1]>col[:,0]*.66)&(col[:,2]>col[:,0]*.65)&(p[:,2]>86)
distance,_=cKDTree(p[front&magenta]).query(p,k=1,workers=1)
clear=front&((distance<.95)|((p[:,0]>6.0)&(p[:,0]<13.5)&(p[:,2]>85.8)&(p[:,2]<100)))
knn=cKDTree(p[skin]);dist,ix=knn.query(p[clear],k=16,workers=1);wt=1/np.maximum(dist,.1)**2;wt/=wt.sum(axis=1,keepdims=True)
clean=(col[skin][ix]*wt[:,:,None]).sum(axis=1)
# On the stocking side use a dark fabric fill instead of skin.
clean[p[clear,2]<85.8]=[79,63,74]
blend=np.clip((.95-distance[clear])/.30,0,1)
blend[(p[clear,0]>6)&(p[clear,0]<13.5)&(p[clear,2]>85.8)&(p[clear,2]<100)]=1
col[clear]=col[clear]*(1-blend[:,None])+clean*blend[:,None]
center=11.0+.06*(p[:,2]-84.)
delta=abs(p[:,0]-center)
alpha=np.clip((.80-delta)/.18,0,1)*np.clip((1.0-p[:,1])/.4,0,1)
alpha*=((p[:,2]>81.7)&(p[:,2]<104))
strap=np.tile([207.,56.,118.],(len(p),1));strap*=np.clip(1-.06*delta[:,None],.9,1)
col=col*(1-alpha[:,None])+strap*alpha[:,None]
rgb[yy,xx]=np.clip(np.round(col),0,255).astype('uint8')
reports.append({'region':'continuous thigh-bound pink strap','cleared_texels':int(clear.sum()),'painted_texels':int((alpha>0).sum()),'implementation':'thigh surface albedo; no separate floating mesh'})
# Rebuild a clean dark stocking rim and one even upper pink band. Old stud/wing
# projections must not remain as bright triangles above the new physical pin.
yy,xx,p=surface((c==1)&(fc[:,0]>3)&(fc[:,2]>76)&(fc[:,2]<87))
oldcol=rgb[yy,xx].astype(float)
rim=(p[:,2]>76.8)&(p[:,2]<85.8)
band=(p[:,2]>78.5)&(p[:,2]<81.4)
fabric=np.tile([77.,62.,73.],(len(p),1))
# Small broad lighting term, never reuse the projected ornament's baked colors.
fabric*=np.clip(1+.03*p[:,1,None],.82,1.18)
oldcol[rim]=fabric[rim]
pink=np.tile([201.,48.,110.],(len(p),1))*np.clip(1+.02*p[:,1,None],.85,1.15)
band_alpha=np.clip((p[:,2]-78.5)/.16,0,1)*np.clip((81.4-p[:,2])/.16,0,1)
oldcol=oldcol*(1-band_alpha[:,None])+pink*band_alpha[:,None]
center=11+.06*(p[:,2]-84);alpha=np.clip((.80-abs(p[:,0]-center))/.18,0,1)*np.clip((1-p[:,1])/.4,0,1)
alpha*=(p[:,2]>81.25)&(p[:,2]<85.8)
oldcol=oldcol*(1-alpha[:,None])+np.array([207.,56.,118.])*alpha[:,None]
# The frame is fused into the leg component by Tripo. Preserve its silver
# texels instead of treating the buckle's upper edge as dark stocking fabric.
sourcecol=original[yy,xx].astype(float)
silver=(p[:,0]>14)&(p[:,0]<17)&(p[:,2]<78.1)&(sourcecol.mean(axis=1)>125)&((sourcecol.max(axis=1)-sourcecol.min(axis=1))<65)
oldcol[silver]=sourcecol[silver]
rgb[yy,xx]=np.clip(np.round(oldcol),0,255).astype('uint8')
reports.append({'region':'clean left stocking rim and upper garter band','dark_rim_texels':int(rim.sum()),'pink_band_texels':int(band.sum()),'fused_silver_buckle_texels_preserved':int(silver.sum())})
# The cat's old projected colors were also baked into the white strap behind
# the pendant. Clean only the upper white ribbon, preserving the lower buckle.
yy,xx,p=surface(c==14);col=original[yy,xx].astype(float)
good=(col.min(axis=1)>150)&(col.max(axis=1)-col.min(axis=1)<30)
bad=(p[:,2]>121.5)
assert good.sum()>20
dist,ix=cKDTree(p[good]).query(p[bad],k=12,workers=1)
wt=1/np.maximum(dist,.10)**2;wt/=wt.sum(axis=1,keepdims=True)
rgb[yy[bad],xx[bad]]=np.clip(np.round((col[good][ix]*wt[:,:,None]).sum(axis=1)),0,255).astype('uint8')
reports.append({'region':'white bag ribbon behind rebuilt charm','repaired_pixels':int(bad.sum()),'lower_buckle_preserved':True})
# Four-pixel padding into unowned UV gutters prevents old colors bleeding back
# through triangle-edge filtering. Never paint another surface's UV interiors.
owner=Image.new('1',(W,H),0);draw=ImageDraw.Draw(owner)
for tri in uv[D['mi']==0]:draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in tri],fill=1)
changed=np.any(rgb!=original,axis=2)
dist,nearest=distance_transform_edt(~changed,return_indices=True)
padding=(dist<=4)&~np.asarray(owner).astype(bool)&~changed
rgb[padding]=rgb[nearest[0][padding],nearest[1][padding]]
reports.append({'region':'unowned atlas gutters only','padding_pixels':int(padding.sum()),'radius_pixels':4})
# Protect face, hair, and hands: no edits on their UV interiors.
changed=np.any(rgb!=original,axis=2)
yy,xx,_=surface((fc[:,2]>165)|np.isin(c,[4,5]))
assert not changed[yy,xx].any(),'Unrelated head/hand texels changed'
# Expanded cleanup includes the upper thigh, rebuilt stocking rim and white
# ribbon, plus unowned gutters. Head/hands remain protected exactly above.
print(json.dumps({'changed_pixels':int(changed.sum()),'regions':reports}),flush=True)
assert changed.sum()<1500000,'Unexpectedly broad atlas edit'
OUT=ROOT/'textures';OUT.mkdir(exist_ok=True);dest=OUT/'sui-jk-albedo-v9.png';Image.fromarray(rgb).save(dest)
changed=np.any(rgb!=original,axis=2);Image.fromarray((changed*255).astype('uint8')).save(ROOT/'atlas-repair-mask.png')
report={'source_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':[W,H],'changed_pixels':int(changed.sum()),'regions':reports,'method':'textured-triangle UV ownership; local 3D interpolation, robust smooth rear-cardigan color fit, and one thigh-surface strap; no global recolor'}
(ROOT/'atlas-repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
