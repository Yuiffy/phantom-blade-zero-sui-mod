"""Check actual animated particles against cooked rest lengths and skinned limits."""
import json,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-recovery-v1';V=W/'variant'
read=lambda p:json.loads(p.read_text())
doc=read(V/'independent/json/ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple.json')
asset_by_name={e['Name']:e for e in doc if e['Type']=='ClothingAssetCommon'};assets=[asset_by_name[a['name']] for a in read(V/'cloth-details.json')['assets']];bones=read(V/'import-report.json')['actual_reference_bones'];names=[b['name'] for b in bones]
def matrix(t,q):
 m=np.eye(4);m[:3,:3]=Rotation.from_quat(q).as_matrix();m[:3,3]=t;return m
ref=[]
for b in bones:
 a=matrix(b['t'],b['q']);ref.append(ref[b['parent']]@a if b['parent']>=0 else a)
inverse=np.linalg.inv(ref);records=[];passed=True
for profile in read(W/'pose-contract.json')['clips']:
 sim=read(V/('articulation-'+profile+'.json'));assert sim['fbx_sha256']==hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest()
 assert sim['cloth_spec_sha256']==hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),'Stale cloth configuration'
 assert sim['pose_contract_sha256']==hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),'Stale synthetic poses'
 for index,e in enumerate(assets):
  a=e['Properties'];p=a['LodData'][0]['PhysicalMeshData'];rest=np.array([[v[k] for k in ['X','Y','Z']] for v in p['Vertices']]);tri=np.array(p['Indices']).reshape(-1,3)
  edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);length=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1);edges=edges[length>1e-5];length=length[length>1e-5]
  md=np.array(next(m['Value']['Values'] for m in p['WeightMaps'] if m['Key']=='1'));fixed=md==0;uses={}
  for i,weights in enumerate(p['BoneData']):
   for k in range(weights['NumInfluences']):
    suffix=('['+str(k)+']' if k else '');n=a['UsedBoneNames'][weights['BoneIndices'+suffix]];uses.setdefault(names.index(n),[]).append((i,weights['BoneWeights'+suffix]))
  ratios=[];pin=[];over=[]
  for frame in sim['frames']:
   pose=np.array([matrix(b[:3],b[3:]) for b in frame['component_bones']]);trans=pose@inverse;target=np.zeros_like(rest)
   for bi,items in uses.items():
    ix=np.array([i for i,v in items]);wt=np.array([v for i,v in items]);target[ix]+=(rest[ix]@trans[bi,:3,:3].T+trans[bi,:3,3])*wt[:,None]
   q=np.array(next(x['component_positions'] for x in frame['assets'] if x['asset_index']==index));assert np.isfinite(q).all();delta=np.linalg.norm(q-target,axis=1)
   pin.append(float(delta[fixed].max()));over.append(float((delta-md).max()));ratios.extend((np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/length).tolist())
  ok=max(pin)<.03 and max(over)<.15 and min(ratios)>.70 and max(ratios)<1.25;passed=passed and ok
  records.append(dict(profile=profile,asset=e['Name'],passed=ok,pin_error_max_cm=max(pin),maxdistance_overshoot_cm=max(over),edge_ratio_min=min(ratios),edge_ratio_max=max(ratios)))
report=dict(passed=passed,fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),cloth_spec_sha256=hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),pose_contract_sha256=hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),records=records,game_runtime_tested=False)
(V/'articulation-validation.json').write_text(json.dumps(report,indent=2));print('ANIMATED_PARTICLE_STABILITY',passed)
assert passed,[x for x in records if not x['passed']]
