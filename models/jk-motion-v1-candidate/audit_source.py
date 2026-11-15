import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data;m.calc_loop_triangles()
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in m.vertices]
assert all(w and abs(sum(w.values())-1)<1e-5 for w in weights)
assert len(a.data.bones)==264 and len(m.loop_triangles)==69041+sum(c['triangles'] for c in json.loads((R/'source-preparation.json').read_text())['simulation_cages'])
assert all(t.area>1e-9 for t in m.loop_triangles)
components=np.array([d.value for d in m.attributes['source_component'].data]);original=np.flatnonzero(components<2000)
v11=json.loads((R.parent/'tripo-refine-v11/source-render-contract.json').read_text())
assert len(original)==len(v11['positions_blender_cm'])==35402
assert np.max(np.abs(np.array([v.co[:] for v in m.vertices])[original]-np.array(v11['positions_blender_cm'])))==0
assert [weights[i] for i in original]==v11['influences']
contract={'positions_blender_cm':[v.co[:] for v in m.vertices],'influences':weights,'bones':[b.name for b in a.data.bones],'source_components':components.tolist()}
(R/'source-render-contract.json').write_text(json.dumps(contract))
print('MOTION_SOURCE_AUDIT_OK',len(m.vertices),len(m.loop_triangles),'unchanged_visible_vertices',len(original))
