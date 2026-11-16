"""Render the final cooked cloth surface and save a separate editable source."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';W=R/'variant';OUT=R/'review-final';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
source=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
source.name='Sui_Jirai_R5_Editable_Source';arm.name='Hun_Jirai_R5_264'
# The editable master retains all cloth authoring geometry in a hidden object.
bpy.ops.object.select_all(action='DESELECT');source.select_set(True);bpy.context.view_layer.objects.active=source
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='DESELECT');bm=bmesh.from_edit_mesh(source.data);layer=bm.verts.layers.int['source_component'];bm.select_mode={'VERT'}
for v in bm.verts:v.select_set(v[layer]>=2000)
bm.select_flush(True);bmesh.update_edit_mesh(source.data);bpy.ops.mesh.separate(type='SELECTED');bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.context.scene.objects:
 if o.type=='MESH' and o!=source:o.name='Hidden_Three_Physics_Guides';o.hide_render=True;o.hide_set(True)
source['revision']='R5: no cotton wings; shortened arms/neck; repaired native finger weights, wrist seams, hips, sleeve holes and hidden skin'
source['game_runtime_tested']=False
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=10;scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.view_settings.exposure=.4
scene.render.resolution_x=720;scene.render.resolution_y=1000
cam.location=(0,-650,115);cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=247
bpy.ops.object.select_all(action='DESELECT');source.select_set(True);bpy.context.view_layer.objects.active=source
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'Sui_Jirai_R5_Editable.blend'),compress=True)
source.hide_render=True;d=np.load(W/'preview-idle.npz');positions=d['positions'].copy();positions[:,1]*=-1
mesh=bpy.data.meshes.new('Cooked_Surface');mesh.from_pydata(positions,[],d['indices'].tolist());mesh.update()
detail=json.loads((W/'independent/cloth-native-details.json').read_text());mapping={s['material']:s['slot'] for s in detail['sections']}
for i in range(max(mapping)+1):
 name=mapping[i];material=bpy.data.materials.get(name)
 assert material,name
 mesh.materials.append(material)
for face,i in zip(mesh.polygons,d['materials']):face.material_index=int(i);face.use_smooth=True
uv=mesh.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',d['uv'][np.array([l.vertex_index for l in mesh.loops])].ravel())
obj=bpy.data.objects.new('Final_Cooked_Cloth_Sampled_Surface',mesh);bpy.context.collection.objects.link(obj)
for name,pos in [('front',(0,-650,115)),('back',(0,650,115))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
(OUT/'preview-basis.json').write_text(json.dumps({'basis':'final cooked geometry/UV and actual offline Chaos settled sample; source Blender materials preview the verified albedo inputs','game_runtime_tested':False,'source_fbx_sha256':json.loads((R/'binding-report.json').read_text())['fbx_sha256'],'wing_render_sections':0,'cloth_assets':3},indent=2))
print('R5_COOKED_REVIEW_SAVED')
