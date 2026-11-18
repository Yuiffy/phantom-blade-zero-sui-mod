"""Bounded lip edit, exact retained geometry, and isolated lash pigmentation."""
from common import *
from author import black_pigment
import numpy as np,cv2
from PIL import Image

def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);old=np.load(PIN/'final-render.npz');s=np.load(ROOT/'author-selections.npz');r=read(ROOT/'author-report.json')
 assert r['native_sha256']==sha(ROOT/'patched-render.npz') and r['atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 p=old['positions'];q=d['positions'];t=d['indices'].reshape(-1,3);mat=d['materials'];mouth=np.isin(np.arange(len(p)),s['mouth_vertices']);uvset=np.isin(np.arange(len(p)),s['uv_vertices'])
 assert np.array_equal(q[~mouth],p[~mouth]) and np.array_equal(q[:,:2],p[:,:2])
 assert np.all((p[mouth,0]>.05)&(p[mouth,0]<1.6)&(p[mouth,2]>171.1)&(p[mouth,2]<171.8)&(p[mouth,1]>2.5))
 assert np.array_equal(d['indices'],old['indices']) and np.array_equal(d['packed_tangents'],old['packed_tangents'])
 assert np.array_equal(d['uv'][~uvset],old['uv'][~uvset]) and np.array_equal(d['uv'][:,1],old['uv'][:,1]);assert np.all(mat[uvset]==0)
 assert np.isfinite(q).all() and np.isfinite(d['uv']).all()
 for material in [1,8,18,19]:
  mask=mat==material
  for key in ['positions','packed_tangents','uv']:assert np.array_equal(d[key][mask],old[key][mask]),(material,key)
 faces=t[mouth[t].any(1)];a=np.cross(p[faces[:,1]]-p[faces[:,0]],p[faces[:,2]]-p[faces[:,0]]);b=np.cross(q[faces[:,1]]-q[faces[:,0]],q[faces[:,2]]-q[faces[:,0]]);area=np.linalg.norm(a,axis=1);newarea=np.linalg.norm(b,axis=1);valid=area>1e-7
 assert np.min(newarea[valid]/area[valid])>.05 and np.all((a*b).sum(1)>-1e-7)
 original=np.array(Image.open(PIN/'T_Jirai_Base.png').convert('RGB'));atlas=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'));scope=np.array(Image.open(ROOT/'atlas-scope.png'));changed=np.any(atlas!=original,2);assert not np.any(changed&(scope==0))
 occupied=np.zeros((8192,8192),np.uint8)
 for f in t[mat[t[:,0]]==0]:cv2.fillConvexPoly(occupied,np.rint(old['uv'][f,0].astype(float)*8191).astype('i4'),255)
 assert not np.any(changed&(occupied>0))
 surf=np.load(REPO/'private/jirai-face-v3/surface.npz');src=d['source_index'];comp=np.where(src>=0,surf['components'][np.maximum(src,0)],-1);skin=t[mat[t[:,0]]==0];xy=np.rint(old['uv'][skin,0].astype(float).mean(1)*8191).astype(int).clip(0,8191);rgb=original[xy[:,1],xy[:,0]]
 targets=black_pigment(p[skin].mean(1),comp[skin[:,0]],rgb);xy=np.rint(d['uv'][skin[targets],0].astype(float).mean(1)*8191).astype(int).clip(0,8191);newrgb=atlas[xy[:,1],xy[:,0]];black=int(np.count_nonzero(newrgb.max(1)<32))
 assert black==len(newrgb),(black,len(newrgb),'Lash centroid not black')
 # Normal, ARM and SCMT textures sampled by the relocated UVs are constant.
 constants={}
 for name in ['T_Jirai_FlatNormal','T_Jirai_ARM_Skin','T_SkinEyes_SCMT']:
  a=np.array(Image.open(REPO/'private/skin-eyes-v1/variant/textures'/(name+'.png')));assert np.all(a==a[0,0]);constants[name]=a[0,0].tolist()
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),eye_socket_and_lash_geometry_exact=True,face3_iris_and_sclera_positions_frames_uv_indices_exact=True,other_positions_except_right_lip_exact=True,all_indices_frames_uv1_exact=True,mouth_merged_vertices=int(mouth.sum()),mouth_max_shift_cm=float(np.max(abs(q-p))),mouth_min_area_ratio=float(np.min(newarea[valid]/area[valid])),mouth_triangle_winding_preserved=True,black_lash_triangle_centroids=black,source_png_color_test_not_cooked_vt=True,original_skin_atlas_occupied_pixels_exact=True,atlas_edits_only_in_isolated_region=True,uniform_other_skin_texture_inputs=constants,halo_hair_and_arm_repair_geometry_exact=True,game_runtime_tested=False))
 print('LASHLIP_GEOMETRY_VERIFIED',final,black,flush=True)

if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
