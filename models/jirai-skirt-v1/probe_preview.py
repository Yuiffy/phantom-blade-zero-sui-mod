import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
W=Path(__file__).resolve().parents[2]/'private/jirai-skirt-v1';V=W/'variant'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));m=next(x for x in bpy.context.scene.objects if x.type=='MESH').data;m.calc_loop_triangles();c=[d.value for d in m.attributes['source_component'].data]
a=next(x for x in json.loads((V/'articulated-surface-audit.json').read_text()) if x['profile']=='crouch');p=np.load(V/'articulation-crouch-surface.npz')['source_frames'][a['rendered_frame']]
tri=[t for t in m.loop_triangles if c[t.vertices[0]]<2000];tree=BVHTree.FromPolygons([Vector(v) for v in p],[tuple(t.vertices) for t in tri],all_triangles=True)
pos=Vector((0,400,100));target=Vector((0,-5,96));rot=(target-pos).to_track_quat('-Z','Y');right=rot@Vector((1,0,0));up=rot@Vector((0,1,0));forward=rot@Vector((0,0,-1))
rows=[]
for x,y in [(450,400),(450,420),(420,430),(450,450),(450,510),(400,370),(350,450)]:
 origin=pos+right*((x/900-.5)*110)+up*((.5-y/900)*110);hit,n,idx,dist=tree.ray_cast(origin,forward,1000);t=tri[idx];rows.append(dict(pixel=[x,y],slot=m.materials[t.material_index].name,component=c[t.vertices[0]],rest_center=np.array([m.vertices[i].co[:] for i in t.vertices]).mean(0).tolist(),hit=list(hit)))
(W/'preview-probe.json').write_text(json.dumps(rows,indent=2));print(rows)
