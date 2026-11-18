"""Author inspection: actual posed opaque shorts with the skirt hidden."""
import bpy,bmesh,json,hashlib
import numpy as np
import sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-shape-v1';V=W/'variant';O=W/'preview';report=[]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from current_atlas import apply as apply_atlas
for profile in ['wide-crouch','diagonal-crouch','lunge-right']:
 bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;c=np.array([d.value for d in m.attributes['source_component'].data]);frames=np.load(V/('articulation-'+profile+'-surface.npz'));p=frames['source_frames'][-1]
 atlas=apply_atlas(m)
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 m.vertices.foreach_set('co',p.ravel());m.update();target=Vector(np.mean(p[c==920],axis=0))
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer] not in [5,920]],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=760;s.render.resolution_y=760;s.view_settings.exposure=.4;cam=s.camera
 for name,delta in [('front',(120,-300,35)),('underside',(120,-300,-90))]:
  cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=88;s.render.filepath=str(O/('coverage-'+profile+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
 report.append(dict(profile=profile,step=int(frames['steps'][-1]),fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),cloth_spec_sha256=hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),basis='actual offline cooked reconstruction; skirt hidden for coverage inspection',game_runtime_tested=False))
(V/'coverage-preview.json').write_text(json.dumps(report,indent=2));print('COVERAGE_PREVIEWS_DONE')
