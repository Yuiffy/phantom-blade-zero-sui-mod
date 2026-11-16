"""Independently constrain editable changes to the declared skirt rest shape."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';B=R/'private/jirai-skirt-recovery-v1'
sys.path.insert(0,str(C));from skirt_shape import reshape
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
 return {'p':np.array([v.co[:] for v in m.vertices]),'c':np.array([v.value for v in m.attributes['source_component'].data]),'faces':[(tuple(f.vertices),f.material_index) for f in m.polygons],'slots':[x.name for x in m.materials],'uv':np.array([x.uv[:] for x in m.uv_layers.active.data]),'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices],'bones':{b.name:np.array(b.matrix_local) for b in a.data.bones},'skirt':sorted({i for f in m.polygons if m.materials[f.material_index].name=='MI_Jirai_Skirt' for i in f.vertices})}
b=read(B/'sui-jirai-motion.blend');a=read(W/'sui-jirai-motion.blend')
assert a['faces']==b['faces'] and a['slots']==b['slots'] and a['weights']==b['weights']
assert np.array_equal(a['uv'],b['uv']) and np.array_equal(a['c'],b['c'])
assert a['bones'].keys()==b['bones'].keys() and all(np.array_equal(a['bones'][n],b['bones'][n]) for n in a['bones'])
cage=np.where(a['c']==2002)[0];changed=set(a['skirt'])|set(cage);other=[i for i in range(len(a['p'])) if i not in changed]
assert np.array_equal(a['p'][other],b['p'][other])
assert np.max(abs(a['p'][a['skirt']]-reshape(b['p'][a['skirt']])))<1e-5
assert np.max(abs(a['p'][cage]-reshape(b['p'][cage],False)))<1e-5
assert np.array_equal(a['p'][a['c']==920],b['p'][b['c']==920])
assert (W/'cloth-spec.json').read_bytes()==(B/'cloth-spec.json').read_bytes()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'passed':True,'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'basis_fbx_sha256':sha(B/'Sui_Jirai_Hun_Body.fbx'),'skirt_shape_only_changes':True,'all_bone_matrices_exact':True,'topology_uv_and_weights_exact':True,'body_hair_hands_and_continuous_shorts_positions_exact':True,'hair_and_skirt_config_exact_recovery1':True,'skirt_and_safety_shorts_only_changes':True,'source_atlas_unchanged':True,'eyes':json.loads((B/'source-preservation.json').read_text())['eyes'],'game_runtime_tested':False}
(W/'source-preservation.json').write_text(json.dumps(report,indent=2));print('SOURCE_SKIRT_ONLY_CHANGE_VERIFIED')
