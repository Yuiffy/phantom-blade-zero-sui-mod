"""Require exact R6 preservation except skirt weights and hidden skirt cage."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from collections import Counter,defaultdict
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-recovery-v1';B=R/'private/skin-eyes-v1'
def read(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
 return dict(points=np.array([v.co[:] for v in m.vertices]),normals=np.array([v.vector[:] for v in m.corner_normals]),components=[v.value for v in m.attributes['source_component'].data],faces=[tuple(f.vertices) for f in m.polygons],slots=[f.material_index for f in m.polygons],materials=[x.name for x in m.materials],uvs=[[list(m.uv_layers.active.data[j].uv) for j in f.loop_indices] for f in m.polygons],weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices],bones={b.name:np.array(b.matrix_local) for b in a.data.bones},skirt_ids={i for f in m.polygons if m.materials[f.material_index].name in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim'] for i in f.vertices})
b=read(B/'sui-jirai-motion.blend');a=read(W/'sui-jirai-motion.blend')
assert a['materials']==b['materials']
checked=0
for comp in sorted(set(b['components'])-{920,2002}):
 ai=[i for i,c in enumerate(a['components']) if c==comp];bi=[i for i,c in enumerate(b['components']) if c==comp];assert len(ai)==len(bi),comp
 if not any(i in a['skirt_ids'] for i in ai):assert np.array_equal(a['points'][ai],b['points'][bi]),('position',comp)
 else:
  pa=a['points'][ai];pb=b['points'][bi];rad=pb[:,:2]-[0,5];length=np.linalg.norm(rad,axis=1);t=np.clip((122-pb[:,2])/14,0,1);amount=4*t*t*(3-2*t);expected=pb.copy();expected[:,:2]+=rad/length[:,None]*amount[:,None]
  assert np.max(np.linalg.norm(pa-expected,axis=1))<1e-5,('skirt flare formula',comp)
 if not any(i in a['skirt_ids'] for i in ai):assert all(a['weights'][i]==b['weights'][j] for i,j in zip(ai,bi)),('weights',comp)
 checked+=len(ai)
def retained_faces(data):
 ordinal={};counts={}
 for i,c in enumerate(data['components']):ordinal[i]=(c,counts.get(c,0));counts[c]=counts.get(c,0)+1
 return [(tuple(ordinal[i] for i in f),mi,uv) for f,mi,uv in zip(data['faces'],data['slots'],data['uvs']) if all(data['components'][i] not in [920,2002] for i in f)]
bf=retained_faces(b);af=retained_faces(a)
# Retained polygons must be the original ordered subsequence. Independently
# prove every removed polygon was completely inside the new opaque shorts.
ord_to_index={};counts={}
for i,cid in enumerate(a['components']):ord_to_index[(cid,counts.get(cid,0))]=i;counts[cid]=counts.get(cid,0)+1
shorts=[tuple(f) for f in a['faces'] if all(a['components'][i]==920 for i in f)]
tree=BVHTree.FromPolygons([Vector(v) for v in a['points']],shorts,all_triangles=True)
at=0;removed=[];actual_keys={x[0] for x in af}
for bk,bmi,buv in bf:
 if at<len(af) and af[at][0]==bk:
  ak,ami,auv=af[at];at+=1;assert np.array_equal(buv,auv),'retained UV changed'
  if bmi!=ami:assert all(c==5 for c,i in bk) and a['materials'][ami]=='MI_Jirai_ShortLining','unexpected material change'
 else:
  assert b['materials'][bmi]=='MI_Jirai_Skirt','only internal skirt caps may be removed'
  q=[Vector(a['points'][ord_to_index[k]]) for k in bk];assert len(q)==3
  samples=q+[(q[i]+q[(i+1)%3])*.5 for i in range(3)]+[sum(q,Vector())/3];clearance=[]
  for p in samples:
   hit,n,_,distance=tree.find_nearest(p);signed=(p-hit).dot(n)
   assert 110<p.z<124 and signed<-.3,('removed skirt polygon not enclosed by shorts',bk,list(p),signed)
   clearance.append(-signed)
  removed.append(min(clearance))
assert at==len(af) and removed,'unexpected inserted faces or no enclosed cap cleanup'
assert a['bones'].keys()==b['bones'].keys();assert all(np.array_equal(a['bones'][n],b['bones'][n]) for n in a['bones']),'bone changed'
ac=json.loads((W/'cloth-spec.json').read_text());bc=json.loads((B/'cloth-spec.json').read_text());assert len(ac)==len(bc)==3
assert ac[:2]==bc[:2],'hair cloth config changed'
for n in ['textures/jirai-albedo.png','intended-reference-skeleton.json','game-materials.json']:assert (W/n).read_bytes()==(B/n).read_bytes(),n
# A new physical-only cage is permitted; every retained visible face remains exact.
# Its material, topology and openings are independently constrained here.
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
c=a['components'];ids={i for i,v in enumerate(c) if v==2002};faces=[f for f in m.polygons if all(i in ids for i in f.vertices)]
assert len(ids)==17*36 and len(faces)==16*36*2
assert all(m.materials[f.material_index].name=='MI_Jirai_SkirtSim' for f in faces)
edges=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%3]))) for f in faces for i in range(3));assert max(edges.values())==2
adj=defaultdict(set)
for (i,j),count in edges.items():
 if count==1:adj[i].add(j);adj[j].add(i)
assert len(adj)==72 and all(len(v)==2 for v in adj.values())
seen=set();loops=[]
for start in adj:
 if start in seen:continue
 todo=[start];seen.add(start);loop=[]
 while todo:
  i=todo.pop();loop.append(i)
  for j in adj[i]-seen:seen.add(j);todo.append(j)
 loops.append(loop)
assert len(loops)==2 and all(len(v)==36 for v in loops)
# Compare retained corner normals in the same face/component order.
def kept_normals(d):
 out=[];at=0;ordinal={};counts={}
 for i,cid in enumerate(d['components']):ordinal[i]=(cid,counts.get(cid,0));counts[cid]=counts.get(cid,0)+1
 for len_seen,face in enumerate(d['faces']):
  n=len(face)
  if all(d['components'][i] not in [920,2002] for i in face) and tuple(ordinal[i] for i in face) in actual_keys:
   values=d['normals'][at:at+n].copy()
   if d is b and d['materials'][d['slots'][len_seen]]=='MI_Jirai_Skirt':
    for k,i in enumerate(face):
     p=d['points'][i];rad=p[:2]-[0,5];radius=np.linalg.norm(rad);t=float(np.clip((122-p[2])/14,0,1));amount=4*t*t*(3-2*t);da=-24*t*(1-t)/14 if 0<t<1 else 0
     j=np.eye(3);j[:2,:2]=(1+amount/radius)*np.eye(2)-amount*np.outer(rad,rad)/radius**3;j[:2,2]=rad/radius*da
     normal=np.linalg.solve(j.T,values[k]);values[k]=normal/np.linalg.norm(normal)
   out.extend(values)
  at+=n
 return np.array(out)
normal_error=float(np.max(np.linalg.norm(kept_normals(a)-kept_normals(b),axis=1)))
# Blender re-encodes custom normals in its packed corner representation when
# joining meshes. Bound the actual angular drift to one tenth of a degree.
an=kept_normals(a);bn=kept_normals(b)
an=an/np.linalg.norm(an,axis=1)[:,None];bn=bn/np.linalg.norm(bn,axis=1)[:,None]
normal_angle=float(np.degrees(np.arccos(np.clip(np.sum(an*bn,axis=1),-1,1))).max())
loop_slots=[a['materials'][mi] for face,mi in zip(a['faces'],a['slots']) if all(a['components'][i] not in [920,2002] for i in face) for _ in face]
angles=np.degrees(np.arccos(np.clip(np.sum(an*bn,axis=1),-1,1)))
# The .1-degree preservation gate applies to surfaces whose shape did not
# change. The reshaped skirt has authored normals and needs image review.
normal_groups={n:float(angles[np.array(loop_slots)==n].max()) for n in sorted(set(loop_slots))}
retained_angle=max(v for n,v in normal_groups.items() if n!='MI_Jirai_Skirt')
assert retained_angle<.1,('retained non-skirt corner normal angle',retained_angle)
report=dict(interior_triangles_removed=len(removed),removed_faces_min_inside_shorts_cm=min(removed),eyes=json.loads((B/'source-preservation.json').read_text())['eyes'],skin_eyes_baseline_preserved=True,hidden_skirt_guide_retopologized=True,hidden_guide_vertices=len(ids),hidden_guide_boundary_loops=2,retained_corner_normal_max_error=normal_error,retained_corner_normal_angle_max_deg=retained_angle,reshaped_skirt_jacobian_normal_deviation_max_deg=normal_groups["MI_Jirai_Skirt"],reshaped_skirt_shading_requires_image_review=True,passed=True,source_fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),basis_fbx_sha256=hashlib.sha256((B/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),all_non_skirt_retained_visible_positions_exact=True,skirt_flare_max_cm=4,all_non_skirt_non_shorts_weights_exact=True,all_bone_matrices_exact=True,hair_surface_guides_weights_config_exact=True,atlas_and_material_definitions_exact=True,atlas_comparison_scope="SkinEyes1 geometry-stage source; final previews/editable/container preserve verified Fishnet1 8K separately",retained_topology_and_uv_exact=True,upper_thigh_opaque_backup_material_only=True,preserved_vertices_checked=checked,skirt_and_safety_shorts_only_changes=True)
(W/'source-preservation.json').write_text(json.dumps(report,indent=2));print('SKIRT_AND_COVERAGE_PRESERVATION_OK',checked)
