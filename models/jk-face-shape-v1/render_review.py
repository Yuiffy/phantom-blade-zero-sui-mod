"""Render native input/output at fixed cameras using installed source PNGs."""
from pathlib import Path
import bpy, numpy as np, os, json, hashlib
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jk-face-shape-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-face-v3/face-preview.blend'))
for o in [o for o in bpy.context.scene.objects if o.type=='MESH']:
    bpy.data.objects.remove(o,do_unlink=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
s.render.resolution_x=900;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.view_settings.exposure=.4
out=W/os.environ.get('PBZ_FACE_PREVIEW','preview');out.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest={}
for tag in os.environ.get('PBZ_FACE_TAGS','before,authored').split(','):
    manifest[tag]={'native_sha256':sha(W/(tag+'.npz')),'images':{}}
    d=np.load(W/(tag+'.npz'));p=d['positions'].copy();p[:,1]*=-1;n=d['normals'].copy();n[:,1]*=-1
    mat=d['materials'];tri=d['indices'].reshape(-1,3);tri=tri[mat[tri[:,0]]<19]
    mesh=bpy.data.meshes.new('JK_Native');mesh.from_pydata(p.tolist(),[],tri.tolist());mesh.update()
    for row in json.loads((R/'private/outfit-patterns-v1/preview-materials.json').read_text())['jk']:
        m=bpy.data.materials.new(row['slot']);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
        path=Path(row['path'])
        if path.name=='jk-before.png':path=R/'private/outfit-patterns-v1/jk-after.png'
        im=bpy.data.images.load(str(path),check_existing=True);tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;m.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(m)
    uv=mesh.uv_layers.new(name='UVMap');tex=d['uv'][:,0].astype(float);tex[:,1]=1-tex[:,1]
    for f in mesh.polygons:f.material_index=int(mat[f.vertices[0]]);f.use_smooth=True
    for l in mesh.loops:uv.data[l.index].uv=tex[l.vertex_index]
    mesh.normals_split_custom_set([n[l.vertex_index] for l in mesh.loops])
    obj=bpy.data.objects.new('JK_Native',mesh);bpy.context.collection.objects.link(obj)
    views=[('front',(-.42,-120,180.5),(-.42,0,180.5),29),('threequarter',(-48,-120,179),(-.42,0,179),29),('side',(-120,-5,179),(-.42,-2,179),29)]
    for name,pos,target,scale in views:
        if name not in os.environ.get('PBZ_FACE_VIEWS','front,threequarter,side').split(','):continue
        cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
        s.render.filepath=str(out/(tag+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
        manifest[tag]['images'][str(Path(s.render.filepath))]=sha(Path(s.render.filepath))
    if tag!='before':bpy.ops.wm.save_as_mainfile(filepath=str(W/'JK_FaceShape_Editable.blend'),compress=True)
    bpy.data.objects.remove(obj,do_unlink=True)
(out/'render-manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
print('JK_FACE_REVIEW_RENDERED')
