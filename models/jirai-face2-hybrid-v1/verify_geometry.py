"""Exact source assertions replace the rejected eye-area design targets."""
from common import *
import numpy as np,collections
from PIL import Image

def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);a=np.load(FACE/'native/baseline-render.npz');b=np.load(PIN/'final-render.npz');c=np.load(REPO/'private/jirai-polish-v1/final-render.npz');s=np.load(ROOT/'author-selections.npz');r=read(ROOT/'author-report.json')
 p=d['positions'];t=d['indices'].reshape(-1,3);m=d['materials'];skin=m==0;reserve=np.isin(np.arange(len(p)),s['reserve']);normal_only=np.isin(np.arange(len(p)),s['mouth_shading']);halo=m==8
 assert np.array_equal(p[skin&~reserve],a['positions'][skin&~reserve])
 for key in ['packed_tangents','uv']:
  mask=skin&~reserve&(~normal_only if key=='packed_tangents' else True)
  assert np.array_equal(d[key][mask],a[key][mask]),key
 keep=(m[t[:,0]]==0);keep[s['slots']]=False
 assert np.array_equal(t[keep],a['indices'].reshape(-1,3)[keep])
 for material in [18,19]:
  mask=m==material
  for key in ['positions','packed_tangents','uv']:assert np.array_equal(d[key][mask],b[key][mask]),(material,key)
  mask=m[t[:,0]]==material;assert np.array_equal(t[mask],b['indices'].reshape(-1,3)[mask])
 for key in ['positions','packed_tangents']:assert np.array_equal(d[key][halo|reserve],c[key][halo|reserve])
 other=~(skin|halo)
 for key in ['positions','packed_tangents','uv']:assert np.array_equal(d[key][other],b[key][other])
 untouched=m[t[:,0]]!=0;assert np.array_equal(t[untouched],b['indices'].reshape(-1,3)[untouched])
 assert np.array_equal(d['uv'][:,1],b['uv'][:,1]);assert np.isfinite(p).all()
 selected=s['mouth_shading'];normal=d['packed_tangents'][selected,4:7].view('i1').astype(float)/127;tangent=d['packed_tangents'][selected,:3].view('i1').astype(float)/127
 assert np.max(abs(np.linalg.norm(normal,axis=1)-1))<.014 and np.max(abs(np.sum(normal*tangent,axis=1)))<.025
 # Weld only for incidence checks; the native vertex/weight records remain
 # distinct and are independently compared after packaging.
 _,inv=np.unique(np.round(p,4),axis=0,return_inverse=True);directions=collections.defaultdict(list)
 for face in inv[t[m[t[:,0]]==0]]:
  if len(set(face))<3:continue
  for aa,bb in zip(face,np.roll(face,-1)):directions[tuple(sorted((int(aa),int(bb))))].append(int(aa)<int(bb))
 rings=[];copies=dict(s['weight_copies'].tolist())
 for row in r['bridges']:
  for name in ['upper_original','lower_original']:
   ring=row[name]
   for aa,bb in zip(ring,np.roll(ring,-1)):
    incidence=directions[tuple(sorted((int(inv[aa]),int(inv[bb]))))];assert len(incidence)==2 and incidence[0]!=incidence[1]
   rings.append(dict(side=row['side'],ring=name,closed_edges=len(ring)))
  for idx in row['new_vertices']:assert np.array_equal(p[idx],p[copies[idx]])
 atlas=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'));original=np.array(Image.open(REPO/'private/jirai-face-v2/T_Jirai_Base.png').convert('RGB'));x,y=r['arm_tile_xy'];changed=np.any(atlas!=original,2);changed[y-8:y+9,x-8:x+9]=False;assert not changed.any()
 # Every retained original Skin triangle continues to sample original pixels.
 import cv2
 mask=np.zeros((8192,8192),np.uint8)
 for face in t[(m[t[:,0]]==0)&~np.isin(t,s['reserve']).any(1)]:cv2.fillConvexPoly(mask,np.rint(d['uv'][face,0].astype(float)*8191).astype('i4'),255)
 assert not mask[y-8:y+9,x-8:x+9].any()
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),face2_skin_geometry_indices_uv_exact_except_arm_reserve=True,face2_socket_lash_positions_frames_uv_indices_exact=True,face2_mouth_positions_uv_indices_albedo_exact=True,mouth_shading_only_vertices=len(s['mouth_shading']),face3_iris_sclera_positions_frames_uv_indices_exact=True,polish_halo_and_arm_geometry_frames_exact=True,closed_arm_boundaries=rings,skin_weight_copy_count=len(copies),uv1_exact=True,retained_hair_outfit_and_other_material_geometry_exact=True,atlas_changes_only_unused_arm_tile=True,game_runtime_tested=False))
 print('HYBRID_GEOMETRY_VERIFIED',final,flush=True)

if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
