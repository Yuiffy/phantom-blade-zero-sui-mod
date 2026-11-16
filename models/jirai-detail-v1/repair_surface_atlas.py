"""Surface-owned texel repair; mirrors a clean thigh, with world-space feathering."""
from pathlib import Path
import numpy as np,cv2,json,hashlib
from PIL import Image
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1'
d=np.load(W/'surface-baseline.npz');p=d['positions'];comp=d['components'];uv=d['uv'];lv=d['loop_vertices']
im=np.array(Image.open(W/'textures/r5-albedo.png').convert('RGB'));H,T=im.shape[:2]
def patches(source=5,zlo=75,zhi=115):
 for ls in d['loop_triangles']:
  vi=lv[ls];pts=p[vi]
  if not np.all(comp[vi]==source) or pts[:,2].max()<zlo or pts[:,2].min()>zhi:continue
  q=uv[ls]*[T-1,H-1];q[:,1]=H-1-q[:,1]
  lo=np.floor(q.min(0)).astype(int).clip(0,[T-1,H-1]);hi=np.ceil(q.max(0)).astype(int).clip(0,[T-1,H-1]);A=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(A))<1e-8:continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(A).T;b=np.dstack([b,1-b.sum(-1)]);inside=(b>=-1e-5).all(-1)
  yield xx[inside],yy[inside],(b@pts)[inside]
donors=[];colors=[]
for x,y,xyz in patches():
 rgb=im[y,x];ok=(xyz[:,0]<-1)&(xyz[:,2]>75)&(xyz[:,2]<114)&(rgb.min(1)>180)&(rgb.max(1)-rgb.min(1)<65)
 donors.append(xyz[ok]);colors.append(rgb[ok])
donors=np.concatenate(donors);colors=np.concatenate(colors).astype(float);tree=cKDTree(donors)
out=im.copy();mask=np.zeros((H,T),np.uint8)
def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
for x,y,xyz in patches():
 # Whole circumference repairs the former rear stripe and the old front strap.
 # Fade above/below the bare region; the actual cat garter below is preserved.
 alpha=(xyz[:,0]>0)*smooth((xyz[:,2]-77.5)/2)*smooth((113-xyz[:,2])/3)
 ok=alpha>0
 if not ok.any():continue
 x=x[ok];y=y[ok];xyz=xyz[ok];a=alpha[ok];query=xyz.copy();query[:,0]*=-1
 dist,idx=tree.query(query,k=8);wt=1/np.maximum(dist,.03)**2;wt/=wt.sum(1,keepdims=True);rgb=(colors[idx]*wt[:,:,None]).sum(1)
 out[y,x]=np.rint(im[y,x]*(1-a[:,None])+rgb*a[:,None]).clip(0,255).astype(np.uint8);mask[y,x]=np.maximum(mask[y,x],np.rint(a*255).astype(np.uint8))
# Clean baked choker fragments on the neck; the actual separate collar/band
# remains geometry and will receive a uniform leather/metal assignment.
neck=[]
for x,y,xyz in patches(0,170,175):
 rgb=im[y,x];ok=(abs(xyz[:,0])<5)&(xyz[:,2]>170.5)&(xyz[:,2]<174)&(rgb.min(1)>185)&((rgb.max(1)-rgb.min(1))<65)
 neck.append(rgb[ok])
neck=np.concatenate(neck);assert len(neck)>100;neckcolor=np.median(neck,axis=0)
for x,y,xyz in patches(0,164,171):
 a=smooth((xyz[:,2]-164)/1)*smooth((171-xyz[:,2])/1.3)*(1-smooth((abs(xyz[:,0])-3.5)/1.5));ok=a>0
 x=x[ok];y=y[ok];a=a[ok];out[y,x]=np.rint(im[y,x]*(1-a[:,None])+neckcolor*a[:,None]).astype(np.uint8);mask[y,x]=np.maximum(mask[y,x],np.rint(a*255).astype(np.uint8))
# Pad only into currently unoccupied texels, never across another UV island.
occupied=np.zeros_like(mask)
for ls,mat in zip(d['loop_triangles'],d['materials']):
 if mat not in [0,1,2,3,4,5,6,7,10,11] or np.all(comp[lv[ls]]==5) or (np.all(comp[lv[ls]]==0) and p[lv[ls],2].min()>164 and p[lv[ls],2].max()<171):continue
 q=uv[ls]*[T-1,H-1];q[:,1]=H-1-q[:,1];cv2.fillConvexPoly(occupied,np.rint(q).astype(np.int32),255)
edge=(mask>0).astype(np.uint8);dist,labels=cv2.distanceTransformWithLabels(1-edge,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
seeds=out[edge>0];pad=(dist<=6)&(occupied==0)&(labels>0)&(mask==0)
out[pad]=seeds[labels[pad]-1];mask[pad]=255
Image.fromarray(out).save(W/'textures/jirai-albedo.png');Image.fromarray(mask).save(W/'textures/skin-repair-mask.png')
changed=np.any(out!=im,2);assert not np.any(changed&(mask==0))
(W/'atlas-repair.json').write_text(json.dumps({'changed_pixels':int(changed.sum()),'donor_texels':len(donors),'source_sha256':hashlib.sha256((W/'textures/r5-albedo.png').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((W/'textures/jirai-albedo.png').read_bytes()).hexdigest(),'outside_mask_identical':True,'scope':'source5 anatomical left bare thigh; original front strap projection removed for rebuilt geometry; rear repair seam removed; source0 neck baked choker fragments cleaned with feathered skin mask'},indent=2))
print('ATLAS_REPAIRED',int(changed.sum()))
