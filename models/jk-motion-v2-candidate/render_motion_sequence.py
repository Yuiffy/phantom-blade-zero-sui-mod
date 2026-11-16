"""Render sampled actual cloth output; no game or desktop capture."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
old=next(o for o in bpy.context.scene.objects if o.type=='MESH');old.hide_render=True
d=np.load(W/'preview-motion-sequence.npz');frames=d['frames'].copy();frames[:,:,1]*=-1
m=bpy.data.meshes.new('Actual_Offline_Chaos_Sequence');m.from_pydata(frames[0],[],d['indices'].tolist());m.update()
for mat in old.data.materials:m.materials.append(mat)
for p,i in zip(m.polygons,d['materials']):p.material_index=int(i);p.use_smooth=True
uv=m.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',d['uv'][np.array([l.vertex_index for l in m.loops])].ravel())
obj=bpy.data.objects.new('Actual_Offline_Chaos',m);bpy.context.collection.objects.link(obj)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=4
scene.render.resolution_x=400;scene.render.resolution_y=500
light=bpy.data.objects.get('Softbox')
if not scene.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
camera=scene.camera;camera.location=(0,-600,165);camera.rotation_euler=(Vector((0,0,165))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=90
out=W/'motion-sequence';out.mkdir(exist_ok=True)
for i,points in enumerate(frames):
 m.vertices.foreach_set('co',points.ravel());m.update();scene.render.filepath=str(out/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
print('ACTUAL_CHAOS_SEQUENCE_RENDERED',len(frames),flush=True)
