"""Keep optional authored wings separate from the body and hide physics guides."""
import bpy,bmesh
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]/'private/jirai-v1';OUT=R/'review-r4-wings';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
def separate(name,predicate):
 before=set(bpy.context.scene.objects)
 bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(body.data);layer=bm.verts.layers.int['source_component'];bm.select_mode={'VERT'}
 for v in bm.verts:v.select_set(predicate(v[layer]))
 bm.select_flush(True);bmesh.update_edit_mesh(body.data);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
 objects=set(bpy.context.scene.objects)-before;assert len(objects)==1
 o=objects.pop();o.name=name;return o
guides=separate('Hidden_Physics_Guides',lambda c:c>=2000);guides.hide_render=True;guides.hide_set(True)
wings=separate('Optional_Cotton_Wings',lambda c:c in [910,911])
assert all(a.value not in [910,911] and a.value<2000 for a in body.data.attributes['source_component'].data)
wings['provenance']='Assistant-added ornament, absent from the supplied four views. User accepted retaining it for a game trial on 2026-11-16.'
wings['removal']='Delete this independent object and the two Wing cloth specs, then rebuild; do not change body weights or shoulder rig.'
scene=bpy.context.scene;cam=scene.camera;cam.location=(0,-650,115);cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=247
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.shading.type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Sui_Jirai_R4_OptionalWings.blend'),compress=True)
print('R4_EDITABLE_REVIEW_SAVED',flush=True)
