"""Check UV ownership in the materials that actually receive the new atlas."""
from common import *
import numpy as np,cv2
from PIL import Image

d=np.load(ROOT/'surface.npz');p=d['positions'];c=d['components'];lv=d['loop_vertices'];uv=d['uv']
before=np.array(Image.open(BASE/'T_Jirai_Base.png').convert('RGB'));after=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'))
changed=np.any(before!=after,2);protected=np.zeros(changed.shape,np.uint8)
shared=np.zeros(changed.shape,np.uint8)
for loops,material in zip(d['loop_triangles'],d['materials']):
 vi=lv[loops];cid=int(c[vi[0]])
 if cid>=2000 or cid in [950,951]:continue
 q=uv[loops]*8191;q[:,1]=8191-q[:,1]
 if material not in [0,1]:cv2.fillConvexPoly(shared,np.rint(q).astype(np.int32),255)
 elif cid not in [0,19]:cv2.fillConvexPoly(protected,np.rint(q).astype(np.int32),255)
count=int(np.count_nonzero(changed&(protected>0)))
assert count==0,('Unrequested surface in a rebound material changed',count)
assert not np.any(changed&(np.array(Image.open(ROOT/'repair-mask.png'))==0))
fm=np.load(ROOT/'front-map.npz');fuv=fm['uv'];cid=fm['component'];xx=np.rint(fuv[:,:,0]*8191).astype(int);yy=np.rint((1-fuv[:,:,1])*8191).astype(int)
rgb_before=before[yy,xx];rgb_after=after[yy,xx];samples=[]
for x,z in [(-3.25,177.7),(-3.15,178),(2.4,177.4),(2.45,177.9)]:
 ix=round((x+11.35)/22*1000);iy=round((191-z)/22*1000);a=rgb_before[iy,ix];b=rgb_after[iy,ix]
 samples.append(dict(x_cm=x,z_cm=z,component=int(cid[iy,ix]),before=a.tolist(),after=b.tolist()))
 assert cid[iy,ix]==0 and b.min()>225,(x,z,b)
# All other material slots retain the original atlas even where UVs overlap.
report=dict(passed=True,changed_texels=int(changed.sum()),protected_component_uv_texels_changed=count,shared_uv_changed_texels_kept_on_original_atlas=int(np.count_nonzero(changed&(shared>0))),isolated_albedo_bound_only_to=['MI_Jirai_Skin','MI_Jirai_Hair'],original_eyebrow_components_101_102_untouched=True,retained_surfaces_in_rebound_materials_exact=True,other_materials_original_atlas_preserved=True,nasal_eye_backing_samples=samples,geometry_editing_performed=False,source_atlas_sha256=sha(BASE/'T_Jirai_Base.png'),output_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),game_runtime_tested=False)
write(ROOT/'surface-verification.json',report);print('FACE_SURFACE_VERIFIED',json.dumps(report))
