"""Save a reviewable editable mother file with physics guides hidden separately."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-v1';OUT=ROOT/'review-r3-shoulder';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(body.data);layer=bm.verts.layers.int['source_component'];bm.select_mode={'VERT'}
for v in bm.verts:v.select_set(v[layer]>=2000)
bm.select_flush(True);bmesh.update_edit_mesh(body.data);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
assert len(body.data.vertices)>20000 and all(d.value<2000 for d in body.data.attributes['source_component'].data)
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob!=body:
  assert all(d.value>=2000 for d in ob.data.attributes['source_component'].data)
  ob.name='Hidden_Physics_Guides';ob.hide_render=True;ob.hide_set(True)
arm.data.name='Hun_Jirai_ShoulderCorrected_264';body.modifiers[0].name='Jirai Anatomical Shoulder Rig'
arm['shoulder_correction']='Actual humerus heads moved to anatomical shoulders; elbow/wrist rest positions retained'
arm['ue_retarget_contract']='Per-character native skeleton; no shared skeleton override'
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.context.scene.render.filepath=str(OUT/'preview.png')
scene=bpy.context.scene;cam=scene.camera;cam.location=(0,-650,115);cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=247
scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.cycles.samples=12;scene.view_settings.exposure=.4
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Sui_Jirai_Shoulder_R3.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('Review mother file saved')
