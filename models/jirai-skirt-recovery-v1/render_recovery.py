"""Peak motion versus the final stationary pose, from cooked reconstruction."""
import bpy,bmesh,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
C=Path(__file__).resolve().parent;sys.path.insert(0,str(C))
from current_atlas import apply as apply_atlas
W=C.parents[1]/'private/jirai-skirt-recovery-v1';V=W/'variant';O=W/'preview/recovery';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
stamp=json.loads((V/'articulated-reconstruction.json').read_text());assert stamp['combined_tests_sha256']==sha(V/'combined-tests.json')
rows=[]
for profile in ['walk-recover','jog-recover','crouch-recover']:
 data=np.load(V/f'articulation-{profile}-surface.npz');frames=data['source_frames'];steps=data['steps']
 bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;atlas=apply_atlas(m)
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 comp=np.array([x.value for x in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);zone=(comp==5)&(rest[:,2]>50)&(rest[:,2]<105)
 skirt={i for f in m.polygons if m.materials[f.material_index].name=='MI_Jirai_Skirt' for i in f.vertices}
 hem=np.array([i for i in skirt if 100<rest[i,2]<116 and np.linalg.norm(rest[i,:2]-[0,5])>18])
 neutral=frames[int(np.argmin(abs(steps-60)))]
 peak=int(np.argmax(np.percentile(frames[:,hem,2]-neutral[hem,2],95,axis=1)))
 for phase,index in [('moving',peak),('stopped',len(frames)-1)]:
  bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;apply_atlas(m)
  for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
  m.vertices.foreach_set('co',frames[index].ravel());m.update()
  bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
  s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=800;s.view_settings.exposure=.4;cam=s.camera
  for name,pos in [('front',(0,-400,106)),('side',(350,-80,106))]:
   cam.location=pos;cam.rotation_euler=(Vector((0,-5,108))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=100
   path=O/f'{profile}-{phase}-{name}.png';s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
   rows.append({'profile':profile,'phase':phase,'step':int(steps[index]),'file':str(path),'sha256':sha(path)})
(V/'recovery-preview.json').write_text(json.dumps({'basis':'offline Blender rendering of actual continuous Chaos through final cooked GPU mapping','fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'cloth_spec_sha256':sha(W/'cloth-spec.json'),'combined_tests_sha256':sha(V/'combined-tests.json'),'mapping_sha256':sha(V/'independent/cloth-native-details.json'),'atlas':atlas,'images':rows,'game_runtime_tested':False},indent=2))
print('RECOVERY_PREVIEWS_READY',len(rows))
