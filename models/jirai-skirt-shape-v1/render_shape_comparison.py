"""Same camera and scale: old author rest, new rest, and final cooked settled shape."""
import bpy,bmesh,json,sys,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';V=W/'variant';O=W/'preview/shape';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(C));from current_atlas import apply as apply_atlas
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
for mode in ['before','after-static','after-stopped']:
 path=(R/'private/jirai-skirt-recovery-v1' if mode=='before' else W)/'sui-jirai-motion.blend'
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;apply_atlas(m)
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 if mode=='after-stopped':
  data=np.load(V/'articulation-walk-recover-surface.npz');m.vertices.foreach_set('co',data['source_frames'][-1].ravel());m.update()
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.exposure=.4;cam=s.camera
 for name,pos in [('front',(0,-400,109)),('side',(400,-40,109))]:
  cam.location=pos;cam.rotation_euler=(Vector((0,0,109))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=100
  f=O/f'{mode}-{name}.png';s.render.filepath=str(f);bpy.ops.render.render(write_still=True);rows.append({'mode':mode,'angle':name,'file':str(f),'sha256':sha(f)})
(V/'shape-preview.json').write_text(json.dumps({'images':rows,'basis':'offline same-camera before/after author geometry plus final cooked continuous Chaos settled frame','source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'mapping_sha256':sha(V/'independent/cloth-native-details.json'),'game_runtime_tested':False},indent=2))
print('SHAPE_COMPARISON_RENDERED')
