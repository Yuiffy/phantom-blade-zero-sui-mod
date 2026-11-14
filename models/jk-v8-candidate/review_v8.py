import bpy,json,math,numpy as np,sys,os
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'shots';OUT.mkdir(exist_ok=True)
SOURCES={'v7':Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod/models/jk-v7-candidate/sui-jk-hun-bound-v7.blend'),'v8':ROOT/'sui-jk-hun-bound.blend'}
reports={}
def load(tag):
 bpy.ops.wm.open_mainfile(filepath=str(SOURCES[tag]))
 sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.threads_mode='FIXED';sc.render.threads=2;sc.cycles.device='CPU';sc.cycles.samples=8
 ob=next(o for o in sc.objects if o.type=='MESH');arm=next(o for o in sc.objects if o.type=='ARMATURE')
 return sc,ob,arm
def reset(arm):
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update()
def rotate(arm,name,axis,angle):
 p=arm.pose.bones[name];b=p.bone.matrix_local.to_quaternion();p.rotation_mode='QUATERNION';p.rotation_quaternion=b.inverted()@Quaternion(Vector(axis),math.radians(angle))@b
 bpy.context.view_layer.update()
def aim(arm,side,target,pole):
 u=arm.pose.bones['upperarm_'+side];l=arm.pose.bones['lowerarm_'+side];h=arm.pose.bones['hand_'+side]
 s=u.head.copy();e=l.head.copy();w=h.head.copy();a=(e-s).length;b=(w-e).length
 v=Vector(target)-s;d=min(v.length,a+b-.1);axis=v.normalized();along=(a*a-b*b+d*d)/(2*d)
 perp=Vector(pole)-s;perp-=axis*perp.dot(axis);perp.normalize()
 elbow=s+axis*along+perp*math.sqrt(max(0,a*a-along*along));wrist=s+axis*d
 q=(e-s).rotation_difference(elbow-s);u.matrix=Matrix.Translation(s)@q.to_matrix().to_4x4()@Matrix.Translation(-s)@u.matrix
 bpy.context.view_layer.update();e=l.head.copy();w=h.head.copy();q=(w-e).rotation_difference(wrist-e)
 l.matrix=Matrix.Translation(e)@q.to_matrix().to_4x4()@Matrix.Translation(-e)@l.matrix;bpy.context.view_layer.update()
def render(sc,tag,label,pos,target,scale,size=(720,900)):
 if os.environ.get('PBZ_REVIEW_NO_RENDER'):return
 if os.environ.get('PBZ_REVIEW_SKIP_V7') and tag=='v7':return
 if os.environ.get('PBZ_RENDER_LABELS') and label not in os.environ['PBZ_RENDER_LABELS'].split(','):return
 cam=sc.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 sc.render.resolution_x,sc.render.resolution_y=size;sc.render.resolution_percentage=100
 sc.render.filepath=str(OUT/f'{tag}-{label}.png');bpy.ops.render.render(write_still=True)
def evaluated(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh();co=np.array([v.co[:] for v in data.vertices]);ev.to_mesh_clear();assert np.isfinite(co).all();return co

_,ob,_=load('v8');src=np.array([d.vector[:] for d in ob.data.attributes['source_rest_position'].data])
comp=np.array([d.value for d in ob.data.attributes['source_component'].data]);x=np.abs(src[:,0]-.00195217);z=src[:,2]
regions={'neck_collar_transition':(comp==0)&(x<.025)&(z>.76)&(z<.785),'visible_neck':(comp==0)&(x<.018)&(z>.77)&(z<.785),'shoulder':(comp==0)&(x>.025)&(x<.145)&(z>.66)&(z<.77)}
for tag in ['v7','v8']:
 sc,ob,arm=load(tag);reset(arm)
 rest=np.array([v.co[:] for v in ob.data.vertices]);edges=np.array([e.vertices[:] for e in ob.data.edges]);lens=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
 rows=[]
 render(sc,tag,'front',(0,-600,110),(0,0,110),235)
 render(sc,tag,'upper',(0,-600,160),(0,0,160),92,(760,760))
 for pose in ['head-turn','head-nod','arms-up','weapon-guard']:
  reset(arm)
  if pose=='head-turn':rotate(arm,'head',(0,0,1),85)
  elif pose=='head-nod':rotate(arm,'head',(1,0,0),43)
  elif pose=='arms-up':rotate(arm,'upperarm_r',(0,1,0),65);rotate(arm,'upperarm_l',(0,1,0),-55);rotate(arm,'lowerarm_r',(1,0,0),-65)
  else:aim(arm,'r',(-8,-35,139),(-65,-12,139));aim(arm,'l',(10,-29,143),(65,-8,139))
  co=evaluated(ob);ratio=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)/np.maximum(lens,1e-10)
  row={'pose':pose,'finite_vertices':True}
  for name,mask in regions.items():
   selected=mask[edges[:,0]]&mask[edges[:,1]]&(lens>.05)
   r=ratio[selected];row[name]={'edges':len(r),'p99':float(np.percentile(r,99)),'max':float(r.max()),'over_1_6':int((r>1.6).sum())}
  rows.append(row)
  if tag=='v8' and pose!='head-nod':render(sc,tag,pose,(0,-600,155),(0,0,155),115,(760,760))
 reports[tag]=rows
 reset(arm)
 if tag=='v8':render(sc,tag,'back-upper',(0,600,156),(0,0,156),100,(760,760))
(ROOT/'pose-review.json').write_text(json.dumps({'game_animations_executed':False,'poses_are_manual_diagnostics':True,'edge_regions_use_source_provenance':True,'versions':reports},indent=2))
print(json.dumps(reports))
