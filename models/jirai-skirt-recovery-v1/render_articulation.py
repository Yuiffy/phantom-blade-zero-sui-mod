"""Offline photo inspection of the actual reconstructed cloth render surface."""
import bpy,bmesh,json,os,hashlib,math
import numpy as np
import sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-recovery-v1';V=W/'variant';O=W/'preview';reports=[]
sys.path.insert(0,str(Path(__file__).resolve().parent))
from current_atlas import apply as apply_atlas
if os.environ.get('PBZ_BASELINE')=='1':
 V=W/'baseline';O=W/'preview/baseline';W=R/'private/jirai-detail-v1'
O.mkdir(parents=True,exist_ok=True)
if os.environ.get('PBZ_BASELINE')!='1':
 stamp=json.loads((V/'articulated-reconstruction.json').read_text())
 assert stamp['combined_tests_sha256']==hashlib.sha256((V/'combined-tests.json').read_bytes()).hexdigest()
 assert stamp['cooked_mapping_sha256']==hashlib.sha256((V/'independent/cloth-native-details.json').read_bytes()).hexdigest()
for profile in list(json.loads((R/'private/jirai-skirt-recovery-v1/pose-contract.json').read_text())['clips']):
 bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles();arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
 atlas=apply_atlas(m) if os.environ.get('PBZ_BASELINE')!='1' else None
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 comp=np.array([x.value for x in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);slots=[m.materials[t.material_index].name for t in m.loop_triangles]
 skin_tri=[tuple(t) for t,slot in zip(tri,slots) if all(comp[i]==5 for i in t) and slot=='MI_Jirai_Skin'];skirt_tri=[tuple(t) for t,slot in zip(tri,slots) if slot=='MI_Jirai_Skirt'];skin_edges=sorted({tuple(sorted((t[i],t[j]))) for t in skin_tri for i,j in [(0,1),(1,2),(2,0)] if all(78<rest[k,2]<119 for k in [t[i],t[j]])})
 garment_tri=[tuple(t) for t,slot in zip(tri,slots) if slot in ['MI_Jirai_Blouse','MI_Jirai_Corset']]
 hair_edges=sorted({tuple(sorted((int(t[i]),int(t[j])))) for t,slot in zip(tri,slots) if slot in ['MI_Jirai_TailL','MI_Jirai_TailR','MI_Jirai_SideL','MI_Jirai_SideR'] for i,j in [(0,1),(1,2),(2,0)] if all(rest[k,2]<170 for k in [t[i],t[j]])})
 opaque_tri=[tuple(t) for t in tri if all(comp[i]<2000 for i in t)]
 eligible={tuple(t) for t in skirt_tri+skin_tri}
 eligible_occluder=[t in eligible for t in opaque_tri]
 data=np.load(V/('articulation-'+profile+'-surface.npz'));frames=data['source_frames'];steps=data['steps'];audit=[]
 for index,p in enumerate(frames):
  bvh=BVHTree.FromPolygons([Vector(a) for a in p],skirt_tri,all_triangles=True);cross=[];visible_cross=[]
  occluder=BVHTree.FromPolygons([Vector(a) for a in p],opaque_tri,all_triangles=True)
  directions=[Vector((math.cos(az)*math.cos(el),math.sin(az)*math.cos(el),math.sin(el))) for az in np.linspace(0,math.tau,16,endpoint=False) for el in np.radians([0,20,45,70])]
  for a,b in skin_edges:
   delta=Vector(p[b]-p[a]);length=delta.length
   if length<.01:continue
   hit,_,_,dist=bvh.ray_cast(Vector(p[a]),delta/length,length)
   if hit is not None and .015<dist<length-.015:
    cross.append([int(a),int(b),float(dist)])
    for direction in directions:
     first,_,face_index,d=occluder.ray_cast(hit+direction*200,-direction,200.05)
     # Trace the complete opaque model, including the other thigh, torso and
     # shorts. A contact behind the character's own body is not visible.
     if first is not None and eligible_occluder[face_index] and 199.92<=d<=200.015:
      visible_cross.append([int(a),int(b),float(dist)]);break
  garment=BVHTree.FromPolygons([Vector(a) for a in p],garment_tri,all_triangles=True);hair_cross=[]
  for a,b in hair_edges:
   delta=Vector(p[b]-p[a]);length=delta.length
   if length<.01:continue
   hit,_,_,dist=garment.ray_cast(Vector(p[a]),delta/length,length)
   if hit is not None and .015<dist<length-.015:hair_cross.append([a,b,float(dist)])
  audit.append({'frame':index,'step':int(steps[index]),'visible_thigh_edges_crossing_skirt':len(visible_cross),'raw_thigh_edge_intersections':len(cross),'edge_examples':visible_cross[:8],'raw_edge_examples':cross[:8],'hair_edges_crossing_garment':len(hair_cross),'hair_edge_examples':hair_cross[:8]})
 # Exclude warmup and choose the largest lower-leg movement, or head movement.
 zone=(comp==5)&(rest[:,2]>50)&(rest[:,2]<105) if profile!='head-arms' else (comp==0)&(rest[:,2]>173)
 movement=np.linalg.norm(frames[:,zone]-rest[zone],axis=2).max(1);peak=int(np.argmax(movement));p=frames[peak];m.vertices.foreach_set('co',p.ravel());m.update()
 if os.environ.get('PBZ_WORST_CONTACT')=='1':
  worst=max([x for x in audit if x['step']>=90],key=lambda x:x['visible_thigh_edges_crossing_skirt'])
  if worst['visible_thigh_edges_crossing_skirt']>0:peak=worst['frame']
  p=frames[peak];m.vertices.foreach_set('co',p.ravel());m.update()
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=8;s.render.resolution_x=900;s.render.resolution_y=900;s.view_settings.exposure=.4;cam=s.camera
 views=[('rear',(0,400,100),(0,-5,96),110),('side',(350,-80,100),(0,-5,96),110),('front',(0,-400,100),(0,-5,96),110),('high3q',(170,-300,245),(0,-5,96),115)] if profile!='head-arms' else [('front',(0,-400,167),(0,0,166),100),('side',(400,-80,165),(0,0,165),100)]
 if os.environ.get('PBZ_ONLY_AUDIT')=='1' or profile not in os.environ.get('PBZ_RENDER_PROFILES','crouch,wide-crouch,diagonal-crouch,run').split(','):views=[]
 if os.environ.get('PBZ_RENDER_VIEWS'):views=[v for v in views if v[0] in os.environ['PBZ_RENDER_VIEWS'].split(',')]
 for name,pos,target,scale in views:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(O/(profile+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
 reports.append({'profile':profile,'rendered_frame':peak,'rendered_step':int(steps[peak]),'fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'pose_contract_sha256':hashlib.sha256((R/'private/jirai-skirt-recovery-v1/pose-contract.json').read_bytes()).hexdigest(),'basis':'actual offline animated solver output reconstructed through cooked GPU cloth mapping','skin_scope':'only actual skin material triangles; opaque safety-short faces are reported as clothing','contact_visibility':'64 full-model occlusion rays per contact: 16 azimuths x elevations 0,20,45,70 deg; all opaque body and clothing included; raw intersections retained separately; no game camera claim','thigh_edge_intersections':audit,'game_runtime_tested':False})
(V/'articulated-surface-audit.json').write_text(json.dumps(reports,indent=2))
if os.environ.get('PBZ_BASELINE')!='1':(V/'preview-atlas.json').write_text(json.dumps(atlas,indent=2))
print('ARTICULATED_SURFACE_INSPECTION_DONE')
