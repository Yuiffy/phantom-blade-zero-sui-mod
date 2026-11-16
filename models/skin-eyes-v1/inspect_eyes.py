import bpy, json
import numpy as np
from pathlib import Path

R = Path(__file__).resolve().parents[2]
W = R / 'private/skin-eyes-v1'; W.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R / 'private/jirai-detail-v1/sui-jirai-motion.blend'))
o = next(x for x in bpy.context.scene.objects if x.type == 'MESH')
m = o.data
p = np.array([v.co[:] for v in m.vertices])
c = np.array([v.value for v in m.attributes['source_component'].data])
rows = []
for cid in sorted(set(c)):
    ids = np.where(c == cid)[0]
    q = p[ids]
    if q[:,2].max() < 150: continue
    mats = sorted({m.materials[f.material_index].name for f in m.polygons if c[f.vertices[0]] == cid})
    rows.append(dict(component=int(cid), vertices=len(ids), minimum=q.min(axis=0).tolist(), maximum=q.max(axis=0).tolist(), materials=mats))
(W / 'eye-inspection.json').write_text(json.dumps(rows, indent=2))
np.savez_compressed(W / 'surface-inspection.npz', points=p, components=c,
    triangles=np.array([tuple(t.vertices) for t in m.loop_triangles]))
print(json.dumps(rows, indent=2))
