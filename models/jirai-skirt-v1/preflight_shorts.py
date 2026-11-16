"""Diagnostic only: try revised shorts over previous cooked cloth frames.

This deliberately does not write shipping evidence or claim cooked validation.
The final candidate must be rebuilt and independently reconstructed afterwards.
"""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';V=W/'variant'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles()
c=np.array([d.value for d in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);ids=np.where(c==920)[0]
tri=[tuple(t.vertices) for t in m.loop_triangles];slots=[m.materials[t.material_index].name for t in m.loop_triangles]
skin=[t for t,s in zip(tri,slots) if s=='MI_Jirai_Skin' and all(c[i]==5 for i in t)]
skirt=[t for t,s in zip(tri,slots) if s=='MI_Jirai_Skirt'];opaque=[t for t in tri if all(c[i]<2000 for i in t)];eligible=set(skin+skirt)
edges=sorted({tuple(sorted((t[i],t[j]))) for t in skin for i,j in [(0,1),(1,2),(2,0)] if all(78<rest[k,2]<119 for k in [t[i],t[j]])})
bones=json.loads((V/'import-report.json').read_text())['actual_reference_bones'];ref=[];uses={}
for b in bones:
 q=b['q'];a=Matrix.LocRotScale(Vector(b['t']),Quaternion((q[3],*q[:3])),Vector((1,1,1)));ref.append(ref[b['parent']]@a if b['parent']>=0 else a)
for i in ids:
 for g in m.vertices[int(i)].groups:uses.setdefault(o.vertex_groups[g.group].name,[]).append((i,g.weight))
directions=[Vector((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e))) for a in np.linspace(0,math.tau,16,endpoint=False) for e in np.radians([0,20,45,70])]
report={}
for profile in ['diagonal-crouch','lunge-right','wide-crouch','crouch','run','lunge-left']:
 frames=np.load(V/('articulation-'+profile+'-surface.npz'))['source_frames'];sim=json.loads((V/('articulation-'+profile+'.json')).read_text());rows=[]
 for fi,f in enumerate(sim['frames']):
  p=frames[fi].copy();short=np.zeros_like(rest);rp=rest.copy();rp[:,1]*=-1
  for bi,b in enumerate(bones):
   if b['name'] not in uses:continue
   t=f['component_bones'][bi];a=np.array(Matrix.LocRotScale(Vector(t[:3]),Quaternion((t[6],*t[3:6])),Vector((1,1,1)))@ref[bi].inverted());u=np.array(uses[b['name']]);ix=u[:,0].astype(int);short[ix]+=(rp[ix]@a[:3,:3].T+a[:3,3])*u[:,1,None]
  short[:,1]*=-1;p[ids]=short[ids]
  tree=BVHTree.FromPolygons([Vector(v) for v in p],skirt,all_triangles=True);oc=BVHTree.FromPolygons([Vector(v) for v in p],opaque,all_triangles=True);visible=[]
  for i,j in edges:
   d=Vector(p[j]-p[i]);length=d.length
   if length<.01:continue
   hit,_,_,distance=tree.ray_cast(Vector(p[i]),d/length,length)
   if hit is None or not .015<distance<length-.015:continue
   for direction in directions:
    first,_,face,depth=oc.ray_cast(hit+direction*200,-direction,200.05)
    if first is not None and opaque[face] in eligible and 199.92<=depth<=200.015:visible.append([int(i),int(j)]);break
  rows.append(dict(step=f['step'],visible=visible))
 report[profile]=rows;print('PREFLIGHT_ONLY',profile,max(len(x['visible']) for x in rows),flush=True)
(W/'shorts-preflight-diagnostic.json').write_text(json.dumps(report,indent=2))
