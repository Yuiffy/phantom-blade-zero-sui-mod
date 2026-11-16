"""Source-aware synthetic hand, shoulder, wrist and rear skirt checks."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
from mathutils.bvhtree import BVHTree
REPO=Path(__file__).resolve().parents[2];R=REPO/'private/jirai-proportion-v1';out=[]
def make_tree(points,tri):return BVHTree.FromPolygons([Vector(p) for p in points],tri,all_triangles=True)
for tag,root in [('before',REPO/'private/jirai-v1'),('after',R)]:
 bpy.ops.wm.open_mainfile(filepath=str(root/'sui-jirai-motion.blend'))
 o=next(x for x in bpy.context.scene.objects if x.type=='MESH');arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data;m.calc_loop_triangles()
 comp=np.array([d.value for d in m.attributes['source_component'].data]);p=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)
 weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
 hands=np.array([sum(v for n,v in w.items() if n.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')))>.95 for w in weights]);emask=hands[edges].all(1)&(length>.02)
 skintri=[tuple(t.vertices) for t in m.loop_triangles if all(comp[v]==0 for v in t.vertices)]
 sleevetri=[tuple(t.vertices) for t in m.loop_triangles if all(comp[v] in [1,23,24,25,49,50] for v in t.vertices)]
 def reset():
  for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4);b.rotation_mode='QUATERNION'
 def rotate(n,axis,angle):
  b=arm.data.bones[n].matrix_local.to_quaternion();arm.pose.bones[n].rotation_quaternion=b.inverted()@Quaternion(Vector(axis),math.radians(angle))@b
 def posed():
  bpy.context.view_layer.update();e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();q=np.array([v.co[:] for v in me.vertices]);e.to_mesh_clear();assert np.isfinite(q).all();return q
 handrecords=[]
 for angle in [35,70]:
  reset()
  for side in ['l','r']:
   for finger in ['index','middle','ring','pinky']:
    for i in [1,2,3]:arm.pose.bones[f'{finger}_{i:02d}_{side}'].rotation_quaternion=Quaternion((0,0,1),math.radians(angle if side=='l' else -angle))
  q=posed();ratio=np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/np.maximum(length,1e-8)
  handrecords.append({'angle':angle,'edges':int(emask.sum()),'edge_ratio_p99':float(np.percentile(ratio[emask],99)),'edges_over_1_6':int((ratio[emask]>1.6).sum()),'max_ratio':float(ratio[emask].max())})
 shoulderrecords=[]
 for angle in [0,45,65,90]:
  reset();rotate('upperarm_l',(0,1,0),-angle);rotate('upperarm_r',(0,1,0),angle);q=posed();skin=make_tree(q,skintri);sleeve=make_tree(q,sleevetri);gaps=[]
  for side in ['l','r']:
   a=arm.pose.bones['upperarm_'+side].head;b=arm.pose.bones['lowerarm_'+side].head;u=(b-a).normalized();x=u.cross(Vector((0,1,0))).normalized();y=u.cross(x).normalized()
   for t in np.linspace(.10,.72,16):
    start=a*(1-t)+b*t
    for theta in np.linspace(0,2*math.pi,48,endpoint=False):
     direction=x*math.cos(theta)+y*math.sin(theta)
     sp,_,_,sd=skin.ray_cast(start,direction,12);cp,_,_,cd=sleeve.ray_cast(start,direction,12)
     if sp is not None and cp is not None:gaps.append(cd-sd)
  shoulderrecords.append({'raise':angle,'samples':len(gaps),'min_gap_cm':min(gaps) if gaps else None,'interpenetrating_samples':sum(g<-.05 for g in gaps),'p01_gap_cm':float(np.percentile(gaps,1)) if gaps else None})
 rearrecords=[]
 # Sample the actual upper hip patch against rays through the actual posed outer
 # skirt. These are reference/manual poses, not game physics or extracted clips.
 skirttri=[tuple(t.vertices) for t in m.loop_triangles if all(comp[v]==2 for v in t.vertices)]
 patch=(comp==5)&(p[:,2]>115)&(p[:,2]<130)&(abs(p[:,0])<14)&(p[:,1]>6)
 for left,right in [(0,0),(-45,25),(25,-45),(-60,40)]:
  reset();rotate('thigh_l',(1,0,0),left);rotate('thigh_r',(1,0,0),right);q=posed();tree=make_tree(q,skirttri);gaps=[]
  for pt in q[patch]:
   hit,_,_,_=tree.ray_cast(Vector((pt[0],80,pt[2])),Vector((0,-1,0)),120)
   if hit is not None:gaps.append(hit.y-pt[1])
  rearrecords.append({'thigh_angles':[left,right],'sampled_hip_points':len(gaps),'min_back_skirt_gap_cm':float(min(gaps)) if gaps else None,'outside_skirt':int(sum(g<-.05 for g in gaps))})
 out.append({'version':tag,'hand_curls':handrecords,'sleeve_contacts':shoulderrecords,'rear_skirt':rearrecords})
after=out[1]
(R/'revision-pose-diagnostic.json').write_text(json.dumps({'versions':out},indent=2))
assert max(x['edge_ratio_p99'] for x in after['hand_curls'])<1.6,after['hand_curls']
assert all(x['outside_skirt']==0 for x in after['rear_skirt']),after['rear_skirt']
report={'basis':'manual Blender diagnostic poses, not extracted game animations','versions':out,'rear_patch_containment_passed':True,'finger_edge_p99_under_1_6':True,'game_runtime_tested':False}
(R/'revision-pose-audit.json').write_text(json.dumps(report,indent=2));print('REVISION_AUDIT',json.dumps(report))
