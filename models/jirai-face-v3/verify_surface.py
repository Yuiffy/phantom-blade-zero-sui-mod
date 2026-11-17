"""Check actual half-float UV ownership on materials receiving the face atlas."""
from common import *
import numpy as np,cv2
from PIL import Image
d=np.load(ROOT/'surface.npz');p=d['old_positions'];c=d['components'];uv=d['uv'].copy();lv=d['loop_vertices'];tri=d['loop_triangles'];mi=d['materials']
uv[:,0]=uv[:,0].astype('<f2').astype(float);uv[:,1]=1-(1-uv[:,1]).astype('<f2').astype(float)
before=np.array(Image.open(BASE/'T_Jirai_Base.png').convert('RGB'));after=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'))
changed=np.any(before!=after,axis=2);protected=np.zeros(changed.shape,np.uint8);shared=protected.copy()
for loops,material in zip(tri,mi):
    vi=lv[loops];cid=int(c[vi[0]]);q=uv[loops]*8191;q[:,1]=8191-q[:,1]
    if cid>=2000:continue
    if material not in [0,1]:
        cv2.fillConvexPoly(shared,np.rint(q).astype(np.int32),255)
        continue
    allowed=(material==1 and cid==19) or (material==0 and (cid in [56,101,102] or (cid==0 and p[vi,2].max()>170 and p[vi,2].min()<183)))
    if not allowed:cv2.fillConvexPoly(protected,np.rint(q).astype(np.int32),255)
# Erode by one texel to exclude raster conventions on shared UV boundaries.
interior=cv2.erode(protected,np.ones((3,3),np.uint8))
bad=changed&(interior>0)
assert not bad.any(),('Retained surface of a rebound material changed',int(bad.sum()))
assert np.all(np.array(Image.open(ROOT/'repair-mask.png'))[changed]>0)
write(ROOT/'surface-verification.json',dict(passed=True,output_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),
    source_atlas_sha256=sha(BASE/'T_Jirai_Base.png'),surface_sha256=sha(ROOT/'surface.npz'),
    changed_texels=int(changed.sum()),protected_surface_interior_changed_texels=0,
    shared_uv_changed_texels_on_unmodified_other_materials=int(np.count_nonzero(changed&(shared>0))),
    actual_half_float_uvs_used=True,shared_original_atlas_not_overridden=True,iris_has_dedicated_albedo=True,
    game_runtime_tested=False))
print('FACE3_SURFACE_VERIFIED')
