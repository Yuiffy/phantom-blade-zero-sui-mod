"""Compare identical source geometry/cameras with only the face atlas changed."""
from pathlib import Path
import bpy,bmesh,json,os
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v2';O=W/'preview';O.mkdir(exist_ok=True)
views=[('front',(-.35,-120,180),(-.35,0,180),23),('left',(-45,-120,180),(-.35,0,180),23),('right',(45,-120,180),(-.35,0,180),23)]
for version,path in [('before',R/'private/fishnet-v1/T_Jirai_Base.png'),('after',W/'T_Jirai_Base.png')]:
 if os.environ.get('PBZ_AFTER_ONLY')=='1' and version=='before':continue
 bpy.ops.wm.open_mainfile(filepath=str(R/'private/skin-eyes-v1/sui-jirai-motion.blend'))
 o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
 image=bpy.data.images.load(str(path),check_existing=True)
 baseline=bpy.data.images.load(str(R/'private/fishnet-v1/T_Jirai_Base.png'),check_existing=True)
 skin=m.materials['MI_Jirai_Skin'];old=next(l.from_node.image for l in skin.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links if l.from_node.type=='TEX_IMAGE')
 for mat in m.materials:
  if not mat.use_nodes:continue
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image==old:node.image=image if mat.name in ['MI_Jirai_Skin','MI_Jirai_Hair'] else baseline
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free()
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16
 s.render.resolution_x=1100;s.render.resolution_y=1000;s.render.resolution_percentage=100
 s.view_settings.exposure=.4
 for name,pos,target,scale in views:
  cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale
  s.render.filepath=str(O/f'{version}-{name}.png');bpy.ops.render.render(write_still=True)
 # Retain an editable head/body source with the exact replacement atlas.
 if version=='after':
  image.pack();bpy.ops.wm.save_as_mainfile(filepath=str(W/'face-preview.blend'),compress=True)
(O/'manifest.json').write_text(json.dumps(dict(basis='offline Cycles; same source geometry, lights and cameras; PBZ shaders and gameplay untested',views=views,geometry_source='private/skin-eyes-v1/sui-jirai-motion.blend'),indent=2))
print('FACE_PREVIEWS_RENDERED')
