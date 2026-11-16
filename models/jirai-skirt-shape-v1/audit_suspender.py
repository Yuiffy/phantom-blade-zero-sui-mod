"""Check rebuilt strap and buckle against posed cooked thigh surfaces."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-shape-v1';V=W/'variant'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));m=next(x for x in bpy.context.scene.objects if x.type=='MESH').data;m.calc_loop_triangles()
c=np.array([v.value for v in m.attributes['source_component'].data]);rest=np.array([v.co[:] for v in m.vertices]);faces=[tuple(t.vertices) for t in m.loop_triangles if all(c[i]==5 for i in t.vertices)]
assert 77 not in c and all(t.normal.y<-.5 for t in m.loop_triangles if all(c[i]==940 for i in t.vertices)),'strap front winding'
out=[]
for profile in list(json.loads((W/'pose-contract.json').read_text())['clips']):
 d=np.load(V/('articulation-'+profile+'-surface.npz'));frames=d['source_frames'];steps=d['steps']
 for i,p in enumerate(frames):
  tree=BVHTree.FromPolygons([Vector(a) for a in p],faces,all_triangles=True)
  for cid in [940,941]:
   distances=[];signed=[]
   for j in np.where(c==cid)[0]:
    q,n,_,distance=tree.find_nearest(Vector(p[j]));assert q is not None;distances.append(distance);signed.append((Vector(p[j])-q).dot(n))
   ids=np.where(c==cid)[0];worst=int(ids[int(np.argmin(signed))]);far=int(ids[int(np.argmax(distances))])
   lower=[k for k,j in enumerate(ids) if rest[j,2]<=100]
   out.append({'profile':profile,'step':int(steps[i]),'component':cid,'distance_min_cm':min(distances),'distance_max_cm':max(distances),'signed_min_cm':min(signed),'lower_strap_z_le_100_min_signed_cm':min(signed[k] for k in lower),'minimum_signed_vertex_rest_cm':rest[worst].tolist(),'maximum_gap_vertex_rest_cm':rest[far].tolist(),'negative_vertices_rest_cm':[rest[j].tolist() for j,sgn in zip(ids,signed) if sgn<-.015]})
report={'fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'basis':'independently decoded cooked weights evaluated under actual offline UE bone poses','samples':out,'game_runtime_tested':False}
(V/'suspender-fit-audit.json').write_text(json.dumps(report,indent=2));print('SUSPENDER_FIT',min(x['signed_min_cm'] for x in out),max(x['distance_max_cm'] for x in out))
