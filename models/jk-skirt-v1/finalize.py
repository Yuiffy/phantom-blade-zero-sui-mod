"""Freeze completed final-container evidence, then install with readback rollback."""
from common import *
from datetime import datetime,timezone,timedelta
import argparse
import shutil
import numpy as np

def static_mapping(stage):
 from native import decode
 p,_,_,d=decode(read(W/'native/final.json'));s=d['sections'][14];m=s['cloth_maps'][0];asset=read(W/stage/'cloth-details.json')['assets'][2]
 q=np.array(asset['positions']);tri=np.array(asset['indices']).reshape(-1,3);fn=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);fn/=np.maximum(np.linalg.norm(fn,axis=1)[:,None],1e-12);normals=np.zeros_like(q)
 for j in range(3):np.add.at(normals,tri[:,j],fn)
 normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12);ix=np.array(m['source']);b=np.array(m['position']);bary=np.column_stack([b[:,:2],1-b[:,:2].sum(1)])
 recon=((q[ix[:,:3]]+normals[ix[:,:3]]*b[:,3,None,None])*bary[:,:,None]).sum(1);alpha=1-ix[:,3]/65535
 error=np.linalg.norm(recon-p[s['base_vertex']:s['base_vertex']+s['vertices']],axis=1)*alpha
 report=dict(passed=float(error.max())<=.3,max_error_cm=float(error.max()),basis='actual extracted section/GPU mapping and independently checked authored physical rest guide')
 assert report['passed'];write(W/'static-mapping-verification.json',report)
 return report

def prepare():
 stage=read(W/'chosen-stage.json')['stage'];evaluation=read(W/stage/'evaluation.json')
 assert evaluation['passed'] and len(evaluation['records'])==6
 assert evaluation['document_sha256']==sha(W/'native/final.json')
 for row in evaluation['records']:
  assert row['passed'] and set(map(int,row['simulated_asset_particle_counts']))==set(range(5))
 manifest=read(W/stage/'input-manifest.json');assert not manifest['skirt_only']
 for group in ['inputs','outputs']:
  for p,h in manifest[group].items():assert sha(p)==h,(group,p)
 frozen=W/stage/'frozen-inputs';frozen.mkdir(exist_ok=True);archive=[]
 for p,h in manifest['inputs'].items():
  source=Path(p);target=frozen/source.name
  if target.exists():assert sha(target)==h
  else:shutil.copy2(source,target)
  archive.append(dict(source=p,archived=str(target),sha256=h))
 write(W/stage/'frozen-inputs.json',archive)
 static_mapping(stage)
 report=read(W/'final-verification.json');assert report['passed']
 assert read(W/'final-cloth-readback.json')['passed'] and read(W/'editor-reload-verification.json')['passed']
 contacts=read(W/stage/'contacts.json');baseline=read(W/'baseline/contacts.json')
 comparisons=[]
 for hz in [30,60]:
  name=f'jog-{hz}-surface.npz';a=next(r for r in baseline['records'] if r['file']==name);b=next(r for r in contacts['records'] if r['file']==name)
  assert b['visible_thigh_sum']<a['visible_thigh_sum'] and b['visible_thigh_max']<a['visible_thigh_max']
  comparisons.append(dict(hz=hz,baseline_visible_thigh_crossings=a['visible_thigh_sum'],candidate_visible_thigh_crossings=b['visible_thigh_sum'],basis='sampled visible edge crossings, not exposed area or game animation'))
 review=read(W/'review-decision.json');assert review['passed']
 paths=[W/'final-verification.json',W/'final-cloth-readback.json',W/'editor-reload-verification.json',W/'composition.json',W/'composition-baseline.json',W/'build-report.json',W/'native/final.json',W/'native/latest.json',W/'independent/baseline-body.json',W/'review-decision.json',W/stage/'evaluation.json',W/stage/'input-manifest.json',W/stage/'contacts.json',W/stage/'render-settings.json',W/'skirt-collision-spec.json',W/'static-mapping-verification.json',W/stage/'frozen-inputs.json',Path(read(W/stage/'render-settings.json')['mapping_path'])]
 paths.extend(Path(p) for p in manifest['inputs']);paths.extend(C/name for name in ['native.py','evaluate.py','compose.py','package_verify.py','render_blender.py','finalize.py'])
 for hz in [30,60]:
  p=W/'preview'/f'review-{stage}-{hz}-full.json';data=read(p)
  assert review['image_manifests'][str(p)]==sha(p)
  images=[x for x in data['images'] if Path(x['source_surface']).parent.name==stage]
  assert len(images)==10 and data['offline_only'] and data['script_sha256']==sha(C/'render_blender.py')
  for row in images:
   assert sha(row['image'])==row['image_sha256'] and sha(row['source_surface'])==row['source_sha256']
   paths.append(Path(row['image']));paths.append(Path(row['source_surface']))
  paths.append(p)
 for row in report['container_files']:assert sha(W/'container'/row['name'])==row['sha256']
 assert snapshot()==read(W/'composition-baseline.json')
 gates=dict(passed=True,stage=stage,container_files=report['container_files'],evidence_hashes={str(p):sha(p) for p in paths},running_comparisons=comparisons,game_runtime_tested=False)
 write(W/'delivery-gates.json',gates);print('JK_SKIRT_DELIVERY_GATES_PASSED',flush=True)
 return gates

def install_verified():
 prepare()
 from install import install,rollback
 from package_verify import verify
 install()
 try:verify(True)
 except Exception:
  rollback();receipt=read(W/'installation-receipt.json');receipt['status']='rolled-back-after-independent-readback-failure';write(W/'installation-receipt.json',receipt);raise
 receipt=read(W/'installation-receipt.json');receipt['status']='installed-independent-readback-verified-runtime-pending';write(W/'installation-receipt.json',receipt)
 print('JK_SKIRT_INSTALLED_AND_INDEPENDENTLY_VERIFIED',flush=True)

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args()
 install_verified() if args.install else prepare()
