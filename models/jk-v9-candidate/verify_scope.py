"""Verify the scope against installed v8, including surviving triangle UVs."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
ROOT=Path(__file__).resolve().parent

def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 return o,m,a
ob,me,arm=snapshot(ROOT.parent/'tripo-refine-v8/sui-jk-hun-bound.blend')
ornament=json.loads((ROOT/'ornament-refinement.json').read_text())
removed={44}|set(ornament['removed_v8_components'])
old=np.array([v.co[:] for v in me.vertices]);comp=np.array([v.value for v in me.attributes['source_component'].data]);weights=[{ob.vertex_groups[g.group].name:float(g.weight) for g in v.groups} for v in me.vertices]
bones={b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}
faces={tuple(sorted(p.vertices)):(p.material_index,{v:me.uv_layers.active.data[l].uv.copy() for v,l in zip(p.vertices,p.loop_indices)}) for p in me.polygons if comp[p.vertices[0]] not in removed}
ob,me,arm=snapshot(ROOT/'sui-jk-hun-bound.blend')
ids=np.array([v.value for v in me.attributes['v8_vertex_index'].data]);new=np.array([v.co[:] for v in me.vertices]);src=np.array([v.vector[:] for v in me.attributes['source_rest_position'].data])
isnew=ids==-1;kept=~isnew
assert len(ids[kept])==len(set(ids[kept])) and set(ids[kept])==set(np.flatnonzero(~np.isin(comp,list(removed))))
newcomp=np.array([d.value for d in me.attributes['source_component'].data])
assert set(newcomp[isnew])=={100,101}
assert len(ids[isnew])==ornament['added_vertices']
assert {b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}==bones
moved=np.zeros(len(ids),bool);moved[kept]=np.linalg.norm(new[kept]-old[ids[kept]],axis=1)>1e-6
allowed=kept&(np.isin(newcomp,[4,5])|((newcomp==0)&(src[:,2]<.635)&(abs(src[:,0])>.105)))
assert not np.any(moved&~allowed)
assert len(me.polygons)==len(faces)+ornament['added_triangles']
seen=set();newfaces=0
for p in me.polygons:
 if any(isnew[v] for v in p.vertices):
  assert all(isnew[v] for v in p.vertices)
  assert len(set(newcomp[list(p.vertices)]))==1
  newfaces+=1;continue
 key=tuple(sorted(int(ids[v]) for v in p.vertices));mi,uv=faces[key];assert mi==p.material_index
 seen.add(key)
 for v,l in zip(p.vertices,p.loop_indices):assert np.max(abs(np.array(uv[int(ids[v])])-np.array(me.uv_layers.active.data[l].uv)))<1e-7
badges={57,58,60,61,62,63};changed_w=0
assert seen==set(faces) and newfaces==ornament['added_triangles']
for i,v in enumerate(me.vertices):
 oldid=ids[i];w={ob.vertex_groups[g.group].name:float(g.weight) for g in v.groups}
 if isnew[i]:
  assert w==({'thigh_l':1.} if newcomp[i]==100 else {'spine_04':1.})
  if newcomp[i]==100:assert 4<new[i,0]<17 and -6<new[i,1]<0 and 76<new[i,2]<84
  else:assert -18<new[i,0]<-7 and -11<new[i,1]<-5 and 126<new[i,2]<145
  continue
 err=max(abs(w.get(k,0)-weights[oldid].get(k,0)) for k in w.keys()|weights[oldid].keys())
 if err>1e-6:
  assert comp[oldid] in {4,5}|badges;changed_w+=1
 if comp[oldid] in badges:assert w=={'thigh_l' if new[i,0]>0 else 'thigh_r':1.}
report={'baseline':'JK v8','skeleton_parent_and_matrices_exactly_equal':True,'surviving_topology_uv_material_indices_exactly_equal':True,'removed_components':sorted(removed),'removed_vertices':int(np.isin(comp,list(removed)).sum()),'added_ornament_vertices':int(isnew.sum()),'added_ornament_triangles':newfaces,'new_ornaments_confined_to_attachment_bounds_and_bones':True,'moved_vertices':int(moved.sum()),'weight_changed_vertices':changed_w,'preserved_positions_only_hands_and_distal_sleeves_changed':True,'preserved_weights_only_hands_or_stocking_badges_changed':True,'head_neck_shoulders_skirt_leg_geometry_unchanged':True,'source_contract_sha256':hashlib.sha256((ROOT/'source-render-contract.json').read_bytes()).hexdigest()}
(ROOT/'scope-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
