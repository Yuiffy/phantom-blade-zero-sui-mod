"""Render the actual 60th solver tick, before any component motion begins."""
import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
old=next(o for o in bpy.context.scene.objects if o.type=='MESH');old.hide_render=True
d=np.load(W/'preview-idle.npz');vertices=d['positions'].copy();vertices[:,1]*=-1
m=bpy.data.meshes.new('Actual_Offline_Settled_Output');m.from_pydata(vertices,[],d['indices'].tolist());m.update()
for mat in old.data.materials:m.materials.append(mat)
for p,i in zip(m.polygons,d['materials']):p.material_index=int(i);p.use_smooth=True
uv=m.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',d['uv'][np.array([l.vertex_index for l in m.loops])].ravel())
obj=bpy.data.objects.new('Cooked_Settled_Preview',m);bpy.context.collection.objects.link(obj)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8;scene.render.resolution_x=850;scene.render.resolution_y=1100
light=bpy.data.objects.get('Softbox')
if not scene.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
for name,pos,target,scale in [('idle-side',(-600,0,170),(-10,0,170),100),('idle-front',(0,-600,115),(0,0,115),245)]:
 scene.camera.location=pos;scene.camera.rotation_euler=(Vector(target)-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=scale
 scene.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
