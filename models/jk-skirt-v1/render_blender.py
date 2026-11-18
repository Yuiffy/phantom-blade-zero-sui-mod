"""Private offline review of the GPU-reconstructed JK skirt; no game control."""
import bpy,numpy as np,json,sys,os,hashlib
from pathlib import Path
from mathutils import Vector
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-v1';R=W.parents[1];out=W/'preview';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.render.resolution_x=900;s.render.resolution_y=950;s.render.resolution_percentage=100
s.world.color=(.18,.18,.18);s.view_settings.view_transform='AgX'
for pos,power,size in [((55,-75,155),130000,100),((-70,-40,115),85000,100),((20,90,150),100000,80)]:
 data=bpy.data.lights.new('Studio','AREA');data.energy=power;data.shape='DISK';data.size=size;obj=bpy.data.objects.new('Studio',data);s.collection.objects.link(obj);obj.location=pos;obj.rotation_euler=(Vector((0,0,100))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));s.collection.objects.link(camera);s.camera=camera;camera.data.type='ORTHO';camera.data.lens=70
rows=json.loads((R/'private/outfit-patterns-v1/preview-materials.json').read_text())['jk'];materials=[]
for row in rows:
 m=bpy.data.materials.new(row['slot']);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.68
 path=Path(row['path'])
 if path.name=='jk-before.png':path=R/'private/outfit-patterns-v1/jk-after.png'
 im=bpy.data.images.load(str(path),check_existing=True);tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);materials.append(m)
native=np.load(R/'private/jk-face-shape-v1/final.npz');uv=native['uv'][:,0].copy();uv[:,1]=1-uv[:,1]
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'jog'
hashfile=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
review=[]
hz=int(os.environ.get('JK_PREVIEW_HZ','30'))
base_contacts=json.loads((W/'baseline/contacts.json').read_text())['records'];base_row=next(x for x in base_contacts if x['file']==f'jog-{hz}-surface.npz')
compare_peak=max(base_row['samples'],key=lambda x:x.get('thigh_visible_edges_crossing',x['thigh_edges_crossing'])+x.get('shorts_visible_edges_crossing',0))['frame']
for stage in os.environ.get('JK_STAGES','baseline,'+os.environ.get('JK_CANDIDATE','candidate2')).split(','):
 contacts=json.loads((W/stage/'contacts.json').read_text())['records'];row=next(x for x in contacts if x['file']==f'jog-{hz}-surface.npz');peak=max(row['samples'],key=lambda x:x.get('thigh_visible_edges_crossing',x['thigh_edges_crossing'])+x.get('shorts_visible_edges_crossing',0))['frame']
 for profile,frame,label in [('jog',compare_peak,'jog-compare')] if mode=='jog' else [('jog',6,'idle'),('jog',compare_peak,'jog-compare'),('jog',peak,'jog-own-peak'),('jog',None,'recovered'),('crouch',None,'crouch')]:
  data=np.load(W/stage/f'{profile}-{hz}-surface.npz')
  if frame is None:frame=int(np.argmin(abs(data['times']-(2. if profile=='crouch' else 15.5))))
  p=data['frames'][frame].copy();p[:,1]*=-1;faces=data['faces'];mesh=bpy.data.meshes.new('ReconstructedJK');mesh.from_pydata(p.tolist(),[],faces.tolist());mesh.update()
  for m in materials:mesh.materials.append(m)
  tex=uv[data['ids']];layer=mesh.uv_layers.new(name='UVMap')
  for f,mat in zip(mesh.polygons,data['materials']):f.material_index=int(mat);f.use_smooth=True
  for loop in mesh.loops:layer.data[loop.index].uv=tex[loop.vertex_index]
  obj=bpy.data.objects.new('ReconstructedJK',mesh);s.collection.objects.link(obj)
  for view,pos,scale in [('front',(0,-150,106),70),('quarter',(90,-145,113),75)]:
   camera.location=pos;camera.rotation_euler=(Vector((0,0,96))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale;s.render.filepath=str(out/f'{stage}-{label}-{view}.png');bpy.ops.render.render(write_still=True)
   surface=W/stage/f'{profile}-{hz}-surface.npz';review.append(dict(image=s.render.filepath,image_sha256=hashfile(s.render.filepath),source_surface=str(surface),source_sha256=hashfile(surface),profile=profile,hz=hz,frame=int(frame),time=float(data['times'][frame]),view=view))
  bpy.data.objects.remove(obj,do_unlink=True)
(out/f'review-{os.environ.get("JK_CANDIDATE","candidate2")}-{hz}-{mode}.json').write_text(json.dumps(dict(images=review,script_sha256=hashfile(__file__),offline_only=True,game_shader_reproduced=False),indent=2))
print('JK_SKIRT_PREVIEW_READY')
