"""Fast diagnostic only: skinning without cloth, never a shipping gate."""
import bpy,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';clips=json.loads((W/'pose-contract.json').read_text())['clips'];report={}
for label,folder in [('before',R/'private/jirai-detail-v1'),('after',W)]:
 bpy.ops.wm.open_mainfile(filepath=str(folder/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles();arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
 rest=np.array([v.co[:] for v in m.vertices]);c=np.array([v.value for v in m.attributes['source_component'].data]);tri=[tuple(t.vertices) for t in m.loop_triangles];skirt=[tuple(t.vertices) for t in m.loop_triangles if m.materials[t.material_index].name=='MI_Jirai_Skirt'];edges=sorted({tuple(sorted((t[i],t[j]))) for t in tri if all(c[k]==5 for k in t) for i,j in [(0,1),(1,2),(2,0)] if all(78<rest[k,2]<119 for k in [t[i],t[j]])});weights={}
 for v in m.vertices:
  for g in v.groups:weights.setdefault(o.vertex_groups[g.group].name,[]).append((v.index,g.weight))
 native=json.loads((folder/'intended-reference-skeleton.json').read_text())['bones'];C=Matrix.Diagonal((1.,-1.,1.,1.));ref={b.name:np.array(b.matrix_local) for b in arm.data.bones};report[label]={}
 for profile,clip in clips.items():
  if profile=='head-arms':continue
  counts=[]
  for f in [33,51,75,105]:
   world=[]
   for b,key in zip(native,clip['keys'][f]):
    q=key['q'];local=C@Matrix.LocRotScale(Vector(b['t']),Quaternion((q[3],*q[:3])),Vector(b['s']))@C;world.append(world[b['parent']]@local if b['parent']>=0 else local)
   p=np.zeros_like(rest)
   for b,wmat in zip(native,world):
    name=b['name']
    if name not in weights:continue
    uses=np.array(weights[name]);ix=uses[:,0].astype(int);a=np.array(wmat)@np.linalg.inv(ref[name]);p[ix]+=(rest[ix]@a[:3,:3].T+a[:3,3])*uses[:,1,None]
   tree=BVHTree.FromPolygons([Vector(x) for x in p],skirt,all_triangles=True);hits=[]
   for a,b in edges:
    d=Vector(p[b]-p[a]);length=d.length
    if length<.01:continue
    hit,_,_,dist=tree.ray_cast(Vector(p[a]),d/length,length)
    if hit is not None and .015<dist<length-.015:hits.append([a,b])
   counts.append({'frame':f,'crossing_edges':len(hits),'rest_examples':[rest[e].tolist() for e in hits[:3]]})
  report[label][profile]=counts
(W/'skinning-only-diagnostic.json').write_text(json.dumps(report,indent=2));print('SKINNING_ONLY',json.dumps({k:{p:max(x['crossing_edges'] for x in a) for p,a in v.items()} for k,v in report.items()}))
