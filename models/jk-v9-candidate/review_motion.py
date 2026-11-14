import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=8;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.resolution_x=850;sc.render.resolution_y=850
cam=sc.camera
for n,ang in [('thigh_l',-22),('thigh_r',22)]:
 pb=arm.pose.bones[n];q=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q.inverted()@Quaternion((0,1,0),math.radians(ang))@q
bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();co=np.array([v.co[:] for v in mesh.vertices]);np.save(ROOT/'v9-splay-evaluated.npy',co);ev.to_mesh_clear()
cam.location=(0,-600,96);cam.rotation_euler=(Vector((0,0,96))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=80
sc.render.filepath=str(ROOT/'v9-legs-splayed.png');bpy.ops.render.render(write_still=True)
# Independent hand-only diagnostic: curl local hinge channels as a native pose.
for pb in arm.pose.bones:pb.rotation_quaternion=Quaternion()
for side in ['l','r']:
 for finger in ['index','middle','ring','pinky']:
  for i in [1,2,3]:
   pb=arm.pose.bones[f'{finger}_{i:02d}_{side}'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((0,0,1),math.radians(-35 if side=='r' else 35))
bpy.context.view_layer.update();cam.location=(100,-250,106);cam.rotation_euler=(Vector((54,-11,104))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=29
sc.render.filepath=str(ROOT/'v9-hand-curl.png');bpy.ops.render.render(write_still=True)
