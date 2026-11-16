"""Render the current mother mesh with simulation guides excluded from preview."""
import bpy,bmesh,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=16;scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.view_settings.exposure=.4
def reset():
 for p in arm.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0);p.scale=(1,1,1)
 bpy.context.view_layer.update()
def rotate(n,axis,angle):
 p=arm.pose.bones[n];b=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=b.inverted()@Quaternion(Vector(axis),math.radians(angle))@b
def render(name,pos,target=(0,0,110),scale=247):
 bpy.context.view_layer.update();cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
reset();render('review-r2-front',(0,-650,115));render('review-r2-back',(0,650,115))
if not os.environ.get('PBZ_REVIEW_QUICK'):render('review-r2-three-quarter',(-320,-650,130))
render('review-r2-shoulders',(-130,-650,160),(0,0,151),87)
rotate('upperarm_r',(0,1,0),65);rotate('upperarm_l',(0,1,0),-55);rotate('lowerarm_r',(1,0,0),-65);render('review-r2-arms',(0,-650,115));reset()
if os.environ.get('PBZ_REVIEW_QUICK'):print('JIRAI_R2_REVIEW_OK',flush=True);raise SystemExit(0)
rotate('thigh_l',(1,0,0),-55);rotate('calf_l',(1,0,0),80);rotate('thigh_r',(1,0,0),-35);rotate('calf_r',(1,0,0),65);rotate('head',(0,0,1),45);render('review-r2-crouch',(-350,-650,115));reset()
for side in ['l','r']:
 for finger in ['index','middle','ring','pinky']:
  for i in [1,2,3]:arm.pose.bones[f'{finger}_{i:02d}_{side}'].rotation_quaternion=Quaternion((0,0,1),math.radians(-45 if side=='r' else 45))
render('review-r2-grip',(0,-650,115));reset()
print('JIRAI_R2_REVIEW_OK',flush=True)
