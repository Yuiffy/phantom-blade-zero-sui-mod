"""Offline photo inspection of the actual reconstructed cloth render surface."""
import bpy,bmesh,json,os,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';V=W/'variant';O=W/'preview';reports=[]
for profile in ['crouch','run','head-arms']:
 bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles();arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 comp=np.array([x.value for x in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);tri=np.array([t.vertices[:] for t in m.loop_triangles]);slots=[m.materials[t.material_index].name for t in m.loop_triangles]
 skin_tri=[tuple(t) for t in tri if all(comp[i]==5 for i in t)];skirt_tri=[tuple(t) for t,slot in zip(tri,slots) if slot=='MI_Jirai_Skirt'];skin_edges=sorted({tuple(sorted((t[i],t[j]))) for t in skin_tri for i,j in [(0,1),(1,2),(2,0)] if all(78<rest[k,2]<109 for k in [t[i],t[j]])})
 garment_tri=[tuple(t) for t,slot in zip(tri,slots) if slot in ['MI_Jirai_Blouse','MI_Jirai_Corset']]
 hair_edges=sorted({tuple(sorted((int(t[i]),int(t[j])))) for t,slot in zip(tri,slots) if slot in ['MI_Jirai_TailL','MI_Jirai_TailR','MI_Jirai_SideL','MI_Jirai_SideR'] for i,j in [(0,1),(1,2),(2,0)] if all(rest[k,2]<170 for k in [t[i],t[j]])})
 data=np.load(V/('articulation-'+profile+'-surface.npz'));frames=data['source_frames'];steps=data['steps'];audit=[]
 for index,p in enumerate(frames):
  bvh=BVHTree.FromPolygons([Vector(a) for a in p],skirt_tri,all_triangles=True);cross=[]
  for a,b in skin_edges:
   delta=Vector(p[b]-p[a]);length=delta.length
   if length<.01:continue
   hit,_,_,dist=bvh.ray_cast(Vector(p[a]),delta/length,length)
   if hit is not None and .015<dist<length-.015:cross.append([int(a),int(b),float(dist)])
  garment=BVHTree.FromPolygons([Vector(a) for a in p],garment_tri,all_triangles=True);hair_cross=[]
  for a,b in hair_edges:
   delta=Vector(p[b]-p[a]);length=delta.length
   if length<.01:continue
   hit,_,_,dist=garment.ray_cast(Vector(p[a]),delta/length,length)
   if hit is not None and .015<dist<length-.015:hair_cross.append([a,b,float(dist)])
  audit.append({'frame':index,'step':int(steps[index]),'visible_thigh_edges_crossing_skirt':len(cross),'edge_examples':cross[:8],'hair_edges_crossing_garment':len(hair_cross),'hair_edge_examples':hair_cross[:8]})
 # Exclude warmup and choose the largest lower-leg movement, or head movement.
 zone=(comp==5)&(rest[:,2]>50)&(rest[:,2]<105) if profile!='head-arms' else (comp==0)&(rest[:,2]>173)
 movement=np.linalg.norm(frames[:,zone]-rest[zone],axis=2).max(1);peak=int(np.argmax(movement));p=frames[peak];m.vertices.foreach_set('co',p.ravel());m.update()
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=8;s.render.resolution_x=900;s.render.resolution_y=900;s.view_settings.exposure=.4;cam=s.camera
 views=[('side',(350,-80,105),(0,-5,105),190),('front',(0,-400,105),(0,-5,102),200),('rear',(0,400,105),(0,-5,103),195)] if profile!='head-arms' else [('front',(0,-400,167),(0,0,166),100),('side',(400,-80,165),(0,0,165),100)]
 if os.environ.get('PBZ_ONLY_AUDIT')=='1':views=[]
 for name,pos,target,scale in views:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;s.render.filepath=str(O/(profile+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
 reports.append({'profile':profile,'rendered_frame':peak,'rendered_step':int(steps[peak]),'fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'pose_contract_sha256':hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),'basis':'actual offline animated solver output reconstructed through cooked GPU cloth mapping','thigh_edge_intersections':audit,'game_runtime_tested':False})
(V/'articulated-surface-audit.json').write_text(json.dumps(reports,indent=2));print('ARTICULATED_SURFACE_INSPECTION_DONE')
