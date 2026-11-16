import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
p=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)
comp=np.array([v.value for v in m.attributes['source_component'].data]);W=np.zeros((len(p),len(o.vertex_groups)))
for v in m.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
mask=(comp[edges]==930).all(1)&(length>.02)
def metrics(weights):
 for j,g in enumerate(o.vertex_groups):
  g.remove(np.where(comp==930)[0].tolist())
  for i in np.where((comp==930)&(weights[:,j]>1e-7))[0]:g.add([int(i)],float(weights[i,j]),'REPLACE')
 out=[]
 for angle in [35,70]:
  for b in a.pose.bones:b.matrix_basis=Matrix.Identity(4);b.rotation_mode='QUATERNION'
  for s in ['l','r']:
   for f in ['index','middle','ring','pinky']:
    for i in [1,2,3]:a.pose.bones[f'{f}_{i:02d}_{s}'].rotation_quaternion=Quaternion((0,0,1),math.radians(angle if s=='l' else -angle))
  bpy.context.view_layer.update();ob=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ob.to_mesh();q=np.array([v.co[:] for v in me.vertices]);ob.to_mesh_clear()
  ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(length,1e-8);ix=np.where(mask)[0];worst=ix[np.argsort(ratio[ix])[-8:]]
  out.append({'angle':angle,'p99':float(np.percentile(ratio[mask],99)),'max':float(ratio[mask].max()),'over1_6':int((ratio[mask]>1.6).sum()),'worst':[{'edge':edges[k].tolist(),'ratio':float(ratio[k]),'positions':p[edges[k]].tolist(),'weights':[{o.vertex_groups[j].name:float(weights[i,j]) for j in np.where(weights[i]>1e-5)[0]} for i in edges[k]]} for k in worst]})
 return out
neighbors=[[] for _ in p]
for i,j in edges:
 if comp[i]==comp[j]==930:neighbors[i].append(j);neighbors[j].append(i)
out=[]
for factor,iterations in [(0,0),(.35,1),(.35,2),(.35,4),(.5,4),(.5,8)]:
 w=W.copy()
 for _ in range(iterations):
  z=w.copy()
  for i in np.where(comp==930)[0]:
   if neighbors[i]:z[i]=w[i]*(1-factor)+w[neighbors[i]].mean(0)*factor
  w=z
 out.append({'factor':factor,'iterations':iterations,'metrics':metrics(w)})
(R/'hand-smoothing-probe.json').write_text(json.dumps(out,indent=2))
print('PROBE',json.dumps([{k:v for k,v in x.items() if k!='metrics'}|{'metrics':[{k:v for k,v in z.items() if k!='worst'} for z in x['metrics']]} for x in out]))
