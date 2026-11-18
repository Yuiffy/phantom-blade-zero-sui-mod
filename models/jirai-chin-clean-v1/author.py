"""Move the fragmented lower face to generously padded, skin-only charts."""
from common import *
import numpy as np,cv2
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image

def main():
 assert_baseline();old=np.load(PIN/'final-render.npz');d={k:old[k].copy() for k in old.files};p=d['positions'];uv=d['uv'][:,0].astype(float);tri=d['indices'].reshape(-1,3);mat=d['materials'];st=tri[mat[tri[:,0]]==0]
 ed=np.concatenate([st[:,[0,1]],st[:,[1,2]],st[:,[2,0]]]);_,labels=connected_components(coo_matrix((np.ones(len(ed)),(ed[:,0],ed[:,1])),shape=(len(p),len(p))),directed=False)
 lower=(mat==0)&(p[:,2]>166.9)&(p[:,2]<171.)&(p[:,1]>0)&(abs(p[:,0]+.35)<8)
 # The two large upper-face charts contain the approved lash colors. Keep
 # them exact; the offending chin islands are the 16 other native charts.
 wanted=[int(k) for k in np.unique(labels[lower]) if np.count_nonzero(labels==k)<200];assert len(wanted)==16
 src=np.array(Image.open(FACE/'T_Jirai_Base.png').convert('RGB'));out=src.copy();occ=np.zeros((8192,8192),np.uint8)
 for f in st:cv2.fillConvexPoly(occ,np.rint(uv[f]*8191).astype('i4'),255)
 occ[:24]=255;occ[-24:]=255;occ[:,:24]=255;occ[:,-24:]=255
 dist=cv2.distanceTransform(255-occ,cv2.DIST_L2,5);yy,xx=np.unravel_index(dist.argmax(),dist.shape);side=1024;origin=(np.array([xx-512,yy-512])//4)*4;ox,oy=origin
 assert not occ[oy-8:oy+side+8,ox-8:ox+side+8].any()
 records=[];moved=[];scope=np.zeros_like(occ)
 for slot,lab in enumerate(wanted):
  ids=np.where(labels==lab)[0];faces=st[labels[st[:,0]]==lab];lookup={int(v):i for i,v in enumerate(ids)}
  plane=p[ids][:,[0,2]].astype(float);lo=plane.min(0);extent=np.maximum(np.ptp(plane,axis=0),.01);local=48+(plane-lo)/extent*159
  dst=origin+np.array([(slot%4)*256,(slot//4)*256]);patch=np.full((256,256,3),[238,206,204],np.uint8);depth=np.full((256,256),-np.inf)
  d['uv'][ids,0]=(dst+local)/8191
  for f in faces:
   q=local[[lookup[int(v)] for v in f]];low=np.floor(q.min(0)).astype(int).clip(0,255);high=np.ceil(q.max(0)).astype(int).clip(0,255);a=np.column_stack([q[0]-q[2],q[1]-q[2]])
   if abs(np.linalg.det(a))<1e-8:continue
   gx,gy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1));b=(np.stack([gx,gy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)]);inside=(b>=-1e-5).all(-1);x=gx[inside];y=gy[inside];b=b[inside];xyz=b@p[f]
   take=xyz[:,1]>=depth[y,x];x=x[take];y=y[take];xyz=xyz[take];b=b[take];depth[y,x]=xyz[:,1]
   donor=np.rint(b@uv[f]*8191).astype(int).clip(0,8191);rgb=src[donor[:,1],donor[:,0]].astype(float)
   # Original chin skin is already nearly constant. Remove no lip pigment:
   # blend to its own clean skin sample strictly below the mouth height.
   amount=np.clip((171.05-xyz[:,2])/.40,0,1);amount=amount*amount*(3-2*amount)
   patch[y,x]=np.rint(rgb*(1-amount[:,None])+np.array([238,206,204])*amount[:,None]).clip(0,255).astype('u1')
  valid=np.isfinite(depth);assert valid.any(),lab
  # Fill every unused pixel, giving the isolated surface a >=48px gutter.
  _,nearest=cv2.distanceTransformWithLabels(1-valid.astype('u1'),cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL);patch[~valid]=patch[valid][nearest[~valid]-1]
  dx,dy=dst;out[dy:dy+256,dx:dx+256]=patch;scope[dy:dy+256,dx:dx+256]=255;moved.extend(ids.tolist())
  records.append(dict(island=lab,vertices=len(ids),destination_xy=dst.tolist(),chart_size=256,gutter_pixels=48,xyz_min=p[ids].min(0).tolist(),xyz_max=p[ids].max(0).tolist()))
 assert not np.any(np.any(out!=src,2)&(occ>0))
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png');Image.fromarray(scope).save(ROOT/'atlas-scope.png');np.savez_compressed(ROOT/'patched-render.npz',**d)
 np.savez_compressed(ROOT/'author-selections.npz',uv_vertices=np.array(moved),mouth_vertices=np.empty(0,int),weight_copies=np.empty((0,2),int))
 write(ROOT/'author-report.json',dict(passed=True,native_sha256=sha(ROOT/'patched-render.npz'),atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),source_native_sha256=sha(PIN/'final-render.npz'),source_atlas_sha256=sha(FACE/'T_Jirai_Base.png'),islands=records,relocated_islands=len(records),uv_vertices=len(moved),all_positions_frames_indices_weights_uv1_exact=True,eye_and_lash_charts_unchanged=True,game_runtime_tested=False))
 write(ROOT/'atlas-report.json',dict(source_sha256=sha(FACE/'T_Jirai_Base.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),changed_pixels=int(np.any(out!=src,2).sum()),old_occupied_skin_texels_exact=True,isolated_patch_origin=origin.tolist(),isolated_patch_size=1024,minimum_chart_gutter=48))
 print('CHIN_AUTHORED',len(records),len(moved),flush=True)

if __name__=='__main__':main()
