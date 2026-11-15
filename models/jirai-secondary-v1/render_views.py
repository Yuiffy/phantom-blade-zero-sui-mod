"""Offline inspection renders, with explicit camera/pose manifests."""
import bpy,bmesh,json,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';O=W/'preview';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
scene=bpy.context.scene;scene.cycles.samples=8;scene.render.resolution_x=850;scene.render.resolution_y=900;scene.view_settings.exposure=.4;cam=scene.camera
views=[('thigh-back',(0,300,82),(6,5,105),52),('suspender-front',(30,-300,90),(12,0,102),38),('suspender-detail',(10,-300,94),(11,-2,94.5),17),('suspender-side',(160,-300,94),(11,-2,97),25),('hair-front',(0,-400,168),(0,0,169),85),('hair-side',(400,-80,160),(0,6,165),90),('full-front',(0,-400,110),(0,0,102),220),('full-back',(0,400,110),(0,0,102),220),('full-left',(400,-60,110),(0,0,102),220),('full-right',(-400,-60,110),(0,0,102),220)]
for name,pos,target,scale in views:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
(O/'manifest.json').write_text(json.dumps({'source':str(W/'sui-jirai-motion.blend'),'basis':'offline Blender neutral pose; not game screenshots','views':[{'name':name,'camera':pos,'target':target,'ortho_cm':scale} for name,pos,target,scale in views]},indent=2));print('INSPECTION_RENDERS_OK')
