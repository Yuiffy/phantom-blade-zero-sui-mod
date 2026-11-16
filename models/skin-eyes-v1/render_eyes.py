"""Geometry/material preview only; does not emulate the game's native shaders."""
import bpy, bmesh, json, os, hashlib
from pathlib import Path
from mathutils import Vector

R=Path(__file__).resolve().parents[2];W=R/'private/skin-eyes-v1';O=W/'preview';O.mkdir(exist_ok=True)
views=[('front',(0,-120,177),(0,-1,177),23),
       ('three-quarter',(40,-120,179),(0,-1,177),25),
       ('oblique',(-70,-120,177),(0,-1,177),25)]
for version,root in [('before',R/'private/jirai-detail-v1'),('after',W)]:
    if os.environ.get('PBZ_AFTER_ONLY')=='1' and version=='before':continue
    bpy.ops.wm.open_mainfile(filepath=str(root/'sui-jirai-motion.blend'))
    ob=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=ob.data
    bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS')
    bm.to_mesh(m);bm.free()
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12
    scene.render.resolution_x=1000;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.view_settings.exposure=.4
    for name,pos,target,scale in views:
        cam=scene.camera;cam.location=pos
        cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.ortho_scale=scale
        scene.render.filepath=str(O/(version+'-'+name+'.png'))
        bpy.ops.render.render(write_still=True)
(O/'manifest.json').write_text(json.dumps(dict(basis='offline Blender; eye geometry and authored surface values only; native game skin shader requires gameplay verification',source_fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),views=views),indent=2))
print('EYE_VIEWS_RENDERED')
