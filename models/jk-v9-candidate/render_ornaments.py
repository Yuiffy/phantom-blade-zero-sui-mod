import bpy,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
for tag,path in [('v8',ROOT.parent/'tripo-refine-v8/sui-jk-hun-bound.blend'),('v9',ROOT/'sui-jk-hun-bound.blend')]:
 if os.environ.get('PBZ_ONLY_V9') and tag!='v9':continue
 bpy.ops.wm.open_mainfile(filepath=str(path));s=bpy.context.scene
 s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=12;s.render.threads_mode='FIXED';s.render.threads=2
 s.render.resolution_x=850;s.render.resolution_y=950;s.render.resolution_percentage=100
 for name,target,scale in [('charm',(-12.5,-7,136),23),('wing',(10.7,-3.4,80),15)]:
  s.camera.location=(target[0],-600,target[2]);s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=scale
  s.render.filepath=str(ROOT/(tag+'-'+name+'-detail.png'));bpy.ops.render.render(write_still=True)
