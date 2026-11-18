"""Review frozen installed native surfaces with corresponding source PNGs."""
from pathlib import Path
import bpy,numpy as np,os,json
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/outfit-patterns-v1'
outfit=os.environ.get('PBZ_PATTERN_OUTFIT','jirai');after=os.environ.get('PBZ_PATTERN_AFTER')=='1';tag='after' if after else 'before'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-face-v3/face-preview.blend'))
template=next(x for x in bpy.context.scene.objects if x.type=='MESH');existing=list(template.data.materials)
for old in [x for x in bpy.context.scene.objects if x.type=='MESH']:bpy.data.objects.remove(old,do_unlink=True)
d=np.load(W/f'{outfit}-native.npz');p=d['positions'].copy();p[:,1]*=-1;norm=d['normals'].copy();norm[:,1]*=-1
tri=d['indices'].reshape(-1,3);mat=d['materials'];hide=[12,13,14] if outfit=='jirai' else list(range(19,24))
tri=tri[~np.isin(mat[tri[:,0]],hide)]
mesh=bpy.data.meshes.new('InstalledNative');mesh.from_pydata(p.tolist(),[],tri.tolist());mesh.update()
materials=json.loads((W/'preview-materials.json').read_text(encoding='utf8'))[outfit]
if outfit=='jirai':
 for m in existing:
  bs=m.node_tree.nodes.get('Principled BSDF') if m.use_nodes else None
  if bs:
   for link in bs.inputs['Base Color'].links:
    if link.from_node.type!='TEX_IMAGE':continue
    image=link.from_node.image
    if m.name=='MI_Jirai_Skin':path=R/'private/jirai-face-v3/T_Jirai_Base.png'
    elif m.name=='MI_Jirai_Hair':path=R/'private/jirai-hairpin-v1/T_Jirai_Base.png'
    elif m.name=='MI_Jirai_EyeIris':path=R/'private/jirai-face-v3/T_Face3_Iris.png'
    elif 'Base' in image.name or 'albedo' in image.name.lower():path=W/f'jirai-{tag}.png'
    else:continue
    link.from_node.image=bpy.data.images.load(str(path),check_existing=True)
  mesh.materials.append(m)
else:
 for row in materials:
  m=bpy.data.materials.new(row['slot']);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
  path=Path(row['path'])
  if after and path==W/f'{outfit}-before.png':path=W/f'{outfit}-after.png'
  im=bpy.data.images.load(str(path),check_existing=True);node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
  mesh.materials.append(m)
uv=mesh.uv_layers.new(name='UVMap');tex=d['uv'][:,0].astype(float);tex[:,1]=1-tex[:,1]
for face in mesh.polygons:face.material_index=int(mat[face.vertices[0]]);face.use_smooth=True
for loop in mesh.loops:uv.data[loop.index].uv=tex[loop.vertex_index]
mesh.normals_split_custom_set([norm[l.vertex_index] for l in mesh.loops])
obj=bpy.data.objects.new('InstalledNative',mesh);bpy.context.collection.objects.link(obj)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('PBZ_PATTERN_SAMPLES','8'));scene.render.resolution_percentage=100
scene.render.resolution_x=900;scene.render.resolution_y=1000;scene.view_settings.exposure=.4
views={'upper':((0,-200,155),(0,0,155),68),'back':((0,200,150),(0,3,150),70),'chest':((0,-150,150),(0,0,150),35),'legs':((0,-180,65),(0,0,65),100),'arm':((-85,-130,145),(-23,0,145),28),'waist':((0,-180,119),(0,0,119),42)}
selected=os.environ.get('PBZ_PATTERN_VIEWS','upper,back').split(',');dest=W/os.environ.get('PBZ_PATTERN_DIR','preview');dest.mkdir(exist_ok=True)
for name in selected:
 pos,target,scale=views[name];cam=scene.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
 scene.render.filepath=str(dest/f'{outfit}-{tag}-{name}.png');bpy.ops.render.render(write_still=True)
print('OUTFIT_PATTERN_REVIEW_RENDERED',outfit,tag)
