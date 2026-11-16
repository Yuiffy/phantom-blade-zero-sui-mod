"""Preview the actual cooked GPU cloth mapping applied to real Chaos samples."""
import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-v1';W=ROOT/'variant';OUT=ROOT/'review-r4-wings';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'))
old=next(o for o in bpy.context.scene.objects if o.type=='MESH');old.hide_render=True;old.hide_viewport=True
d=np.load(W/'preview-motion-sequence.npz');frames=d['frames'].copy();frames[:,:,1]*=-1
m=bpy.data.meshes.new('Cooked_visible_surface');m.from_pydata(frames[0],[],d['indices'].tolist());m.update()
for mat in old.data.materials:m.materials.append(mat)
for p,i in zip(m.polygons,d['materials']):p.material_index=int(i);p.use_smooth=True
uv=m.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',d['uv'][np.array([l.vertex_index for l in m.loops])].ravel())
obj=bpy.data.objects.new('Actual_Chaos_surface',m);bpy.context.collection.objects.link(obj)
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=4;scene.view_settings.exposure=.4
scene.render.resolution_x=480;scene.render.resolution_y=360
cam=scene.camera;cam.location=(155,600,155);cam.rotation_euler=(Vector((0,20,146))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=104
out=OUT/'motion-frames';out.mkdir(exist_ok=True)
for i,points in enumerate(frames):
 m.vertices.foreach_set('co',points.ravel());m.update();scene.render.filepath=str(out/(str(i).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
# A full-body review uses the sampled settled surface; no synthetic wing keys.
m.vertices.foreach_set('co',frames[0].ravel());m.update();scene.render.resolution_x=720;scene.render.resolution_y=1000;scene.cycles.samples=10
for name,pos in [('back',(0,650,115)),('front',(0,-650,115))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=247
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
# Keep source and physically sampled surface as distinct editable objects.
old.hide_viewport=False;old.hide_render=False;obj.hide_viewport=True;obj.hide_render=True
old['review_note']='Five physics guide sections are hidden from render by material in UE. Use the R4 review script to split guides before normal modeling.'
scene['motion_source']='Actual offline Chaos, fore/aft and pitch/roll stress profile; reconstructed with final cooked GPU maps. Not a game animation.'
(OUT/'motion-source.json').write_text(json.dumps({'test':json.loads((W/'render-deformation-review.json').read_text())['test'],'sample_steps':d['steps'].tolist(),'dt':float(d['dt']),'fps':1/(10*float(d['dt'])),'game_runtime_tested':False},indent=2))
print('ACTUAL_WING_MOTION_RENDERED',len(frames),flush=True)
