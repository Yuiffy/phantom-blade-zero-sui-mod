"""Check the final reconstructed standing silhouette and shorts concealment."""
import bpy,bmesh,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-shape-v1';V=W/'variant'
sys.path.insert(0,str(Path(__file__).resolve().parent))
from current_atlas import apply as apply_atlas
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
atlas=apply_atlas(m);data=np.load(V/'articulation-crouch-surface.npz')
for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
m.vertices.foreach_set('co',data['source_frames'][0].ravel());m.update()
bm=bmesh.new();bm.from_mesh(m);c=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[c]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
s=bpy.context.scene;s.cycles.samples=8;s.render.resolution_x=800;s.render.resolution_y=1100;s.render.resolution_percentage=100;s.view_settings.exposure=.4;cam=s.camera
for name,pos in [('front',(0,-400,105)),('rear',(0,400,105)),('side',(400,-60,105))]:
 cam.location=pos;cam.rotation_euler=(Vector((0,0,100))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=205;s.render.filepath=str(W/'preview'/('standing-'+name+'.png'));bpy.ops.render.render(write_still=True)
(V/'rest-preview.json').write_text(json.dumps(dict(fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),basis='final cooked reconstruction, zero-time standing frame',atlas=atlas,game_runtime_tested=False),indent=2))
