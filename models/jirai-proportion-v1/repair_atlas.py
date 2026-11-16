"""Remove the audited duplicate rear suspender's baked projection, within leg UVs."""
from pathlib import Path
import numpy as np,json,hashlib,cv2
from PIL import Image
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';d=np.load(ROOT/'source-geometry.npz');im=np.array(Image.open(next((ROOT/'input').rglob('*.jpg'))).convert('RGB'));H,W=im.shape[:2]
xyz=d['positions'];comp=d['components'];uv=d['uv'];lv=d['loop_vertices'];mask=np.zeros((H,W),np.uint8);shoulder=np.zeros((H,W),np.uint8)
rgb=np.zeros((len(xyz),3));count=np.zeros(len(xyz))
pixels=np.rint(uv*[W-1,H-1]).astype(int);pixels[:,1]=H-1-pixels[:,1];pixels=pixels.clip(0,[W-1,H-1]);samples=im[pixels[:,1],pixels[:,0]]
np.add.at(rgb,lv,samples);np.add.at(count,lv,1);rgb/=np.maximum(count[:,None],1)
clean=(comp==5)&(xyz[:,0]<-.025)&(xyz[:,1]>.005)&(xyz[:,2]>.40)&(xyz[:,2]<.59)&(rgb.mean(1)>175)
tree=cKDTree(xyz[clean]);colors=rgb[clean];mirror=im.copy()
for loop in d['loop_triangles']:
 ids=lv[loop];p=xyz[ids]
 isleg=np.all(comp[ids]==5);isshoulder=np.all(comp[ids]==0)
 if not (isleg or isshoulder):continue
 if isleg and (p[:,0].max()<.035 or p[:,0].min()>.077 or p[:,1].max()<.020 or p[:,2].max()<.419 or p[:,2].min()>.575):continue
 if isshoulder and (p[:,2].max()<.760 or p[:,2].min()>.811 or abs(p[:,0]).max()<.035 or abs(p[:,0]).min()>.095):continue
 q=uv[loop]*[W-1,H-1];q[:,1]=H-1-q[:,1];lo=np.floor(q.min(0)).astype(int).clip(0,[W-1,H-1]);hi=np.ceil(q.max(0)).astype(int).clip(0,[W-1,H-1])
 if np.any(hi<lo):continue
 xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));A=np.column_stack([q[0]-q[2],q[1]-q[2]])
 if abs(np.linalg.det(A))<1e-6:continue
 b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(A).T;b=np.dstack([b,1-b.sum(-1)]);inside=(b>=-1e-5).all(-1);pos=b@p
 if isleg:area=inside&(pos[:,:,0]>.035)&(pos[:,:,0]<.077)&(pos[:,:,1]>.020)&(pos[:,:,2]>.419)&(pos[:,:,2]<.575);target=mask
 else:area=inside&(abs(pos[:,:,0])>.035)&(abs(pos[:,:,0])<.095)&(pos[:,:,2]>.760)&(pos[:,:,2]<.811);target=shoulder
 region=target[lo[1]:hi[1]+1,lo[0]:hi[0]+1];region[area]=255
 if isleg and area.any():
  query=pos[area].copy();query[:,0]*=-1;dist,ix=tree.query(query,k=min(4,len(colors)));weight=1/np.maximum(dist,.001)**2;weight/=weight.sum(1,keepdims=True);color=(colors[ix]*weight[:,:,None]).sum(1)
  view=mirror[lo[1]:hi[1]+1,lo[0]:hi[0]+1];view[area]=np.rint(color).clip(0,255).astype(np.uint8)
dark=(im.mean(2)<200)&(mask>0);fix=cv2.dilate(dark.astype(np.uint8)*255,np.ones((7,7),np.uint8));fix=cv2.bitwise_and(fix,mask);legfix=fix.copy()
shoulder_dark=(im.mean(2)<165)&(shoulder>0);sfix=cv2.dilate(shoulder_dark.astype(np.uint8)*255,np.ones((5,5),np.uint8));sfix=cv2.bitwise_and(sfix,shoulder);fix=cv2.bitwise_or(fix,sfix)
out=cv2.inpaint(im,fix,7,cv2.INPAINT_TELEA);out[legfix>0]=mirror[legfix>0];(ROOT/'textures').mkdir(exist_ok=True);Image.fromarray(out).save(ROOT/'textures/jirai-albedo.png');Image.fromarray(fix).save(ROOT/'textures/rear-strap-repair-mask.png')
(ROOT/'atlas-repair.json').write_text(json.dumps({'changed_pixels':int(np.any(im!=out,2).sum()),'mask_pixels':int((fix>0).sum()),'regions':['source component 5, anatomical left rear thigh duplicate strap projection','source component 0, gray shoulder garment projection on exposed skin'],'source_unchanged':True,'output_sha256':hashlib.sha256((ROOT/'textures/jirai-albedo.png').read_bytes()).hexdigest()},indent=2));print('atlas repaired',int((fix>0).sum()))
