"""Repair surface-owned baked brows/lashes on bangs and medial eye backing."""
from pathlib import Path
import hashlib,json
import numpy as np
import cv2
from PIL import Image
from scipy.ndimage import gaussian_filter1d

R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v2'
source=R/'private/fishnet-v1/T_Jirai_Base.png'
d=np.load(W/'surface.npz');p=d['positions'];c=d['components'];uv=d['uv'];lv=d['loop_vertices']
im=np.array(Image.open(source).convert('RGB'));out=im.copy();H,T=im.shape[:2]
assert (H,T)==(8192,8192)
mask=np.zeros((H,T),np.uint8);occupied=np.zeros_like(mask)

def patches(wanted):
 for ls,mi in zip(d['loop_triangles'],d['materials']):
  vi=lv[ls];pts=p[vi];cid=int(c[vi[0]])
  if cid not in wanted or pts[:,2].max()<175 or pts[:,2].min()>190:continue
  q=uv[ls]*[T-1,H-1];q[:,1]=H-1-q[:,1]
  lo=np.floor(q.min(0)).astype(int).clip(0,[T-1,H-1]);hi=np.ceil(q.max(0)).astype(int).clip(0,[T-1,H-1]);a=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(a))<1e-8:continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)]);inside=(b>=-1e-5).all(-1)
  yield cid,xx[inside],yy[inside],(b@pts)[inside]

def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)

# Use the clean upper part of the SAME bangs for each horizontal position;
# retain its pink streak and lateral strand colors, without baked face marks.
donors=[];colors=[]
for cid,x,y,xyz in patches({19}):
 ok=(xyz[:,2]>184.5)&(xyz[:,2]<187.2)&(xyz[:,1]<-2.5)
 donors.append(xyz[ok]);colors.append(im[y[ok],x[ok]])
donors=np.concatenate(donors);colors=np.concatenate(colors)
grid=np.arange(-9,8.6,.025);profile=np.full((len(grid),3),np.nan)
for i,g in enumerate(grid):
 samples=colors[np.abs(donors[:,0]-g)<.07]
 if len(samples)>4:profile[i]=np.percentile(samples,65,axis=0)
for channel in range(3):
 good=np.isfinite(profile[:,channel]);assert good.sum()>len(grid)*.75
 profile[:,channel]=np.interp(grid,grid[good],profile[good,channel])
 profile[:,channel]=gaussian_filter1d(profile[:,channel],1.1)

counts={'bangs':0,'medial_eye':0}
for cid,x,y,xyz in patches({19,0}):
 a=np.zeros(len(x));rgb=im[y,x].astype(float)
 if cid==19:
  a=smooth((185.0-xyz[:,2])/1.15)*smooth((-xyz[:,1]-1.0)/1.0)
  rgb=np.column_stack([np.interp(xyz[:,0],grid,profile[:,k]) for k in range(3)])
  rgb-=np.clip((183-xyz[:,2])*.5,0,2)[:,None]
  label='bangs'
 elif cid==0:
  # Only the nasal interior of each eye, strictly inside the lid aperture.
  # The source head contains painted socket backing IN FRONT of the new
  # eyeball; whitening the sphere alone cannot replace those visible texels.
  for cx,cz,sign in [(-5.317217,177.799362,1),(4.614422,177.799362,-1)]:
   dx=(xyz[:,0]-cx)*sign;dz=xyz[:,2]-cz
   ellipse=((xyz[:,0]-cx)/2.65)**2+(dz/1.83)**2
   aa=smooth((dx-1.45)/.22)*smooth((.95-ellipse)/.10)
   aa*=smooth((xyz[:,2]-176.2)/.20)*smooth((179.38-xyz[:,2])/.20)
   aa*=(xyz[:,1]<.8)
   a=np.maximum(a,aa)
  rgb[:]=[241,239,235];label='medial_eye'
 ok=a>0
 if not ok.any():continue
 xx=x[ok];yy=y[ok];alpha=a[ok,None]
 out[yy,xx]=np.rint(im[yy,xx]*(1-alpha)+rgb[ok]*alpha).clip(0,255).astype(np.uint8)
 mask[yy,xx]=np.maximum(mask[yy,xx],np.rint(a[ok]*255).astype(np.uint8));counts[label]+=int(ok.sum())

# Pad repaired islands only into unoccupied atlas space. Never bleed into
# retained iris, lashes, clip, pink ponytails, skirt or fishnet UV islands.
for ls in d['loop_triangles']:
 vi=lv[ls]
 if c[vi[0]]>=2000 or c[vi[0]] in {950,951,0,19}:continue
 q=uv[ls]*[T-1,H-1];q[:,1]=H-1-q[:,1]
 cv2.fillConvexPoly(occupied,np.rint(q).astype(np.int32),255)
edge=(mask>0).astype(np.uint8);dist,labels=cv2.distanceTransformWithLabels(1-edge,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
pad=(dist<=4)&(occupied==0)&(labels>0)&(mask==0)
out[pad]=out[edge>0][labels[pad]-1];mask[pad]=255
changed=np.any(out!=im,2);assert not np.any(changed&(mask==0))
# No changed texel can belong to a retained face/body/garment component.
for cid,x,y,xyz in patches({51,52,101,102,125,126,128,131,135,136,139,141,22,34}):
 assert not np.any(changed[y,x]),('retained iris/lash/clip changed',cid)
Image.fromarray(out).save(W/'T_Jirai_Base.png');Image.fromarray(mask).save(W/'repair-mask.png')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
report=dict(source_sha256=sha(source),output_sha256=sha(W/'T_Jirai_Base.png'),surface_sha256=sha(W/'surface.npz'),changed_pixels=int(changed.sum()),samples=counts,outside_mask_exact=True,retained_iris_lash_and_clip_texels_exact=True,fishnet_source_preserved=True,geometry_and_weights_unchanged=True,shared_uv_requires_isolated_skin_and_hair_albedo=True,game_runtime_tested=False)
(W/'atlas-report.json').write_text(json.dumps(report,indent=2)+'\n')
print('FACE_ATLAS_AUTHORED',report)
