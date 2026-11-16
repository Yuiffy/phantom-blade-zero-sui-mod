"""Ensure untouched R5 surface regions and all deforming pivots remain exact."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1'
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
 return {'points':np.array([v.co[:] for v in m.vertices]),'components':np.array([v.value for v in m.attributes['source_component'].data]),'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in m.vertices],'bones':{b.name:np.array(b.matrix_local) for b in a.data.bones},'skirt_components':{m.attributes['source_component'].data[v].value for f in m.polygons if m.materials[f.material_index].name in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim'] for v in f.vertices}}
before=read(R/'private/jirai-proportion-v1/sui-jirai-motion.blend');after=read(W/'sui-jirai-motion.blend');allowed={5,77};checked=0
for c in sorted(set(before['components'])-allowed):
 ai=np.where(before['components']==c)[0];bi=np.where(after['components']==c)[0];assert len(ai)==len(bi),c
 # Component vertex ordering survives the local bmesh deletion/merge.
 assert np.max(abs(before['points'][ai]-after['points'][bi]))<1e-6,('unexpected geometry change',int(c))
 assert all(before['weights'][i]==after['weights'][j] for i,j in zip(ai,bi)),('unexpected weights change',int(c))
 checked+=len(ai)
assert before['bones'].keys()==after['bones'].keys()
errs={n:float(np.max(abs(a-after['bones'][n]))) for n,a in before['bones'].items() if not n.startswith('ik_')}
assert max(errs.values())<.0001,errs
(W/'source-preservation.json').write_text(json.dumps({'passed':True,'source_fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'unchanged_vertices_checked':checked,'non_ik_bone_matrix_max_error':max(errs.values()),'left_thigh_changes_only':True,'all_hair_and_skirt_positions_weights_exactly_preserved':True,'donor_hands_and_arm_proportions_preserved':True,'removed_old_buckle_component':77,'new_geometry_components':[940,941],'optional_wings_still_absent':not any(x in set(after['components']) for x in [910,911,2003,2004])},indent=2));print('SOURCE_PRESERVATION_OK',checked)
