"""Check actual Chaos output against its authored cages and maximum distances."""
from pathlib import Path
import json,numpy as np
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v1'
d=json.loads((W/'cloth-details.json').read_text());out=[]
assert all(s.get('rest_mapping_max_error_cm',0)<.3 for s in d['sections'])
for test in ['60hz','30hz']:
 sim=json.loads((W/('simulation-'+test+'.json')).read_text())
 assert sim['simulation_instances']>0
 summaries=[]
 for index,a in enumerate(d['assets']):
  rest=np.array(a['positions']);tri=np.array(a['indices']).reshape(-1,3)
  maps={m['name']:m['values'] for m in a['maps']};maxdist=np.array(maps['MaxDistance']);fixed=maxdist==0
  edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
  l0=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);edges=edges[l0>1e-5];l0=l0[l0>1e-5]
  pts=[]
  for f in sim['frames']:
   q=next(x for x in f['assets'] if x['asset_index']==index)
   p=np.array(q['component_positions']);assert p.shape==rest.shape and np.isfinite(p).all(),(test,a['name'])
   pts.append(p)
  pts=np.array(pts);delta=np.linalg.norm(pts-rest,axis=2)
  ratios=np.linalg.norm(pts[:,edges[:,0]]-pts[:,edges[:,1]],axis=2)/l0
  # Physical max-distance spheres apply to the simulation particles. This does
  # not by itself bound the offset of every mapped high-resolution render point.
  pin=float(delta[:,fixed].max());overshoot=float((delta-maxdist).max())
  assert pin<.03,(a['name'],'pin',pin)
  assert overshoot<.15,(a['name'],'maxdistance',overshoot)
  assert ratios.max()<1.25 and ratios.min()>.70,(a['name'],'shape',ratios.min(),ratios.max())
  settled=min(6,len(pts)-1);motion=float(np.linalg.norm(pts[settled:]-pts[settled],axis=2).max())
  assert motion>.001,(a['name'],'simulation did not move')
  summaries.append({'asset':a['name'],'particles':len(rest),'fixed':int(fixed.sum()),'max_displacement_cm':float(delta.max()),'maxdistance_overshoot_cm':overshoot,'max_pin_error_cm':pin,'edge_ratio_min':float(ratios.min()),'edge_ratio_max':float(ratios.max()),'motion_after_warmup_cm':motion})
 out.append({'test':test,'frames':len(sim['frames']),'assets':summaries})
(W/'simulation-validation.json').write_text(json.dumps({'status':'offline-Chaos-component-transform-test-only','tests':out,'game_animations_tested':False,'game_runtime_tested':False},indent=2));print(json.dumps(out,indent=2))
