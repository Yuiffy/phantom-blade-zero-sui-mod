"""Validate shape preservation, seam continuity, iris isolation and pixel coverage."""
from common import *
import numpy as np
from PIL import Image

def main(preflight=False):
 a=np.load(ROOT/'before.npz');b=np.load(ROOT/('patched-render.npz' if preflight else 'final-render.npz'))
 old=a['positions'];new=b['positions'];c=b['components'];changed=np.any(old!=new,axis=1);iris=np.isin(c,[40,41])
 assert np.all(c[changed]==0) and np.all(old[changed,2]<175.4)
 lips=(c==36)|((c==0)&(abs(old[:,0]+.4195)<2.7)&(old[:,2]>170.6)&(old[:,2]<173.8)&(old[:,1]>1.5))
 eyes=(old[:,2]>=175.4)&(old[:,2]<183.5)&(old[:,1]>0)&(a['materials']==0)
 assert np.array_equal(old[lips|eyes],new[lips|eyes])
 assert np.array_equal(a['packed_tangents'][lips|eyes],b['packed_tangents'][lips|eyes])
 for key in ['indices','materials']:assert np.array_equal(a[key],b[key])
 assert np.array_equal(a['uv'][~iris],b['uv'][~iris])
 assert np.array_equal(a['packed_tangents'][~changed],b['packed_tangents'][~changed])
 assert np.array_equal(a['packed_tangents'][:,[3,7]],b['packed_tangents'][:,[3,7]])
 tri=a['indices'].reshape(-1,3);target=tri[np.any(changed[tri],axis=1)]
 fn=lambda p:np.cross(p[target[:,1]]-p[target[:,0]],p[target[:,2]]-p[target[:,0]])
 f0,f1=fn(old),fn(new);size=np.linalg.norm(f0,axis=1);valid=size>1e-6
 cos=np.sum(f0[valid]*f1[valid],axis=1)/(size[valid]*np.linalg.norm(f1[valid],axis=1));assert cos.min()>.90
 area=np.linalg.norm(f1[valid],axis=1)/size[valid];assert area.min()>.6
 edges=np.unique(np.sort(np.concatenate([target[:,[0,1]],target[:,[1,2]],target[:,[2,0]]]),axis=1),axis=0)
 l0=np.linalg.norm(old[edges[:,0]]-old[edges[:,1]],axis=1);l1=np.linalg.norm(new[edges[:,0]]-new[edges[:,1]],axis=1);ratio=l1[l0>1e-5]/l0[l0>1e-5];assert ratio.min()>.6 and ratio.max()<1.4
 _,ids=np.unique(old,axis=0,return_inverse=True);spread=0.
 for axis in range(3):
  lo=np.full(ids.max()+1,np.inf);hi=np.full_like(lo,-np.inf);delta=new[:,axis]-old[:,axis]
  np.minimum.at(lo,ids,delta);np.maximum.at(hi,ids,delta);spread=max(spread,float((hi-lo).max()))
 assert spread<1e-5
 sel=np.load(ROOT/'author-selections.npz');occ=sel['occupancy']
 src=np.array(Image.open(PAT/'jk-after.png').convert('RGB'));dst=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'));assert np.array_equal(src[occ>0],dst[occ>0])
 uv=b['uv'][:,0].astype(float);faces=tri[iris[tri[:,0]]];assert np.all(iris[faces])
 samples=np.rint(uv[faces].mean(1)*8191).astype(int);rgb=dst[samples[:,1],samples[:,0]];assert np.all(rgb[:,0]>rgb[:,1]*1.1)
 atlas=read(ROOT/'atlas-report.json');ox,oy=atlas['isolated_patch_origin'];side=atlas['isolated_patch_size'];px=uv[iris]*8191
 assert np.all(px.min(0)>[ox+8,oy+8]) and np.all(px.max(0)<[ox+side-8,oy+side-8])
 report=dict(passed=True,final_container_readback=not preflight,native_render_sha256=sha(ROOT/('patched-render.npz' if preflight else 'final-render.npz')),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),position_vertices=int(changed.sum()),iris_uv_vertices=int(iris.sum()),eyes_lashes_brows_smile_positions_and_frames_exact=True,all_other_uv_and_material_slots_exact=True,original_occupied_texels_exact=True,iris_triangle_sample_count=len(faces),min_triangle_normal_dot=float(cos.min()),min_triangle_area_ratio=float(area.min()),edge_ratio=[float(ratio.min()),float(ratio.max())],max_seam_spread_cm=spread,game_runtime_tested=False)
 write(ROOT/('geometry-preflight.json' if preflight else 'geometry-verification.json'),report);print('JK_GEOMETRY_VERIFIED',report['position_vertices'],float(cos.min()),flush=True)

if __name__=='__main__':main(sys.argv[1:]==['preflight'])
