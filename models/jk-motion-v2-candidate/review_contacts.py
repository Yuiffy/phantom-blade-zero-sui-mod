"""Measure charm/cardigan overlap on reconstructed solver surfaces at reference pose."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');co=np.array([v.co[:] for v in o.data.vertices]);comp=np.array([d.value for d in o.data.attributes['source_component'].data]);faces=np.array([p.vertices[:] for p in o.data.polygons]);mi=np.array([p.material_index for p in o.data.polygons])
jacketfaces=faces[(comp[faces[:,0]]==0)&np.isin(mi,[12,13])];bvh=BVHTree.FromPolygons([Vector(p) for p in co],jacketfaces.tolist())
def measure(points):
 gaps=[]
 for p in points:
  loc,_,_,_=bvh.ray_cast(Vector((float(p[0]),-100,float(p[2]))),Vector((0,1,0)),200)
  if loc is not None:gaps.append(float(loc.y-p[1]))
 return {'sampled_vertices':len(gaps),'min_front_clearance_cm':float(min(gaps)),'vertices_behind_jacket_front':int(np.sum(np.array(gaps)<-.03)),'clearance_p01_cm':float(np.quantile(gaps,.01))}
old=json.loads((R.with_name('tripo-motion-v1')/'source-render-contract.json').read_text());baseline=np.array(old['positions_blender_cm']);report={'basis':'actual-Chaos-output-cooked-GPU-mappings-reference-pose-only','before_rest_charm':measure(baseline[comp==101]),'after_rest_charm':measure(co[comp==101]),'game_animation_collision_unverified':True,'tests':[]}
native=json.loads((W/'independent/cloth-native-details.json').read_text());render=np.load(W/'independent/render-data.npz');rest=render['positions'];section=next(s for s in native['sections'] if s['slot']=='MI_JK_CharmAtlas');mapping=section['cloth_maps'][0];source=np.array(mapping['source']);bary=np.array(mapping['position']);b=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)]);alpha=1-source[:,3]/65535;lo=section['base_vertex'];hi=lo+section['vertices']
for test in ['60hz','30hz','foreaft']:
 sim=json.loads((W/('simulation-'+test+'.json')).read_text());metrics=[]
 for frame in sim['frames']:
  asset=next(a for a in frame['assets'] if a['asset_index']==section['cloth_index']);q=np.array(asset['component_positions']);n=np.array(asset['component_normals'])
  p=((q[source[:,:3]]+n[source[:,:3]]*bary[:,3,None,None])*b[:,:,None]).sum(1);p=rest[lo:hi]*(1-alpha[:,None])+p*alpha[:,None];p[:,1]*=-1
  metrics.append({'step':frame['step'],**measure(p)})
 report['tests'].append({'test':test,'min_front_clearance_cm':min(m['min_front_clearance_cm'] for m in metrics),'max_vertices_behind_jacket_front':max(m['vertices_behind_jacket_front'] for m in metrics),'frames':metrics})
# No claim about body poses not represented here. Fail rather than hide a
# broken experimental collision setup in the tested component motion cases.
assert all(t['min_front_clearance_cm']>-.10 for t in report['tests']),report
(W/'charm-contact-review.json').write_text(json.dumps(report,indent=2));print('CHARM_CONTACT_REVIEW_OK',json.dumps({k:v for k,v in report.items() if k!='tests'}),flush=True)
