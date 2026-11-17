"""Identical lights and views as Face2, with the new geometry and color."""
from pathlib import Path
import bpy,bmesh,json,os
import numpy as np
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v3';O=W/'preview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/'candidate.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
atlas=bpy.data.images.load(str(W/'T_Jirai_Base.png'),check_existing=True)
baseline=bpy.data.images.load(str(R/'private/fishnet-v1/T_Jirai_Base.png'),check_existing=True)
skin=m.materials['MI_Jirai_Skin'];old=next(l.from_node.image for l in skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links if l.from_node.type=='TEX_IMAGE')
for mat in m.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image==old:
   node.image=atlas if mat.name in ['MI_Jirai_Skin','MI_Jirai_Hair','MI_Jirai_EyeIris'] else baseline
# Smooth iris and sclera normals analytically in the authoring preview. The
# native patch will independently encode the same per-vertex tangent frames.
for f in m.polygons:
 if f.material_index in [18,19]:f.use_smooth=True
# Rebuild eye normals explicitly; the source imported custom normals retain
# polygonal glare even when the polygon smooth flag is enabled.
m.update()
normals=np.array([n.vector[:] for n in m.corner_normals])
components=np.array([v.value for v in m.attributes['source_component'].data])
for loop in m.loops:
 cid=components[loop.vertex_index]
 if cid not in [51,52,950,951]:continue
 x,y,z=m.vertices[loop.vertex_index].co;cx=-5.317217 if cid in [51,950] else 4.614422;sign=1 if cx<0 else -1
 dx=x-cx;dz=z-177.799362
 if cid in [51,52]:
  s=max(.01,(max(0,1-(dx/3.1)**2-(dz/2)**2))**.5)
  n=np.array([1.4*dx/(3.1**2*s)-.3*sign,-1,1.4*dz/(4*s)])
 else:
  yy=y+.9+.3*sign*dx
  n=np.array([dx/(3.1**2)+.3*sign*yy/(1.4**2),yy/(1.4**2),dz/4])
 normals[loop.index]=n/np.linalg.norm(n)
m.normals_split_custom_set(normals)
m.materials['MI_Jirai_EyeIris'].node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=140/255
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=int(os.environ.get('PBZ_FACE_SAMPLES','8'))
s.render.resolution_x=1100;s.render.resolution_y=1000;s.render.resolution_percentage=int(os.environ.get('PBZ_FACE_PERCENT','70'));s.view_settings.exposure=.4
views=[('front',(-.35,-120,180)),('left',(-45,-120,180)),('right',(45,-120,180))]
if os.environ.get('PBZ_FACE_FRONT_ONLY')=='1':views=views[:1]
for name,pos in views:
 cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector((-.35,0,180))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=23
 s.render.filepath=str(O/f'after-{name}.png');bpy.ops.render.render(write_still=True)
atlas.pack();bpy.ops.wm.save_as_mainfile(filepath=str(W/'face-preview.blend'),compress=True)
print('FACE3_PREVIEWS_RENDERED')
