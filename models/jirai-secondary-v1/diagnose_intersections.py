import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';V=W/'variant'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles();comp=np.array([x.value for x in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);slots=[m.materials[t.material_index].name for t in m.loop_triangles]
skin_tri=[tuple(t) for t in tri if all(comp[i]==5 for i in t)];skirt_tri=[tuple(t) for t,slot in zip(tri,slots) if slot=='MI_Jirai_Skirt'];edges=sorted({tuple(sorted((int(t[i]),int(t[j])))) for t in skin_tri for i,j in [(0,1),(1,2),(2,0)] if all(78<rest[k,2]<109 for k in [t[i],t[j]])})
reports={}
for profile in ['crouch','run']:
 data=np.load(V/('articulation-'+profile+'-surface.npz'));p=data['source_frames'][10 if profile=='crouch' else 9];bvh=BVHTree.FromPolygons([Vector(a) for a in p],skirt_tri,all_triangles=True);hits=[]
 for a,b in edges:
  delta=Vector(p[b]-p[a]);length=delta.length
  if length<.01:continue
  hit,normal,face,dist=bvh.ray_cast(Vector(p[a]),delta/length,length)
  if hit is not None and .015<dist<length-.015:hits.append({'edge':[a,b],'rest_mid':((rest[a]+rest[b])/2).tolist(),'intersection':list(hit),'skirt_components':[int(comp[i]) for i in skirt_tri[face]]})
 reports[profile]=hits
(V/'intersection-diagnosis.json').write_text(json.dumps(reports,indent=2));print('INTERSECTION_DIAGNOSED')
