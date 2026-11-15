"""Normal front/back/side garment review; background CPU only."""
from pathlib import Path
import bpy
from mathutils import Vector
R=Path(__file__).resolve().parent
for version in ['v2','v3']:
    source=R.with_name('tripo-motion-'+version)/'sui-jk-motion-source.blend'
    bpy.ops.wm.open_mainfile(filepath=str(source))
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8
    s.render.threads_mode='FIXED';s.render.threads=2
    s.render.resolution_x=700;s.render.resolution_y=760;s.render.resolution_percentage=100
    light=bpy.data.objects.get('Softbox')
    if not s.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
    for name,pos,target,scale in [('front',(0,-600,94),(0,2,99),52),('back',(0,600,94),(0,3,99),52),('side',(600,0,94),(0,3,99),52)]:
        cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        s.render.filepath=str(R/(version+'-shorts-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('SHORTS_REVIEW_RENDERED',flush=True)
