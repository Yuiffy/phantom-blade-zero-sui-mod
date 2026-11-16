"""Finite, manually posed polish checks; these are not PBZ game animations."""
import bpy,json,math,numpy as np,os
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parent
def load(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');return o,a
def reset(a):
 for b in a.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def curl(a):
 for side in ['l','r']:
  for finger in ['index','middle','ring','pinky']:
   for j in [1,2,3]:
    b=a.pose.bones[f'{finger}_{j:02d}_{side}'];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((0,0,1),math.radians(35 if side=='l' else -35))
 bpy.context.view_layer.update()
def deformed(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();p=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();return p
def stats(o):
 m=o.data;co=np.array([v.co[:] for v in m.vertices]);cp=np.array([d.value for d in m.attributes['source_component'].data]);e=np.array([e.vertices[:] for e in m.edges]);rest=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1);pose=deformed(o);ratio=np.linalg.norm(pose[e[:,0]]-pose[e[:,1]],axis=1)/np.maximum(rest,1e-8);sel=np.isin(cp[e[:,0]],[4,5])&np.isin(cp[e[:,1]],[4,5])&(rest>.03)
 outliers=[]
 for j in np.flatnonzero(sel&(ratio>1.6)):
  outliers.append({'vertices':e[j].tolist(),'rest_cm':float(rest[j]),'ratio':float(ratio[j]),'positions':co[e[j]].tolist()})
 return {'edges':int(sel.sum()),'p99':float(np.quantile(ratio[sel],.99)),'max':float(ratio[sel].max()),'over_1_6':int((ratio[sel]>1.6).sum()),'outliers':outliers}
o,a=load(ROOT.parent/'tripo-refine-v10/sui-jk-hun-bound.blend');curl(a);before=stats(o)
o,a=load(ROOT/'sui-jk-hun-bound.blend');reset(a);curl(a);after=stats(o)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.resolution_x=1100;sc.render.resolution_y=850;sc.render.resolution_percentage=100
def render(name,pos,target,scale):
 if os.environ.get('PBZ_DETAIL_STATS_ONLY'):return
 sc.camera.location=pos;sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale;sc.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
render('after-hand-curl',(130,-250,102),(52,-12,104),24)
reset(a)
for name,pos,target,scale in [('after-stockings',(0,-600,88),(0,0,88),48),('after-rear-skirt',(0,600,103),(0,7,103),60),('after-hand',(130,-250,102),(52,-12,104),24),('after-charm-front',(-12,-600,137),(-12,-7,137),24),('after-charm-side',(-600,-4,138),(-12,-4,138),24),('after-charm-threequarter',(-300,-400,139),(-12,-5,138),24)]:render(name,pos,target,scale)
# The anchor is interpolated on the true supporting triangle. Cross-section
# center is 1.3mm inside the strap at rest, and must keep following it.
m=o.data;cp=np.array([d.value for d in m.attributes['source_component'].data]);oldids=np.array([d.value for d in m.attributes['v10_vertex_index'].data]);data=json.loads((ROOT/'binding-report.json').read_text());lookup={int(v):i for i,v in enumerate(oldids) if v>=0};tri=[lookup[v] for v in data['anchor_face_v10_indices']];bary=np.array(data['anchor_barycentric']);ring=np.flatnonzero(cp==102)[:10];anchors=[]
for angle in [0,30,-30]:
 reset(a);b=a.pose.bones['spine_05'];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((0,0,1),math.radians(angle));bpy.context.view_layer.update();p=deformed(o);anchor=(p[tri]*bary[:,None]).sum(axis=0);center=p[ring].mean(axis=0);distance=float(np.linalg.norm(anchor-center));assert distance<.15
 anchors.append({'spine_05_local_z_degrees':angle,'tab_center_to_supporting_surface_cm':distance})
reset(a)
report={'manual_diagnostic_only':True,'game_animations_executed':False,'hand_curl_35_degrees':{'v10':before,'v11':after},'attachment':anchors,'weight_interpolation_from_actual_strap_triangle':True}
(ROOT/'detail-review.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
