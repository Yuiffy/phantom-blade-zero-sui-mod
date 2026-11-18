"""Copy declared author inputs into a new isolated workspace, never installed files."""
import json,shutil,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];B=R/'private/jirai-skirt-recovery-v1';W=R/'private/jirai-skirt-shape-v1';V=W/'variant'
assert not (V/'ue/ProjectPBZ/ProjectPBZ.uproject').exists(),'Workspace already prepared'
V.mkdir(parents=True,exist_ok=True)
for name in ['binding-report.json','cloth-spec.json','game-materials.json','intended-reference-skeleton.json','pose-contract.json','editor-tools-build.json','surface-inspection.npz']:
 shutil.copy2(B/name,W/name)
for p in B.glob('component-*.json'):shutil.copy2(p,W/p.name)
for name in ['textures','research']:shutil.copytree(B/name,W/name,dirs_exist_ok=True)
for name in ['material-spec.json','source-spec.json']:
 p=B/'variant'/name;(V/name).write_text(p.read_text().replace('jirai-skirt-recovery-v1','jirai-skirt-shape-v1'),encoding='utf8')
shutil.copytree(B/'variant/shoulder-rig',V/'shoulder-rig')
src=B/'variant/ue/ProjectPBZ';dst=V/'ue/ProjectPBZ';dst.mkdir(parents=True)
shutil.copy2(src/'ProjectPBZ.uproject',dst/'ProjectPBZ.uproject')
for name in ['Config','Content','Plugins']:
 shutil.copytree(src/name,dst/name,ignore=shutil.ignore_patterns('Intermediate','Saved','DerivedDataCache','.vs','obj'))
selection=json.loads((B/'selection.json').read_text());selection.update(inherited_from=str(B/'selection.json'),inherited_selection_sha256=hashlib.sha256((B/'selection.json').read_bytes()).hexdigest(),geometry_changed_requires_fresh_tests=True)
(W/'selection.json').write_text(json.dumps(selection,indent=2))
print('SHAPE_WORKSPACE_PREPARED')
