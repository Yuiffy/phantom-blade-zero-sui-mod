"""Inspect the final source shorts topology and opaque material contract."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-shape-v1'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
c=[d.value for d in m.attributes['source_component'].data]
contract=json.loads((W/'source-render-contract.json').read_text())
assert np.array_equal(np.array(contract['positions_blender_cm']),np.array([v.co[:] for v in m.vertices]))
used={i for f in m.polygons for i in f.vertices}
assert contract['used_vertices']==[i in used for i in range(len(m.vertices))]
contract['components']=c;(W/'source-render-contract.json').write_text(json.dumps(contract))
faces=[f for f in m.polygons if all(c[i]==920 for i in f.vertices)]
assert faces and all(m.materials[f.material_index].name=='MI_Jirai_ShortLining' for f in faces)
# The hip wall is convex above 115 cm. Check actual outward winding, so the
# interior-cap removal cannot silently use reversed garment normals.
orientation=[]
for face in faces:
 if 115<face.center.z<130:
  radial=np.array([face.center.x,face.center.y-5.5,0]);orientation.append(float(np.dot(radial,np.array(face.normal))))
assert orientation and min(orientation)>0,'Safety-short hip normals face inward'

edges=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%len(f.vertices)]))) for f in faces for i in range(len(f.vertices)))
assert all(n in [1,2] for n in edges.values()),'Nonmanifold shorts'
adj=defaultdict(set);connected=defaultdict(set)
for (a,b),n in edges.items():
 connected[a].add(b);connected[b].add(a)
 if n==1:adj[a].add(b);adj[b].add(a)
assert all(len(v)==2 for v in adj.values()),'Open crotch seam'
def parts(graph):
 seen=set();out=[]
 for start in graph:
  if start in seen:continue
  todo=[start];seen.add(start);part=[]
  while todo:
   i=todo.pop();part.append(i)
   for j in graph[i]-seen:seen.add(j);todo.append(j)
  out.append(part)
 return out
assert len(parts(connected))==1,'Shorts must have a continuous crotch'
loops=parts(adj);assert len(loops)==3,'Only waist and two leg openings are allowed'
rows=[]
for loop in loops:
 p=np.array([m.vertices[i].co[:] for i in loop]);rows.append(dict(vertices=len(loop),minimum=p.min(0).tolist(),maximum=p.max(0).tolist()))
assert sum(x['minimum'][2]>124 for x in rows)==1
assert sum(x['maximum'][2]<104 for x in rows)==2
material=next(x for x in json.loads((W/'game-materials.json').read_text()) if x['slot']=='MI_Jirai_ShortLining')
assert material['base_color_linear'][3]==1 and max(material['base_color_linear'][:3])<.02
out=dict(upper_hip_outward_normal_min_dot=min(orientation),passed=True,continuous_crotch=True,one_connected_surface=True,boundary_loops=rows,opaque_black=True,material=material,fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),game_runtime_tested=False)
(W/'coverage-verification.json').write_text(json.dumps(out,indent=2));print('CONTINUOUS_OPAQUE_SHORTS_VERIFIED')
