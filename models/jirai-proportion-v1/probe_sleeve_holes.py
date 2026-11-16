import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;bm=bmesh.new();bm.from_mesh(m);comp=bm.verts.layers.int['source_component']
edges={e for e in bm.edges if e.is_boundary and all(v[comp]==1 for v in e.verts)};loops=[]
while edges:
 edge=edges.pop();todo=[edge];group={edge}
 while todo:
  e=todo.pop()
  for v in e.verts:
   for q in v.link_edges:
    if q in edges:edges.remove(q);group.add(q);todo.append(q)
 vs={v for e in group for v in e.verts};pts=[v.co for v in vs];center=sum(pts,Vector())/len(pts)
 loops.append({'edges':len(group),'center':list(center),'extent':[(max(p[i] for p in pts)-min(p[i] for p in pts)) for i in range(3)]})
(R/'sleeve-hole-probe.json').write_text(json.dumps(loops,indent=2));print('HOLES',json.dumps(loops))
