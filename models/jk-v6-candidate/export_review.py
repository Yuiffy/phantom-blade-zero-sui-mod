"""Deliver editable, rest-pose review assets without changing the cooked FBX."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
fbx=ROOT/'Sui_JK_Hun_Body.fbx';fbx_before=sha(fbx)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-refined-source.blend'))
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.type in {'MESH','ARMATURE'}:o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(ROOT/'sui-jk-refined-preview.glb'),export_format='GLB',use_selection=True,export_animations=False,export_cameras=False,export_lights=False)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
contract=json.loads((ROOT/'source-render-contract.json').read_text())
assert len(mesh.data.vertices)==len(contract['positions_blender_cm'])
assert all((v.co-Vector(p)).length<1e-6 for v,p in zip(mesh.data.vertices,contract['positions_blender_cm']))
assert all((p.matrix_basis.to_translation()).length<1e-6 and abs(p.matrix_basis.to_quaternion().angle)<1e-6 for p in arm.pose.bones)
scene=bpy.context.scene;cam=scene.camera
if not scene.get('review_lighting_in_cm'):
    light=bpy.data.objects.get('Softbox')
    light.location*=200;light.data.energy*=40000;light.data.size*=200
    scene['review_lighting_in_cm']=True
cam.location=(0,-600,110);cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=235
bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
assert sha(fbx)==fbx_before
print(json.dumps({'source_glb_sha256':sha(ROOT/'sui-jk-refined-preview.glb'),'bound_blend_sha256':sha(ROOT/'sui-jk-hun-bound.blend'),'fbx_unchanged':True}))
