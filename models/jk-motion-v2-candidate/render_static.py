import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.resolution_x=850;scene.render.resolution_y=950;scene.render.resolution_percentage=100
light=bpy.data.objects.get('Softbox')
if not scene.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
for name,pos,target,scale in [('v2-stockings',(0,-600,87),(0,0,87),48),('v2-stockings-back',(0,600,88),(0,4,88),48),('v2-palm',(80,220,103),(55,-8,103),22),('v2-hand',(130,-250,102),(52,-12,104),24),('v2-halo',(0,-600,198),(-8,8,198),70),('v2-side',(-600,0,162),(-10,0,162),110),('v2-charm',(-80,-250,140),(-12,-5,137),30)]:
 camera=scene.camera;camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
 scene.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)
print('STATIC_REVIEW_RENDERED',flush=True)
