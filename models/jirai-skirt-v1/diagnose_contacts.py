import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';V=W/'variant'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));m=next(x for x in bpy.context.scene.objects if x.type=='MESH').data;m.calc_loop_triangles()
c=np.array([v.value for v in m.attributes['source_component'].data]);r=np.array([v.co[:] for v in m.vertices]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);slots=[m.materials[t.material_index].name for t in m.loop_triangles]
audit=json.loads((V/'articulated-surface-audit.json').read_text());out={}
for profile in audit:
 frames=np.load(V/('articulation-'+profile['profile']+'-surface.npz'))['source_frames'];out[profile['profile']]={}
 for kind,field in [('hair','hair_edges_crossing_garment'),('thigh','visible_thigh_edges_crossing_skirt')]:
  frame=max(profile['thigh_edge_intersections'],key=lambda f:f[field]);p=frames[frame['frame']]
  target=[tuple(t) for t,s in zip(tri,slots) if s in (['MI_Jirai_Blouse','MI_Jirai_Corset'] if kind=='hair' else ['MI_Jirai_Skirt'])]
  source=[t for t,s in zip(tri,slots) if (s in ['MI_Jirai_TailL','MI_Jirai_TailR','MI_Jirai_SideL','MI_Jirai_SideR'] if kind=='hair' else all(c[i]==5 for i in t))]
  edges=sorted({tuple(sorted((int(t[i]),int(t[j])))) for t in source for i,j in [(0,1),(1,2),(2,0)] if all(r[k,2]<170 if kind=='hair' else 78<r[k,2]<119 for k in [t[i],t[j]])})
  tree=BVHTree.FromPolygons([Vector(a) for a in p],target,all_triangles=True);hits=[]
  for a,b in edges:
   delta=Vector(p[b]-p[a]);length=delta.length
   if length<.01:continue
   hit,_,face,dist=tree.ray_cast(Vector(p[a]),delta/length,length)
   if hit is not None and .015<dist<length-.015:hits.append({'edge':[a,b],'source':int(c[a]),'target':int(c[target[face][0]]),'rest_mid':((r[a]+r[b])/2).tolist(),'intersection':list(hit),'garment_vertices':[int(i) for i in target[face]],'garment_vertices_rest':r[list(target[face])].tolist(),'garment_rest':r[list(target[face])].mean(0).tolist()})
  out[profile['profile']][kind]={'frame':frame['frame'],'step':frame['step'],'hits':hits}
(V/'contacts-diagnosis.json').write_text(json.dumps(out,indent=2));print('CONTACTS_DIAGNOSED')
