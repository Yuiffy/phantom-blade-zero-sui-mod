import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';V=W/'variant';O=W/'preview'
for profile in ['crouch','run']:
 bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;c=np.array([x.value for x in m.attributes['source_component'].data]);rest=np.array([x.co[:] for x in m.vertices]);d=np.load(V/('articulation-'+profile+'-surface.npz'));frames=d['source_frames'];ids=c==940;peak=int(np.argmax(np.linalg.norm(frames[:,ids]-rest[ids],axis=2).max(1)));p=frames[peak]
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 m.vertices.foreach_set('co',p.ravel());m.update();target=p[ids].mean(0)
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=8;s.render.resolution_x=850;s.render.resolution_y=850;s.view_settings.exposure=.4;cam=s.camera;cam.location=target+np.array([80,-300,90]);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=60;s.render.filepath=str(O/('suspender-'+profile+'.png'));bpy.ops.render.render(write_still=True)
print('SUSPENDER_POSE_RENDERS_DONE')
