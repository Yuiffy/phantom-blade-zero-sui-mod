"""Render the exact bounded native vertex/UV/normal readback, not an approximation."""
from pathlib import Path
import bpy,numpy as np,os,json
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v3';O=W/os.environ.get('PBZ_PREVIEW_DIR','native-preview');O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/'face-preview.blend'))
old=next(x for x in bpy.context.scene.objects if x.type=='MESH')
materials=list(old.data.materials)
before=os.environ.get('PBZ_FACE_BEFORE')=='1'
atlas=bpy.data.images.load(str(R/'private/jirai-face-v2/T_Jirai_Base.png' if before else W/'T_Jirai_Base.png'),check_existing=False)
iris=bpy.data.images.load(str(R/'private/fishnet-v1/T_Jirai_Base.png' if before else W/os.environ.get('PBZ_IRIS_SOURCE','T_Face3_Iris.png')),check_existing=False)
for mat in materials:
    if mat.name not in ['MI_Jirai_Skin','MI_Jirai_Hair','MI_Jirai_EyeIris']:continue
    bs=mat.node_tree.nodes.get('Principled BSDF')
    for link in bs.inputs['Base Color'].links:
        if link.from_node.type=='TEX_IMAGE':link.from_node.image=iris if mat.name=='MI_Jirai_EyeIris' else atlas
    if mat.name=='MI_Jirai_EyeIris':bs.inputs['Roughness'].default_value=.26 if before else 140/255
data=np.load(W/('native/baseline-render.npz' if before else os.environ.get('PBZ_NATIVE_SOURCE','native/final-render.npz')))
pos=data['positions'].copy();pos[:,1]*=-1
norm=data['normals'].copy();norm[:,1]*=-1
tri=data['indices'].reshape(-1,3).copy()
# The exported UE triangle order becomes the source Blender winding after
# reflecting its Y axis; no second reversal is required.
native_material=data['materials'];keep=~np.isin(native_material[tri[:,0]],[15,16,17])
tri=tri[keep]
m=bpy.data.meshes.new('Face3_FinalNativeReadback');m.from_pydata(pos.tolist(),[],tri.tolist());m.update()
for mat in materials:m.materials.append(mat)
uv=m.uv_layers.new(name='UVMap')
source_uv=data['uv'][:,0].copy()
# FBX/UE stores V in image-down convention. Restore Blender's V-up UVs.
source_uv[:,1]=1-source_uv[:,1]
corner_norm=[]
for f in m.polygons:
    f.material_index=int(native_material[f.vertices[0]]);f.use_smooth=True
for loop in m.loops:
    uv.data[loop.index].uv=source_uv[loop.vertex_index]
    corner_norm.append(norm[loop.vertex_index])
m.normals_split_custom_set(corner_norm)
o=bpy.data.objects.new('Face3_FinalNativeReadback',m);bpy.context.collection.objects.link(o)
bpy.data.objects.remove(old,do_unlink=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('PBZ_FACE_SAMPLES','16'))
s.render.resolution_x=1100;s.render.resolution_y=1000;s.render.resolution_percentage=int(os.environ.get('PBZ_FACE_PERCENT','100'));s.view_settings.exposure=.4
views=[('front',(-.35,-120,180)),('left',(-45,-120,180)),('right',(45,-120,180))]
if os.environ.get('PBZ_FACE_FRONT_ONLY')=='1':views=views[:1]
for name,position in views:
    cam=s.camera;cam.location=position;cam.rotation_euler=(Vector((-.35,0,180))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=23
    s.render.filepath=str(O/f'{"before" if before else "after"}-{name}.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'native-preview.blend'),compress=True)
print('FACE3_NATIVE_PREVIEW_RENDERED')
