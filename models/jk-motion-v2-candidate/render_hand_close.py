import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
import bmesh
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int.get('source_component');remove=[v for v in bm.verts if v[layer]!=5];bmesh.ops.delete(bm,geom=remove,context='VERTS');bm.to_mesh(m);bm.free();m.update()
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.resolution_x=800;scene.render.resolution_y=850
light=bpy.data.objects.get('Softbox')
if not scene.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
for name,sign in [('v2-palm-close',1),('v2-hand-back-close',-1)]:
 center=Vector((56.9,-11.4,104));scene.camera.location=center+Vector((-.8276,.2271,-.5133))*300*sign;scene.camera.rotation_euler=(center-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=23
 light.location=scene.camera.location;light.data.energy=500000;light.data.size=130
 scene.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)
