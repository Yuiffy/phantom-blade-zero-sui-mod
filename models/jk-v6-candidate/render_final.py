import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
scene=bpy.context.scene;cam=scene.camera
assert scene.get('review_lighting_in_cm')
scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.resolution_x=800;scene.render.resolution_y=1000
for name,pos in [('bound-front',(0,-600,110)),('bound-side',(-600,-80,110)),('bound-back',(0,600,110))]:
    cam.location=pos;cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=235
    scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
