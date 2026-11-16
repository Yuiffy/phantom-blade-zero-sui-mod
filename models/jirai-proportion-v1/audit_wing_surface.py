"""Check actual mapped padding, ribbons, root and back clearance in all samples."""
import bpy,json,numpy as np,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';W=ROOT/'variant'
detail=json.loads((W/'independent/cloth-native-details.json').read_text())
d=np.load(W/'preview-deformation.npz');rest=d['rest'].copy();rest[:,1]*=-1;faces=d['indices'];uv=d['uv'];materials=d['materials']
records=[]
def surface(q,tri):return BVHTree.FromPolygons([Vector(p) for p in q],tri.tolist(),all_triangles=True)
def gaps(q,tri,points):
 b=surface(q,tri);return np.array([b.find_nearest(Vector(q[i]))[3] for i in points])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');body.data.calc_loop_triangles()
sp=np.array([v.co[:] for v in body.data.vertices]);comp=np.array([a.value for a in body.data.attributes['source_component'].data])
torso_faces=np.array([t.vertices[:] for t in body.data.loop_triangles if all(comp[i] in [0,1,10] and abs(sp[i,0])<15 and 125<sp[i,2]<167 for i in t.vertices)])
torso=surface(sp,torso_faces)
for test in ['60hz','30hz','foreaft']:
 sim=json.loads((W/('simulation-'+test+'.json')).read_text());frames=[]
 for f in sim['frames']:
  p=rest.copy()
  for s in detail['sections']:
   if s['cloth_index']<0:continue
   a=next(a for a in f['assets'] if a['asset_index']==s['cloth_index']);q=np.array(a['component_positions']);n=np.array(a['component_normals']);m=s['cloth_maps'][0];src=np.array(m['source']);bary=np.array(m['position']);alpha=1-src[:,3]/65535
   b=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)])
   mapped=((q[src[:,:3]]+n[src[:,:3]]*bary[:,3,None,None])*b[:,:,None]).sum(1);mapped[:,1]*=-1
   lo=s['base_vertex'];hi=lo+s['vertices'];p[lo:hi]=rest[lo:hi]*(1-alpha[:,None])+mapped*alpha[:,None]
  frames.append(p)
 frames=np.array(frames)
 wings=[]
 for s in detail['sections']:
  if s['slot'] not in ['MI_Jirai_WingL','MI_Jirai_WingR']:continue
  ids=np.arange(s['base_vertex'],s['base_vertex']+s['vertices']);tri=faces[materials==s['material']]
  white=tri[np.all(uv[tri,0]<.5,axis=1)];ribbon=ids[uv[ids,0]>.5]
  baseline=gaps(rest,white,ribbon);ribbon_gap=np.array([gaps(q,white,ribbon) for q in frames])
  edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
  l0=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);edges=edges[l0>.05];l0=l0[l0>.05]
  ratio=np.linalg.norm(frames[:,edges[:,0]]-frames[:,edges[:,1]],axis=2)/l0
  roots=ids[np.abs(rest[ids,0])<10.5];tips=ids[np.abs(rest[ids,0])>32]
  dz=(frames[:,tips]-rest[tips])[:,:,2];pin=float(np.linalg.norm(frames[:,roots]-rest[roots],axis=2).max());gapchange=float(np.abs(ribbon_gap-baseline).max())
  assert pin<.35,(test,s['slot'],'visible root moved',pin)
  assert .70<ratio.min() and ratio.max()<1.25,(test,s['slot'],'visible shape',ratio.min(),ratio.max())
  assert gapchange<.3,(test,s['slot'],'ribbons separating',gapchange)
  # Lateral+yaw has no pitch/roll/heave stimulus. Require visible vertical
  # response in the fore/aft+pitch/roll case; all profiles must still move in
  # the separate physical validation, with the same strict shape limits here.
  if test=='foreaft':assert float(np.ptp(dz[7:]))>.1,(test,s['slot'],'no vertical response to pitch/roll')
  clearances=[]
  for q in frames:
   for i in ids[np.abs(rest[ids,0])<15][::3]:
    p=q[i];hit,_,_,_=torso.ray_cast(Vector((p[0],80,p[2])),Vector((0,-1,0)),120)
    if hit is not None:clearances.append(float(p[1]-hit.y))
  assert clearances and min(clearances)>.15,(test,s['slot'],'reference-pose back clearance',min(clearances) if clearances else None)
  wings.append({'slot':s['slot'],'visible_root_max_displacement_cm':pin,'visible_edge_ratio_min':float(ratio.min()),'visible_edge_ratio_max':float(ratio.max()),'tip_vertical_displacement_cm':[float(dz.min()),float(dz.max())],'tip_vertical_range_after_warmup_cm':float(np.ptp(dz[7:])),'ribbon_to_padding_gap_max_change_cm':gapchange,'ribbon_gap_baseline_cm':[float(baseline.min()),float(baseline.max())],'sampled_back_clearance_min_cm':min(clearances),'back_clearance_scope':'reference-pose-torso-only'})
 records.append({'test':test,'wings':wings})
report={'passed':True,'basis':'actual-Chaos-samples-and-final-cooked-GPU-cloth-mapping','fbx_sha256':hashlib.sha256((ROOT/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'body_native_export_sha256':detail['raw_native_export_sha256'],'tests':records,'game_runtime_tested':False,'bone_animations_tested':False}
(W/'wing-surface-verification.json').write_text(json.dumps(report,indent=2));print('WING_SURFACE_AUDIT_OK',json.dumps(report),flush=True)
