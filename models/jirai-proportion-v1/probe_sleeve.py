import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
def mat(name,color):
 x=bpy.data.materials.new(name);x.use_nodes=True;x.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(*color,1);return x
skin=mat('diagnostic_skin_blue',(.05,.25,.8));sleeve=mat('diagnostic_sleeve_white',(.8,.8,.8))
for i,x in enumerate(m.materials):
 if 'Skin' in x.name:m.materials[i]=skin
 elif 'Blouse' in x.name:m.materials[i]=sleeve
for s,sign in [('l',-1),('r',1)]:
 b=a.data.bones['upperarm_'+s].matrix_local.to_quaternion();a.pose.bones['upperarm_'+s].rotation_mode='QUATERNION';a.pose.bones['upperarm_'+s].rotation_quaternion=b.inverted()@Quaternion((0,1,0),math.radians(65*sign))@b
scene=bpy.context.scene;scene.cycles.samples=6;scene.render.resolution_x=750;scene.render.resolution_y=600
cam=scene.camera;cam.location=(-200,500,170);cam.rotation_euler=(Vector((0,4,155))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=80;scene.render.filepath=str(R/'review/shoulder-clay.png');bpy.ops.render.render(write_still=True)
