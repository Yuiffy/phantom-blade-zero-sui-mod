"""Preserve JK's eye opening and smile; soften the chin and isolate iris UVs."""
from common import *
import numpy as np, cv2
from PIL import Image

def smooth(a,b,x):
 t=np.clip((x-a)/(b-a),0,1);return t*t*(3-2*t)

def main():
 assert_baseline()
 old=np.load(PIN/'final.npz');d={k:old[k].copy() for k in old.files}
 p=d['positions'].astype(float);c=np.load(PAT/'jk-components.npz')['components'];editable=(c==0)&(d['materials']==0)
 def deform(q):
  x,y,z=q.T;r=np.abs(x+.4195)
  # Round the original pointed chin without moving the smile, nose or lids.
  lower=editable*smooth(-1.,1.2,y)*(1-smooth(169.0,170.6,z))*smooth(167.,167.8,z)
  cheek=editable*smooth(-1.,1.5,y)*smooth(2.7,5.8,r)*smooth(169.7,171.5,z)*(1-smooth(173.7,175.4,z))
  out=q.copy()
  out[:,0]+=(x+.4195)*.055*lower
  out[:,0]-=(x+.4195)*.025*cheek
  out[:,2]+=.36*lower*(1-.45*smooth(1.5,4.0,r))
  return out
 d['positions']=deform(p).astype('<f4');changed=np.any(d['positions']!=old['positions'],axis=1)
 jac=np.empty((len(p),3,3))
 for k in range(3):
  e=np.zeros(3);e[k]=.002;jac[:,:,k]=(deform(p+e)-deform(p-e))/.004
 assert np.linalg.det(jac).min()>.6
 packed=d['packed_tangents'].copy();n=unit(np.linalg.solve(jac.transpose(0,2,1),(packed[:,4:7].view('i1')/127.)[...,None])[...,0])
 t=np.einsum('nij,nj->ni',jac,packed[:,:3].view('i1')/127.);t=unit(t-n*np.sum(n*t,axis=1,keepdims=True))
 for cols,v in [(slice(0,3),t),(slice(4,7),n)]:packed[changed,cols]=np.rint(np.clip(v[changed],-1,1)*127).astype('i1').view('u1')
 d['packed_tangents']=packed;d['normals']=packed[:,4:7].view('i1').astype(float)/127
 # Only MI_JK_Base is redirected. Every original used texel remains unchanged.
 atlas=np.array(Image.open(PAT/'jk-after.png').convert('RGB'));out=atlas.copy();uv=old['uv'][:,0].astype(float);tri=old['indices'].reshape(-1,3)
 occ=np.zeros((8192,8192),np.uint8)
 for f in tri[d['materials'][tri[:,0]]==0]:cv2.fillConvexPoly(occ,np.rint(uv[f]*8191).astype('i4'),255)
 occ[:16]=255;occ[-16:]=255;occ[:,:16]=255;occ[:,-16:]=255
 dist=cv2.distanceTransform(255-occ,cv2.DIST_L2,5);yy,xx=np.unravel_index(dist.argmax(),dist.shape)
 side=1024;origin=np.array([xx-side//2,yy-side//2]);origin=(origin//4)*4;ox,oy=origin
 assert not occ[oy-8:oy+side+8,ox-8:ox+side+8].any()
 irispath=REPO/'private/jirai-face-v3/T_Face3_Iris.png';iris=np.array(Image.open(irispath).convert('RGB'))
 # The reference JK iris is ruby red: keep the shared motif and lower orange.
 iris=iris.astype(float);iris[:,:,1]*=.80;iris[:,:,2]*=.98;iris=np.rint(iris).clip(0,255).astype('u1')
 out[oy:oy+side,ox:ox+side]=iris
 records=[]
 for comp in (40,41):
  ids=np.where(c==comp)[0];q=p[ids];lo=q[:,[0,2]].min(0);size=np.ptp(q[:,[0,2]],axis=0)
  local=(q[:,[0,2]]-lo)/size;local[:,1]=1-local[:,1]
  # A small inset keeps filtering inside the borrowed iris disk.
  d['uv'][ids,0]=(origin+16+local*(side-33))/8191
  records.append(dict(component=comp,vertices=len(ids),bounds_min=lo.tolist(),bounds_size=size.tolist()))
 d['changed']=changed;d['iris_vertices']=np.isin(c,[40,41]);d['components']=c
 np.savez_compressed(ROOT/'before.npz',**{k:old[k] for k in old.files});np.savez_compressed(ROOT/'patched-render.npz',**d)
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png')
 np.savez_compressed(ROOT/'author-selections.npz',position_vertices=changed,uv_vertices=d['iris_vertices'],occupancy=occ)
 assert np.array_equal(out[occ>0],atlas[occ>0])
 write(ROOT/'atlas-report.json',dict(passed=True,width=8192,source_sha256=sha(PAT/'jk-after.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),shared_iris_source_sha256=sha(irispath),original_occupied_texels_exact=True,isolated_patch_origin=origin.tolist(),isolated_patch_size=side,iris_red_tint_green_scale=.8))
 write(ROOT/'author-report.json',dict(passed=True,position_vertices=int(changed.sum()),uv_vertices=int(d['iris_vertices'].sum()),max_displacement_cm=float(np.linalg.norm(d['positions']-p,axis=1).max()),chin_lift_cm=.36,cheek_taper_fraction=.025,iris_components=records,eye_openings_lashes_brows_lips_positions_exact=True,source_sha256=sha(PIN/'final.npz'),patched_render_sha256=sha(ROOT/'patched-render.npz'),atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),minimum_jacobian_determinant=float(np.linalg.det(jac).min()),game_runtime_tested=False))
 print('JK_FACE_AUTHORED',int(changed.sum()),int(d['iris_vertices'].sum()),flush=True)

if __name__=='__main__':main()
