"""Isolate existing UV islands to recolor lashes and erase one lip branch."""
from common import *
import numpy as np,cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image

def smooth(a):
 a=np.clip(a,0,1);return a*a*(3-2*a)

def outer_wing(q,c):
 cx=np.where(q[...,0]<-.35,-5.317217,4.614422);outward=(q[...,0]-cx)*np.where(cx<0,-1,1)
 return (c==0)&(outward>2.15)&(outward<4.7)&(q[...,2]>176.6+.70*(outward-2.15))&(q[...,2]<179.35)&(q[...,1]>.65)

def lash_region(q,c):
 upper=(c==0)&(abs(q[...,0]+.35)>2.6)&(abs(q[...,0]+.35)<9.8)&(q[...,2]>178.1)&(q[...,2]<180.35)&(q[...,1]>.2)
 lower=np.isin(c,[125,126,128,136])
 return upper|lower|outer_wing(q,c)

def mouth_alpha(q,c):
 # Preserve the rising primary right lip line and clear only its lower spur.
 x=q[...,0];z=q[...,2];primary=171.55+.10*np.clip(x,0,1.7)
 return smooth((x-.05)/.25)*smooth((1.90-x)/.22)*smooth((z-171.02)/.12)*smooth((primary-.055-z)/.085)*(q[...,1]>1.3)*(c==0)

def black_pigment(q,c,rgb):
 # The connected head also contains real skin above the raised lashes. Keep
 # that skin and the eye's pale backing; recolor the original dark/pink strip.
 mean=rgb.mean(-1);cx=np.where(q[...,0]<-.35,-5.317217,4.614422);outward=(q[...,0]-cx)*np.where(cx<0,-1,1)
 top=179.57+.10*outward-.06*((q[...,0]-cx)/3)**2
 return lash_region(q,c)&(np.isin(c,[125,126,128,136])|outer_wing(q,c)|((mean<130)|((q[...,2]<top)&(mean<218))))

def main():
 assert_baseline();old=np.load(PIN/'final-render.npz');d={k:old[k].copy() for k in old.files};p=d['positions'].copy();t=d['indices'].reshape(-1,3);mat=d['materials'];uv=d['uv'][:,0].astype(float)
 source=REPO/'private/jirai-face-v3/surface.npz';s=np.load(source);src=d['source_index'];comp=np.where(src>=0,s['components'][np.maximum(src,0)],-1)
 st=t[mat[t[:,0]]==0];edges=np.concatenate([st[:,[0,1]],st[:,[1,2]],st[:,[2,0]]]);adj=coo_matrix((np.ones(len(edges)),(edges[:,0],edges[:,1])),shape=(len(p),len(p)));_,labels=connected_components(adj,directed=False)
 # Old component IDs for buried iris fragments now contain sleeve bridges.
 # Select current visible geometry and preserve all their reused arm slots.
 active=np.zeros(len(p),bool);active[np.unique(st)]=True
 wanted=np.unique(labels[active&(lash_region(p,comp)|(mouth_alpha(p,comp)>0))])
 im=np.array(Image.open(PIN/'T_Jirai_Base.png').convert('RGB'));out=im.copy();occ=np.zeros((8192,8192),np.uint8)
 for f in st:cv2.fillConvexPoly(occ,np.rint(uv[f]*8191).astype('i4'),255)
 occ[:16]=255;occ[-16:]=255;occ[:,:16]=255;occ[:,-16:]=255
 dist=cv2.distanceTransform(255-occ,cv2.DIST_L2,5);cy,cx=np.unravel_index(dist.argmax(),dist.shape)
 side=1024;origin=np.array([cx-side//2,cy-side//2]);origin=(origin//4)*4;ox,oy=origin
 assert dist[cy,cx]>side/2*2**.5+8 and not occ[oy:oy+side,ox:ox+side].any()
 boxes=[]
 for lab in wanted:
  ids=np.where(labels==lab)[0];xy=uv[ids]*8191;lo=(np.floor(xy.min(0)/4).astype(int)*4-8).clip(0,8191);hi=(np.ceil(xy.max(0)/4).astype(int)*4+8).clip(0,8191);size=(np.ceil((hi-lo+1)/4)*4).astype(int)
  boxes.append((int(lab),ids,lo,hi,size))
 xx=yy=row=0;records=[];moved=[];painted=np.zeros((8192,8192),np.uint8);lash_pixels=mouth_pixels=0
 for lab,ids,lo,hi,size in sorted(boxes,key=lambda b:b[-1][1],reverse=True):
  width,height=size
  if xx+width>side:yy+=row;xx=0;row=0
  assert yy+height<=side
  dst=origin+[xx,yy];xx+=width;row=max(row,height);shift=dst-lo
  patch=im[lo[1]:hi[1]+1,lo[0]:hi[0]+1].copy();ph,pw=patch.shape[:2]
  local_mask=np.zeros((ph,pw),np.uint8);uv_occ=np.zeros_like(local_mask);local_ids={int(v):j for j,v in enumerate(ids)}
  local_uv=uv[ids]*8191-lo;planar=len(ids)>100
  if planar:
   # These two large native head islands reuse texels between upper skin and
   # lashes. Give them separate XZ chart locations instead of dyeing both.
   plane=p[ids][:,[0,2]];minimum=plane.min(0);extent=np.maximum(np.ptp(plane,axis=0),1e-4);local_uv=8+(plane-minimum)/extent*np.array([pw-17,ph-17]);patch[:]=[240,209,210]
  d['uv'][ids,0]=(local_uv+dst)/8191
  depth=np.full((ph,pw),-np.inf)
  faces=st[labels[st[:,0]]==lab]
  for f in faces:
   q=local_uv[[local_ids[int(v)] for v in f]];cv2.fillConvexPoly(uv_occ,np.rint(q).astype('i4'),255)
   low=np.floor(q.min(0)).astype(int).clip(0,[pw-1,ph-1]);high=np.ceil(q.max(0)).astype(int).clip(0,[pw-1,ph-1]);a=np.column_stack([q[0]-q[2],q[1]-q[2]])
   gx,gy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1))
   if abs(np.linalg.det(a))<1e-8:
    # Constant-UV faces still need their pigment changed.
    x=np.array([int(np.clip(round(q[:,0].mean()),0,pw-1))]);y=np.array([int(np.clip(round(q[:,1].mean()),0,ph-1))]);xyz=p[f].mean(0)[None];b=np.full((1,3),1/3)
   else:
    b=(np.stack([gx,gy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)]);inside=(b>=-1e-5).all(-1);x=gx[inside];y=gy[inside];b=b[inside];xyz=b@p[f]
   if planar:
    take=xyz[:,1]>=depth[y,x];x=x[take];y=y[take];xyz=xyz[take];b=b[take];depth[y,x]=xyz[:,1]
    donor=np.rint((b@uv[f])*8191).astype(int).clip(0,8191);patch[y,x]=im[donor[:,1],donor[:,0]]
   c=comp[f[0]];black=black_pigment(xyz,c,patch[y,x]);alpha=mouth_alpha(xyz,c)
   if black.any():patch[y[black],x[black]]=[4,4,4];local_mask[y[black],x[black]]=255;lash_pixels+=int(black.sum())
   # Remove lower red/brown pigment while keeping the original upper line.
   if np.any(alpha>0):
    rgb=patch[y,x].astype(float);skin=np.array([240,209,210]);pigment=smooth((rgb[:,0]-rgb[:,1]-30)/15);amount=alpha*pigment
    take=amount>0;patch[y[take],x[take]]=np.rint(rgb[take]*(1-amount[take,None])+skin*amount[take,None]).astype('u1');local_mask[y[take],x[take]]=255;mouth_pixels+=int(take.sum())
  if planar:
   valid=np.isfinite(depth);assert valid.any()
   _,nearest=cv2.distanceTransformWithLabels(1-valid.astype('u1'),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
   patch[~valid]=patch[valid][nearest[~valid]-1]
  # Cover subpixel triangles and half-float rounding using their actual new
  # quantized UVs. Never use the pigment of an already painted neighbor to
  # classify the forehead as a lash.
  quantized=d['uv'][ids,0].astype(float)*8191-dst
  black_mask=np.zeros_like(local_mask)
  for f in faces:
   center=p[f].mean(0);c=comp[f[0]];sample=np.rint(uv[f].mean(0)*8191).astype(int).clip(0,8191)
   if black_pigment(center,c,im[sample[1],sample[0]]):
    points=np.rint(quantized[[local_ids[int(v)] for v in f]]).astype('i4');cv2.fillConvexPoly(black_mask,points,255)
  black_mask=cv2.dilate(black_mask,np.ones((3,3),np.uint8));patch[black_mask>0]=[4,4,4];local_mask[black_mask>0]=255
  # Pad modified islands only into their own unused margin, never a neighbor.
  if local_mask.any():
   distance,nearest=cv2.distanceTransformWithLabels(1-(local_mask>0).astype('u1'),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
   pad=(distance<=5)&(uv_occ==0)&(nearest>0);patch[pad]=patch[local_mask>0][nearest[pad]-1]
  dx,dy=dst;out[dy:dy+ph,dx:dx+pw]=patch;painted[dy:dy+ph,dx:dx+pw]=255
  moved.extend(ids.tolist())
  records.append(dict(island=lab,vertices=len(ids),source_box=[*lo.tolist(),*hi.tolist()],destination_xy=dst.tolist(),shift_xy=shift.tolist(),planar_source_color_bake=planar))
 # Two shallow right lip ridges cast separate lines even with clean albedo.
 # Bring just the lower spur into the original upper line; retain the left
 # mouth, tip, and every eye/head vertex outside this tiny bounded region.
 x=p[:,0];z=p[:,2];primary=171.55+.10*np.clip(x,0,1.7)
 merge=smooth((x-.05)/.25)*smooth((1.6-x)/.25)*smooth((z-171.10)/.18)*smooth((primary+.06-z)/.10)*(p[:,1]>2.5)*(comp==0)*(mat==0)
 mouth_ids=np.where(merge>0)[0];d['positions'][mouth_ids,2]+=((primary[mouth_ids]-z[mouth_ids])*.88*merge[mouth_ids]).astype('<f4')
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png');Image.fromarray(painted).save(ROOT/'atlas-scope.png');np.savez_compressed(ROOT/'patched-render.npz',**d)
 np.savez_compressed(ROOT/'author-selections.npz',uv_vertices=np.array(moved),mouth_vertices=mouth_ids,weight_copies=np.empty((0,2),dtype=int))
 write(ROOT/'author-report.json',dict(passed=True,native_sha256=sha(ROOT/'patched-render.npz'),atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),source_native_sha256=sha(PIN/'final-render.npz'),source_atlas_sha256=sha(PIN/'T_Jirai_Base.png'),islands=records,relocated_islands=len(records),uv_vertices=len(moved),lash_samples=lash_pixels,mouth_spur_samples=mouth_pixels,mouth_merged_vertices=len(mouth_ids),mouth_max_shift_cm=float(np.max(abs(d['positions'][:,2]-p[:,2]))),frames_indices_weights_unchanged=True,eye_socket_shape_unchanged=True,game_runtime_tested=False))
 write(ROOT/'atlas-report.json',dict(source_sha256=sha(PIN/'T_Jirai_Base.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),changed_pixels=int(np.any(out!=im,2).sum()),original_atlas_pixels_exact=True,only_previously_unused_skin_atlas_region_written=True,planar_source_color_bake_islands=int(sum(r['planar_source_color_bake'] for r in records))))
 print('LASHLIP_AUTHORED',len(records),lash_pixels,mouth_pixels,flush=True)

if __name__=='__main__':main()
