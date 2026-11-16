"""Early shape gate on actual animated solver particles, before cooking."""
from pathlib import Path
import json,hashlib
import numpy as np
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-shape-v1';V=W/'variant';read=lambda p:json.loads(p.read_text());rows=[]
for profile in read(W/'pose-contract.json')['clips']:
 sim=read(V/('articulation-'+profile+'.json'));assert sim['fbx_sha256']==hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest()
 assert sim['cloth_spec_sha256']==hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),'Stale cloth configuration'
 assert sim['pose_contract_sha256']==hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),'Stale synthetic poses'
 for index,a in enumerate(read(V/'cloth-details.json')['assets']):
  p=np.array(a['positions']);tri=np.array(a['indices']).reshape(-1,3);edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);edges=edges[length>1e-5];length=length[length>1e-5]
  ratios=[]
  for f in sim['frames']:
   q=np.array(next(x['component_positions'] for x in f['assets'] if x['asset_index']==index));assert np.isfinite(q).all();ratios.extend((np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/length).tolist())
  rows.append(dict(profile=profile,asset=a['name'],edge_ratio_min=min(ratios),edge_ratio_max=max(ratios),passed=min(ratios)>.70 and max(ratios)<1.25))
report=dict(passed=all(x['passed'] for x in rows),fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),cloth_spec_sha256=hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),records=rows)
(V/'articulation-shape-gate.json').write_text(json.dumps(report,indent=2));print('ANIMATED_SHAPE',report['passed']);assert report['passed'],[x for x in rows if not x['passed']]
