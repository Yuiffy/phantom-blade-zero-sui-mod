"""Predeclared hem/recovery gates on the actual GPU-mapped visible skirt.

This geometry revision accepts only its own independently read final mapping.
The previously declared Recovery1 vertex membership and all gates are preserved.
"""
import json,hashlib,sys
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation

C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';V=W/'variant';O=V/'sweep'
B=R/'private/jirai-skirt-v1/variant';final='--final' in sys.argv
blend_cap=float(sys.argv[sys.argv.index('--blend-cap')+1]) if '--blend-cap' in sys.argv else 1.
assert 0<blend_cap<=1 and (not final or blend_cap==1),'Final evaluation must use only actual cooked mapping'
I=(V if final else B)/'independent'
if final:O=V/'recovery';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert final, 'Changed geometry requires freshly solved and independently mapped final evaluation'
read=lambda p:json.loads(p.read_text())
detail=read(I/'cloth-native-details.json');rest=np.load(I/'render-data.npz')['positions'];weights=read(I/'render-weights.json');bones=read(V/'import-report.json')['actual_reference_bones'];names=[b['name'].lower() for b in bones]
section=next(s for s in detail['sections'] if s['slot']=='MI_Jirai_Skirt');lo=section['base_vertex'];hi=lo+section['vertices'];p0=rest[lo:hi]
# Lower visible skirt including lace. Upper waist cannot dilute hem statistics.
previous=R/'private/jirai-skirt-recovery-v1/variant/independent'
previous_section=next(s for s in read(previous/'cloth-native-details.json')['sections'] if s['slot']=='MI_Jirai_Skirt')
assert previous_section['base_vertex']==lo and previous_section['vertices']==hi-lo
previous_rest=np.load(previous/'render-data.npz')['positions'][lo:hi]
# Preserve the previously declared vertex set when the lower edge moves down;
# do not silently exclude moved vertices by applying the old Z band anew.
hem=(previous_rest[:,2]<116)&(previous_rest[:,2]>100)&(np.linalg.norm(previous_rest[:,:2]-[0,-5],axis=1)>18)
assert hem.sum()>100
ref=[]
for b in bones:
 a=np.eye(4);a[:3,:3]=Rotation.from_quat(b['q']).as_matrix();a[:3,3]=b['t'];ref.append(ref[b['parent']]@a if b['parent']>=0 else a)
inverse=np.linalg.inv(ref);uses={}
for i,w in enumerate(weights[lo:hi]):
 for n,v in w.items():uses.setdefault(names.index(n.lower()),[]).append((i,v))
mapping=section['cloth_maps'][0];idx=np.array(mapping['source']);bary=np.array(mapping['position']);alpha=1-idx[:,3]/65535;bary3=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)])
if not final:alpha=1-np.rint(65535*(1-np.minimum(alpha,blend_cap)))/65535
limits={'quiet_p95_up_cm':1.5,'quiet_max_up_cm':3.,'quiet_p95_drift_cm':3.,'quiet_p95_speed_cm_s':1.,'walk_peak_p95_up_cm':6.,'recovery_deadline_seconds':2.}
records=[]
paths=[V/f'articulation-{profile}{suffix}.json' for profile in ['walk-recover','jog-recover','crouch-recover'] for suffix in ['', '-60hz']] if final else sorted(O.glob('*-recover-*hz.json'))
if '--preset' in sys.argv:
 wanted=sys.argv[sys.argv.index('--preset')+1];paths=[p for p in paths if p.name.startswith(wanted+'-')]
for path in paths:
 sim=read(path);assert sim['pose_contract_sha256']==sha(W/'pose-contract.json')
 if final:
  assert sim['cloth_spec_sha256']==sha(W/'cloth-spec.json') and sim['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx')
  sim['preset']=read(W/'selection.json')['preset']
 assert all(f.get('simulated_teleport_mode')==0 for f in sim['frames']),'Persistent resets invalidate continuous test'
 frames=[];times=[];ratios=[]
 asset=read(V/'cloth-details.json')['assets'][section['cloth_index']];cage=np.array(asset['positions']);tri=np.array(asset['indices']).reshape(-1,3)
 edges=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0);length=np.linalg.norm(cage[edges[:,0]]-cage[edges[:,1]],axis=1);edges=edges[length>1e-5];length=length[length>1e-5]
 for f in sim['frames']:
  b=np.array(f['component_bones']);pose=np.repeat(np.eye(4)[None],len(b),axis=0);pose[:,:3,:3]=Rotation.from_quat(b[:,3:]).as_matrix();pose[:,:3,3]=b[:,:3];a=pose@inverse;p=np.zeros_like(p0)
  for bi,items in uses.items():
   ix=np.array([i for i,v in items]);wt=np.array([v for i,v in items]);p[ix]+=(p0[ix]@a[bi,:3,:3].T+a[bi,:3,3])*wt[:,None]
  s=next(x for x in f['assets'] if x['asset_index']==section['cloth_index']);q=np.array(s['component_positions']);n=np.array(s['component_normals'])
  recon=((q[idx[:,:3]]+n[idx[:,:3]]*bary[:,3,None,None])*bary3[:,:,None]).sum(1)
  p=p*(1-alpha[:,None])+recon*alpha[:,None]
  frames.append(p);times.append((f['step']-60)*sim['dt']);ratios.extend((np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/length).tolist())
 frames=np.array(frames);times=np.array(times);assert np.isfinite(frames).all()
 neutral=frames[np.argmin(abs(times))];dz=frames[:,hem,2]-neutral[hem,2];drift=np.linalg.norm(frames[:,hem]-neutral[hem],axis=2)
 up95=np.percentile(dz,95,axis=1);upmax=dz.max(1);drift95=np.percentile(drift,95,axis=1);speed=np.zeros(len(times));speed[1:]=np.percentile(np.linalg.norm(np.diff(frames[:,hem],axis=0),axis=2),95,axis=1)/np.diff(times)
 cycles=[]
 for stop in [3,8,13]:
  quiet=(times>=stop+2.5)&(times<=stop+3+.001)
  assert quiet.sum()>=2
  recovered=(up95<=limits['quiet_p95_up_cm'])&(upmax<=limits['quiet_max_up_cm'])&(drift95<=limits['quiet_p95_drift_cm'])
  settled=None
  for ix in np.where((times>=stop)&(times<=stop+3+.001))[0]:
   tail=(times>=times[ix])&(times<=stop+3+.001)
   if recovered[tail].all():settled=max(0.,float(times[ix]-stop));break
  row={'stop_time':stop,'quiet_p95_up_cm':float(up95[quiet].max()),'quiet_max_up_cm':float(upmax[quiet].max()),'quiet_p95_drift_cm':float(drift95[quiet].max()),'quiet_p95_speed_cm_s':float(speed[quiet].max()),'recovery_seconds':settled}
  row['passed']=all(row[k]<=limits[k] for k in ['quiet_p95_up_cm','quiet_max_up_cm','quiet_p95_drift_cm','quiet_p95_speed_cm_s']) and settled is not None and settled<=limits['recovery_deadline_seconds'];cycles.append(row)
 peak=float(up95[times>=0].max());shape=min(ratios)>.70 and max(ratios)<1.25
 passed=all(x['passed'] for x in cycles) and shape and (sim['profile']!='walk-recover' or peak<=limits['walk_peak_p95_up_cm'])
 records.append({'file':path.name,'preset':sim['preset'],'profile':sim['profile'],'hz':round(1/sim['dt']),'passed':passed,'peak_p95_up_cm':peak,'initial_settled_hem_p95_displacement_from_reference_cm':float(np.percentile(np.linalg.norm(neutral[hem]-p0[hem],axis=1),95)),'initial_settled_hem_z_percentiles':np.percentile(neutral[hem,2],[5,50,95]).tolist(),'reference_hem_z_percentiles':np.percentile(p0[hem,2],[5,50,95]).tolist(),'edge_ratio_min':min(ratios),'edge_ratio_max':max(ratios),'cycles':cycles,'input_sha256':sha(path)})
 np.savez_compressed(O/(path.stem+'-hem.npz'),positions=frames,times=times,hem=hem,neutral=neutral)
report={'basis':'actual Chaos output reconstructed through unchanged R7 final GPU cloth mapping; synthetic animations only','hem_sample_basis':'same vertex membership as Recovery1, before the geometry edit','limits':limits,'mapping_sha256':sha(I/'cloth-native-details.json'),'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'records':records,'game_runtime_tested':False}
report['predicted_quantized_render_blend_cap']=None if final else blend_cap
report['passed']=len(records)==6 and all(r['passed'] for r in records)
if final:
 report.update(basis='actual continuous Chaos output reconstructed through this candidate final GPU cloth mapping; synthetic animations only',cloth_spec_sha256=sha(W/'cloth-spec.json'),pose_contract_sha256=sha(W/'pose-contract.json'),combined_tests_sha256=sha(V/'combined-tests.json'))
 (V/'recovery-validation.json').write_text(json.dumps(report,indent=2))
(O/'recovery-evaluation.json').write_text(json.dumps(report,indent=2))
for preset in sorted({r['preset'] for r in records}):
 rows=[r for r in records if r['preset']==preset]
 print(preset,'PASS' if len(rows)==6 and all(r['passed'] for r in rows) else 'FAIL',[(r['profile'],r['hz'],round(r['peak_p95_up_cm'],2),round(max(x['quiet_p95_up_cm'] for x in r['cycles']),2)) for r in rows])
if final:assert report['passed'],'Final cooked recovery gate failed'
