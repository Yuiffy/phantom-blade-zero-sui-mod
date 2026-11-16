"""Independently verify every opaque coverage triangle in the final container."""
from pathlib import Path
import numpy as np, json
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v4'
src=np.load(R/'coverage-source.npz');co=src['positions'].copy();co[:,1]*=-1
expected=co[src['faces'][src['materials']==8]]
d=np.load(W/'independent/render-data.npz')
details=json.loads((W/'independent/cloth-native-details.json').read_text())
section,=[s for s in details['sections'] if s['slot']=='MI_JK_SafetyLining']
assert section['cloth_index']==-1 and not section['disabled']
ids=d['indices'][section['base_index']:section['base_index']+3*section['triangles']].reshape(-1,3)
actual=d['positions'][ids]
assert len(actual)==len(expected),(len(actual),len(expected))
dist,ix=cKDTree(actual.mean(1)).query(expected.mean(1),workers=1)
assert dist.max()<.001 and len(set(ix.tolist()))==len(ix)
max_corner=0.
for a,b in zip(expected,actual[ix]):
    closest=np.linalg.norm(a[:,None,:]-b[None,:,:],axis=2).min(1)
    max_corner=max(max_corner,float(closest.max()))
assert max_corner<.001
pose=json.loads((W/'coverage-pose-review.json').read_text())
repair=json.loads((R/'coverage-repair.json').read_text())
assert repair['one_waist_two_leg_openings'] and len(pose['views'])==4
report={'status':'final-container-opaque-coverage-triangles-passed',
 'opaque_triangles':len(actual),'all_coverage_triangle_centers_match':True,
 'max_corner_error_cm':max_corner,'source_boundary_loops':repair['boundary_loops'],
 'central_skin_backup_triangles':pose['protected_central_triangles'],
 'actual_game_animation_coverage_unverified':True,'runtime_tested':False}
(W/'coverage-final-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
