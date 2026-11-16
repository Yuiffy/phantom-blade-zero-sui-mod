"""Reconstruct cooked LBS + GPU cloth positions under actual animated Chaos output."""
import json,hashlib,os
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
from scipy.spatial import cKDTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';V=W/'variant';I=V/'independent'
if os.environ.get('PBZ_BASELINE')=='1':
 V=W/'baseline';W=R/'private/jirai-detail-v1';I=W/'variant/independent'
detail=json.loads((I/'cloth-native-details.json').read_text());data=np.load(I/'render-data.npz');rest=data['positions'];weights=json.loads((I/'render-weights.json').read_text());bones=json.loads((V/'import-report.json').read_text())['actual_reference_bones'];names=[b['name'].lower() for b in bones]
def matrix(t,q):
 a=np.eye(4);a[:3,:3]=Rotation.from_quat(q).as_matrix();a[:3,3]=t;return a
ref=[]
for b in bones:
 a=matrix(b['t'],b['q']);ref.append(ref[b['parent']]@a if b['parent']>=0 else a)
ref=np.array(ref);inverse=np.linalg.inv(ref);uses={}
for i,w in enumerate(weights):
 for n,v in w.items():uses.setdefault(names.index(n.lower()),[]).append((i,v))
source=json.loads((W/'source-render-contract.json').read_text());sp=np.array(source['positions_blender_cm']);sp[:,1]*=-1
visible=np.concatenate([np.arange(s['base_vertex'],s['base_vertex']+s['vertices']) for s in detail['sections'] if not s['disabled']]);tree=cKDTree(rest[visible]);dist,nearest=tree.query(sp);nearest=visible[nearest]
if os.environ.get('PBZ_BASELINE')!='1':
 components=np.array(source['components']);assert np.max(dist[(components<2000)&np.array(source.get('used_vertices',[True]*len(components)))])<.001,'Visible source vertices missing from final cooked mesh'
reports=[]
for profile in list(json.loads((R/'private/jirai-skirt-v1/pose-contract.json').read_text())['clips']):
 sim=json.loads((V/('articulation-'+profile+'.json')).read_text());assert sim['bone_names']==[b['name'] for b in bones]
 assert sim['fbx_sha256']==json.loads((V/'source-spec.json').read_text())['fbx_sha256']
 assert sim['pose_contract_sha256']==hashlib.sha256((R/'private/jirai-skirt-v1/pose-contract.json').read_bytes()).hexdigest()
 assert sim['cloth_spec_sha256']==hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest()
 frames=[];sourceframes=[];metrics=[]
 for f in sim['frames']:
  b=np.array(f['component_bones']);pose=np.repeat(np.eye(4)[None],len(b),axis=0);pose[:,:3,:3]=Rotation.from_quat(b[:,3:]).as_matrix();pose[:,:3,3]=b[:,:3];a=pose@inverse;p=np.zeros_like(rest)
  for bi,items in uses.items():
   ix=np.array([x[0] for x in items]);wt=np.array([x[1] for x in items]);p[ix]+=(rest[ix]@a[bi,:3,:3].T+a[bi,:3,3])*wt[:,None]
  for s in detail['sections']:
   if s['cloth_index']<0:continue
   asset=next(x for x in f['assets'] if x['asset_index']==s['cloth_index']);q=np.array(asset['component_positions']);n=np.array(asset['component_normals']);m=s['cloth_maps'][0];idx=np.array(m['source']);bary=np.array(m['position']);alpha=1-idx[:,3]/65535
   bary3=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)]);recon=((q[idx[:,:3]]+n[idx[:,:3]]*bary[:,3,None,None])*bary3[:,:,None]).sum(1);lo=s['base_vertex'];hi=lo+s['vertices'];p[lo:hi]=p[lo:hi]*(1-alpha[:,None])+recon*alpha[:,None]
  assert np.isfinite(p).all();frames.append(p);sf=p[nearest].copy();sf[dist>.001]=sp[dist>.001];sf[:,1]*=-1;sourceframes.append(sf)
  metrics.append({'step':f['step'],'max_component_displacement_cm':float(np.linalg.norm(p-rest,axis=1).max())})
 np.savez_compressed(V/('articulation-'+profile+'-surface.npz'),frames=np.array(frames),source_frames=np.array(sourceframes),steps=[f['step'] for f in sim['frames']])
 reports.append({'profile':profile,'frames':len(frames),'basis':'cooked quantized weights, cooked GPU cloth mapping, actual animated Chaos output','motion':metrics})
stamp={'profiles':reports,'fbx_sha256':hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'cloth_spec_sha256':hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),'pose_contract_sha256':hashlib.sha256((R/'private/jirai-skirt-v1/pose-contract.json').read_bytes()).hexdigest(),'cooked_mapping_sha256':hashlib.sha256((I/'cloth-native-details.json').read_bytes()).hexdigest(),'game_runtime_tested':False}
if os.environ.get('PBZ_BASELINE')!='1':stamp['combined_tests_sha256']=hashlib.sha256((V/'combined-tests.json').read_bytes()).hexdigest()
(V/'articulated-reconstruction.json').write_text(json.dumps(stamp,indent=2));print('ARTICULATED_RENDER_SURFACES_RECONSTRUCTED')
