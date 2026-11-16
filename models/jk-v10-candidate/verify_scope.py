"""Independently compare v10 to the completed v9 checkpoint."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parent
def snap(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 return {'co':np.array([v.co[:] for v in m.vertices]),'src':np.array([d.vector[:] for d in m.attributes['source_rest_position'].data]),'comp':np.array([d.value for d in m.attributes['source_component'].data]),'ids':np.array([d.value for d in m.attributes['v8_vertex_index'].data]),'faces':[tuple(p.vertices) for p in m.polygons],'mi':[p.material_index for p in m.polygons],'uv':np.array([d.uv[:] for d in m.uv_layers.active.data]),'w':[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups} for v in m.vertices],'bones':{b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in a.data.bones}}
old=snap(ROOT.parent/'tripo-refine-v9/sui-jk-hun-bound.blend');new=snap(ROOT/'sui-jk-hun-bound.blend')
for k in ['src','comp','ids','uv']:assert np.array_equal(old[k],new[k]),k
for k in ['faces','mi','bones']:assert old[k]==new[k],k
x,y,z=new['src'].T
allowed=(new['comp']==0)&(new['ids']>=0)&(z>.585)&(z<.760)&(x<-.025)&(x>-.160)&(y>-.075)
moved=np.linalg.norm(new['co']-old['co'],axis=1)>1e-6
changed=np.array([max(abs(a.get(k,0)-b.get(k,0)) for k in a.keys()|b.keys())>1e-6 for a,b in zip(old['w'],new['w'])])
assert not np.any((moved|changed)&~allowed)
for w in new['w']:assert len(w)<=8 and abs(sum(w.values())-1)<1e-5 and min(w.values())>=0
report={'baseline':'JK v9 ce1a1de','skeleton_parent_and_matrices_exactly_equal':True,'topology_UV_material_indices_and_provenance_exactly_equal':True,'moved_vertices':int(moved.sum()),'weight_changed_vertices':int(changed.sum()),'changes_confined_to_right_proximal_component0':True,'head_hands_legs_skirt_bag_and_accessories_geometry_and_weights_unchanged':True,'max_position_change_cm':float(np.linalg.norm(new['co']-old['co'],axis=1).max()),'source_contract_sha256':hashlib.sha256((ROOT/'source-render-contract.json').read_bytes()).hexdigest()}
(ROOT/'scope-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
