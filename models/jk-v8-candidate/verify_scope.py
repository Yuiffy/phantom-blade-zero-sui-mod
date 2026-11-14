import bpy,json,hashlib,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
SRC=Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod/models/jk-v7-candidate/sui-jk-hun-bound-v7.blend')
def load(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');me=ob.data
 return {'co':np.array([v.co[:] for v in me.vertices]),'uv':np.array([d.uv[:] for d in me.uv_layers.active.data]),'comp':np.array([d.value for d in me.attributes['source_component'].data]),'bag':np.array([d.value for d in me.attributes['backpack_vertex'].data]).astype(bool),'faces':[list(p.vertices) for p in me.polygons],'material_indices':[p.material_index for p in me.polygons],'bones':{b.name:{'parent':b.parent.name if b.parent else None,'matrix':np.array(b.matrix_local).tolist()} for b in arm.data.bones},'w':[{ob.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in me.vertices]}
a=load(SRC);b=load(ROOT/'sui-jk-hun-bound.blend')
for k in ['faces','material_indices','bones']:assert a[k]==b[k],k
assert np.array_equal(a['uv'],b['uv']) and np.array_equal(a['comp'],b['comp'])
mask=np.isin(a['comp'],[1,4,5,9,10,16,17,1001])|(a['co'][:,2]<100)|a['bag']
assert np.array_equal(a['co'][mask],b['co'][mask])
assert all(a['w'][i]==b['w'][i] for i in np.flatnonzero(mask))
report={'baseline':str(SRC),'vertices':len(b['co']),'triangles':len(b['faces']),'skeleton_parent_and_matrices_exactly_equal':True,'topology_uv_material_indices_exactly_equal':True,'lower_body_hands_skirt_lining_backpack_positions_weights_exactly_equal':True,'protected_vertices':int(mask.sum()),'source_contract_sha256':hashlib.sha256((ROOT/'source-render-contract.json').read_bytes()).hexdigest()}
(ROOT/'scope-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
