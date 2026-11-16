import bpy,bmesh,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';O=R/'models/jirai-detail-v1';bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'))
source=next(x for x in bpy.context.scene.objects if x.type=='MESH');source.name='Sui_Jirai_R6_Detail';arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');arm.name='Hun_Jirai_264'
bpy.ops.object.select_all(action='DESELECT');source.select_set(True);bpy.context.view_layer.objects.active=source;bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(source.data);layer=bm.verts.layers.int['source_component'];bm.select_mode={'VERT'}
for v in bm.verts:v.select_set(v[layer]>=2000)
bm.select_flush(True);bmesh.update_edit_mesh(source.data);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
for ob in bpy.context.scene.objects:
 if ob.type=='MESH' and ob!=source:ob.name='Hidden_R5_Physics_Guides';ob.hide_render=True;ob.hide_set(True)
source['revision']='R6 detail: fitted black suspender and rectangular metal buckle; old baked projection and relief removed; rear thigh and choker atlas repaired; native IK markers restored; R5 hair/skirt unchanged'
source['game_runtime_tested']=False
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
bpy.ops.object.select_all(action='DESELECT');source.select_set(True);bpy.context.view_layer.objects.active=source
p=O/'Sui_Jirai_R6_Detail_Editable.blend';bpy.ops.wm.save_as_mainfile(filepath=str(p),compress=True)
(O/'source-manifest.json').write_text(json.dumps({'file':p.name,'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'source_fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'original_visible_game_mesh_or_animation_included':False,'license':'excluded from code MIT; see NOTICE.md'},indent=2));print('EDITABLE_SOURCE_SAVED')
