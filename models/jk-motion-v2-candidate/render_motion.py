"""Background preview of actual diagnostic solver positions, not game animation."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
old=next(o for o in bpy.context.scene.objects if o.type=='MESH');old.hide_render=True
d=np.load(W/'preview-deformation.npz');vertices=d['positions'].copy();vertices[:,1]*=-1
m=bpy.data.meshes.new('Actual_Offline_Chaos_Output');m.from_pydata(vertices,[],d['indices'].tolist());m.update()
for mat in old.data.materials:m.materials.append(mat)
for p,i in zip(m.polygons,d['materials']):p.material_index=int(i);p.use_smooth=True
uv=m.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',d['uv'][np.array([l.vertex_index for l in m.loops])].ravel())
obj=bpy.data.objects.new('Cooked_Cloth_Preview',m);bpy.context.collection.objects.link(obj)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8
scene.render.resolution_x=800;scene.render.resolution_y=1000
light=bpy.data.objects.get('Softbox')
if not scene.get('review_lighting_in_cm'):light.location*=200;light.data.energy*=40000;light.data.size*=200
camera=scene.camera
for name,pos,target,scale in [('motion-front',(0,-600,115),(0,0,115),245),('motion-side',(-600,0,115),(0,0,115),245),('motion-charm',(-80,-250,142),(-12,-5,137),30)]:
 camera.location=pos;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
 scene.render.filepath=str(W/(name+'.png'));bpy.ops.render.render(write_still=True)
print('OFFLINE_SOLVER_PREVIEWS_OK')
