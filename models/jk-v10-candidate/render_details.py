import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=12;sc.render.threads_mode='FIXED';sc.render.threads=2
sc.render.resolution_x=1000;sc.render.resolution_y=850;sc.render.resolution_percentage=100
cam=sc.camera
for name,pos,target,scale in [('rear-hem',(0,600,105),(0,8,111),67),('front-thigh',(0,-600,93),(6,2,95),57),('hand-l',(100,-250,106),(51,-11,104),27),('backpack',(0,600,135),(-8,17,128),70)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 sc.render.filepath=str(ROOT/('v10-'+name+'.png'));bpy.ops.render.render(write_still=True)
