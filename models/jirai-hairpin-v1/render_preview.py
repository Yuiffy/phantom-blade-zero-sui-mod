"""Review the native readback with the installed face and isolated hair albedo."""
from pathlib import Path
import bpy,numpy as np,os
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-hairpin-v1';F=R/'private/jirai-face-v3'
before=os.environ.get('PBZ_PIN_BEFORE')=='1'
path=F/'native/final-render.npz' if before else W/('final-render.npz' if (W/'final-render.npz').exists() else 'patched-render.npz')
data=np.load(path)
bpy.ops.wm.open_mainfile(filepath=str(F/'face-preview.blend'))
old=next(x for x in bpy.context.scene.objects if x.type=='MESH');materials=list(old.data.materials)
for mat in materials:
 if mat.name not in ['MI_Jirai_Skin','MI_Jirai_Hair','MI_Jirai_EyeIris']:continue
 image_path=F/'T_Face3_Iris.png' if mat.name=='MI_Jirai_EyeIris' else (W/'T_Jirai_Base.png' if mat.name=='MI_Jirai_Hair' and not before else F/'T_Jirai_Base.png')
 im=bpy.data.images.load(str(image_path),check_existing=False)
 bs=mat.node_tree.nodes.get('Principled BSDF')
 for link in bs.inputs['Base Color'].links:
  if link.from_node.type=='TEX_IMAGE':link.from_node.image=im
 if mat.name=='MI_Jirai_EyeIris':bs.inputs['Roughness'].default_value=140/255
p=data['positions'].copy();p[:,1]*=-1;norm=data['normals'].copy();norm[:,1]*=-1
tri=data['indices'].reshape(-1,3);mat=data['materials'];tri=tri[~np.isin(mat[tri[:,0]],[15,16,17])]
# Retain the fixed-count native buffer's intentionally inactive triangles;
# Blender ignores these zero-area reserve slots, as does the GPU draw.
mesh=bpy.data.meshes.new('Hairpin1_NativeReadback');mesh.from_pydata(p.tolist(),[],tri.tolist());mesh.update()
for material in materials:mesh.materials.append(material)
uv=mesh.uv_layers.new(name='UVMap');tex=data['uv'][:,0].copy();tex[:,1]=1-tex[:,1]
for face in mesh.polygons:face.material_index=int(mat[face.vertices[0]]);face.use_smooth=True
for loop in mesh.loops:uv.data[loop.index].uv=tex[loop.vertex_index]
mesh.normals_split_custom_set([norm[l.vertex_index] for l in mesh.loops])
obj=bpy.data.objects.new('Hairpin1_NativeReadback',mesh);bpy.context.collection.objects.link(obj);bpy.data.objects.remove(old,do_unlink=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=int(os.environ.get('PBZ_PIN_SAMPLES','8'))
scene.render.resolution_x=1100;scene.render.resolution_y=1000;scene.render.resolution_percentage=int(os.environ.get('PBZ_PIN_PERCENT','70'));scene.view_settings.exposure=.4
views=[('front',(-.35,-120,180),(-.35,0,180),23),('detail',(8.9,-70,185),(8.9,-1,184.5),8.5),('angled',(30,-40,186),(8.9,-1,184.5),8.5)]
if os.environ.get('PBZ_PIN_VIEW'):views=[v for v in views if v[0]==os.environ['PBZ_PIN_VIEW']]
dest=W/os.environ.get('PBZ_PIN_PREVIEW_DIR','preview');dest.mkdir(exist_ok=True)
for name,position,target,scale in views:
 cam=scene.camera;cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
 scene.render.filepath=str(dest/f'{"before" if before else "after"}-{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'hairpin-preview.blend'),compress=True)
print('HAIRPIN_NATIVE_PREVIEW_RENDERED')
