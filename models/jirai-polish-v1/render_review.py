"""Hidden offline native geometry review, including unlit albedo isolation."""
from pathlib import Path
import bpy,numpy as np,os,json,hashlib
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-polish-v1';F=R/'private/jirai-face-v3'
before=os.environ.get('PBZ_POLISH_BEFORE')=='1';tag='before' if before else 'after'
path=R/'private/jirai-hairpin-v1/final-render.npz' if before else W/('final-render.npz' if (W/'final-render.npz').exists() else 'patched-render.npz')
native_path=path;d=np.load(path);bpy.ops.wm.open_mainfile(filepath=str(F/'face-preview.blend'))
old=next(x for x in bpy.context.scene.objects if x.type=='MESH');materials=list(old.data.materials)
unlit=os.environ.get('PBZ_POLISH_UNLIT')=='1'
for m in materials:
 if not m.use_nodes:continue
 bs=m.node_tree.nodes.get('Principled BSDF')
 if not bs:continue
 if m.name=='MI_Jirai_Skin':path=F/'T_Jirai_Base.png' if before else W/'T_Jirai_Base.png'
 elif m.name=='MI_Jirai_Hair':path=R/'private/jirai-hairpin-v1/T_Jirai_Base.png'
 elif m.name=='MI_Jirai_EyeIris':path=F/'T_Face3_Iris.png'
 else:path=R/'private/outfit-patterns-v1/jirai-after.png'
 for link in bs.inputs['Base Color'].links:
  if link.from_node.type=='TEX_IMAGE':link.from_node.image=bpy.data.images.load(str(path),check_existing=True)
 if unlit:
  node=m.node_tree.nodes.new('ShaderNodeEmission')
  if bs.inputs['Base Color'].is_linked:m.node_tree.links.new(bs.inputs['Base Color'].links[0].from_socket,node.inputs['Color'])
  else:node.inputs['Color'].default_value=bs.inputs['Base Color'].default_value
  m.node_tree.links.new(node.outputs[0],m.node_tree.nodes.get('Material Output').inputs['Surface'])
p=d['positions'].copy();p[:,1]*=-1;n=d['normals'].copy();n[:,1]*=-1
t=d['indices'].reshape(-1,3);mat=d['materials'];t=t[~np.isin(mat[t[:,0]],[12,13,14])]
t=t[np.linalg.norm(np.cross(p[t[:,1]]-p[t[:,0]],p[t[:,2]]-p[t[:,0]]),axis=1)>1e-8]
mesh=bpy.data.meshes.new('PolishNative');mesh.from_pydata(p.tolist(),[],t.tolist());mesh.update()
for m in materials:mesh.materials.append(m)
uv=mesh.uv_layers.new(name='UVMap');tex=d['uv'][:,0].astype(float);tex[:,1]=1-tex[:,1]
for face in mesh.polygons:face.material_index=int(mat[face.vertices[0]]);face.use_smooth=True
for loop in mesh.loops:uv.data[loop.index].uv=tex[loop.vertex_index]
mesh.normals_split_custom_set([n[l.vertex_index] for l in mesh.loops])
obj=bpy.data.objects.new('PolishNative',mesh);bpy.context.collection.objects.link(obj);bpy.data.objects.remove(old,do_unlink=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('PBZ_POLISH_SAMPLES','8'));s.render.resolution_percentage=100
s.render.resolution_x=800;s.render.resolution_y=850;s.view_settings.exposure=.4
if unlit:s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
views={'front':((-.35,-120,179),(-.35,0,179),25),'angle':((38,-100,182),(-.35,0,178),25),'side':((75,-90,180),(-.35,0,177),26),'shoulder':((70,-100,161),(21,-6,150),26),'shoulder-back':((65,85,162),(21,-6,150),26),'halo':((0,-140,210),(-4,0,207),48),'upper':((35,-200,179),(0,0,177),90)}
dest=W/os.environ.get('PBZ_POLISH_DIR','preview');dest.mkdir(exist_ok=True)
for name in os.environ.get('PBZ_POLISH_VIEWS','front,angle,shoulder,halo').split(','):
 pos,target,scale=views[name];cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
 s.render.filepath=str(dest/f'{tag}-{name}{"-unlit" if unlit else ""}.png');bpy.ops.render.render(write_still=True)
 def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
 manifest=dest/'render-manifest.json';records=json.loads(manifest.read_text(encoding='utf8')) if manifest.exists() else {}
 records[Path(s.render.filepath).name]=dict(native_sha256=sha(native_path),skin_source_sha256=sha(F/'T_Jirai_Base.png' if before else W/'T_Jirai_Base.png'),image_sha256=sha(s.render.filepath),source_png_not_cooked_vt=True,gameplay=False)
 manifest.write_text(json.dumps(records,indent=2)+'\n',encoding='utf8')
print('POLISH_PREVIEW_RENDERED',tag)
