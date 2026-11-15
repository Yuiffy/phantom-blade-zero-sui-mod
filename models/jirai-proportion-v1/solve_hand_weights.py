"""Constrained local skin-weight repair against several diagnostic finger poses."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
ids=np.array([v.index for v in m.vertices if m.attributes['source_component'].data[v.index].value==930]);lookup={int(v):i for i,v in enumerate(ids)}
edges=np.array([[lookup[i],lookup[j]] for e in m.edges for i,j in [e.vertices[:]] if i in lookup and j in lookup]);p=np.array([m.vertices[i].co[:] for i in ids]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);keep=length>.02;edges=edges[keep];length=length[keep]
names=sorted({o.vertex_groups[g.group].name for i in ids for g in m.vertices[i].groups});W=np.zeros((len(ids),len(names)))
for vi,i in enumerate(ids):
 for g in m.vertices[i].groups:W[vi,names.index(o.vertex_groups[g.group].name)]=g.weight
W/=W.sum(1)[:,None];allowed=W>0
# Existing anatomical ownership is the constraint: do not leak weight into
# adjacent fingers. The native hand bone may take up unwanted webbing weight.
for i,pt in enumerate(p):allowed[i,names.index('hand_l' if pt[0]>0 else 'hand_r')]=True
transforms=[]
for angle,thumb in [(35,0),(70,0),(45,35)]:
 for b in a.pose.bones:b.matrix_basis=Matrix.Identity(4);b.rotation_mode='QUATERNION'
 for s in ['l','r']:
  for f in ['index','middle','ring','pinky','thumb']:
   for j in [1,2,3]:
    n=f'{f}_{j:02d}_{s}'
    if n in a.pose.bones:a.pose.bones[n].rotation_quaternion=Quaternion((0,0,1),math.radians((thumb if f=='thumb' else angle)*(1 if s=='l' else -1)))
 bpy.context.view_layer.update();t=[];hp=np.column_stack([p,np.ones(len(p))])
 for n in names:
  matrix=np.array(a.pose.bones[n].matrix@a.data.bones[n].matrix_local.inverted());t.append((hp@matrix.T)[:,:3]-p)
 transforms.append(np.stack(t,axis=1))
D=np.array(transforms);w=W.copy();mom=np.zeros_like(w);vel=np.zeros_like(w)
def project(x):
 # Euclidean simplex projection, limited to original anatomical influences.
 x=np.where(allowed,x,-1e5);u=np.sort(x,axis=1)[:,::-1];cs=np.cumsum(u,axis=1)-1;r=(u-cs/np.arange(1,len(names)+1)>0).sum(1);theta=cs[np.arange(len(w)),r-1]/r
 return np.maximum(x-theta[:,None],0)*allowed
for step in range(1,1601):
 grad=.004*(w-W)
 for d in D:
  q=p+np.einsum('vb,vbc->vc',w,d);e=q[edges[:,0]]-q[edges[:,1]];dist=np.linalg.norm(e,axis=1)
  excess=np.maximum(dist-length*1.48,0);g=e*(excess/np.maximum(dist,1e-8)/np.maximum(length,.12))[:,None]
  vg=np.zeros_like(p);np.add.at(vg,edges[:,0],g);np.add.at(vg,edges[:,1],-g);grad+=np.einsum('vc,vbc->vb',vg,d)/3
 grad*=allowed;mom=.9*mom+.1*grad;vel=.999*vel+.001*grad*grad;w=project(w-.002*(mom/(1-.9**step))/(np.sqrt(vel/(1-.999**step))+1e-8))
out=[]
for d in D:
 q=p+np.einsum('vb,vbc->vc',w,d);ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/length;out.append({'p99':float(np.percentile(ratio,99)),'max':float(ratio.max()),'over1_6':int((ratio>1.6).sum())})
donor_indices=[m.attributes['jk_hand_vertex'].data[i].value for i in ids]
report={'basis':'constrained original anatomical influences; 35/70 degree curl and 45 degree curl with thumb','poses':out,'max_weight_delta':float(abs(w-W).max()),'changed_vertices':int((abs(w-W).max(1)>.001).sum()),'weights':{str(di):{n:float(v) for n,v in zip(names,row) if v>1e-7} for di,row in zip(donor_indices,w)}}
(R/'hand-weight-repair.json').write_text(json.dumps(report));print('WEIGHT_REPAIR',json.dumps({k:v for k,v in report.items() if k!='weights'}))
