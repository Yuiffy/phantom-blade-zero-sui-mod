"""Whitelist pack, independent readback, exact preservation of concurrent work."""
from common import *
from native import decode,unpack
from compose import extract,tojson,REFERENCE_PACKAGES
from read_cooked_model import import_path
from evaluate import render_settings,target_positions
import numpy as np
import shutil
def cue(label,dirs,include_pa=True):
 out=W/'independent'/label;out.mkdir(parents=True,exist_ok=True)
 env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(d) for d in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
 packages=[BODY,PA] if include_pa else [BODY]
 text=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',out,'json',*[relative_package(p) for p in packages]],env)
 assert not any(s in text for s in ['Failed to','Exception','[WRN]','[ERR]']),text[-2000:]
 return {p:read(out/(relative_package(p)+'.json')) for p in packages}

def validate_independent(data):
 stage=read(W/'chosen-stage.json')['stage'];settings=render_settings(stage);auth=read(W/stage/'cloth-details.json')['assets'][2]
 body=data[BODY];asset=next(x['Properties'] for x in body if x['Name']=='CA_Sui_Skirt_0');physical=asset['LodData'][0]['PhysicalMeshData']
 assert asset['PhysicsAsset']['ObjectPath'].split('.')[0]==PA
 assert np.allclose([[v[k] for k in ['X','Y','Z']] for v in physical['Vertices']],auth['positions'],atol=1e-5,rtol=0)
 assert physical['Indices']==auth['indices']
 values=next(x['Value']['Values'] for x in physical['WeightMaps'] if x['Key']=='1');expect=next(x['values'] for x in auth['maps'] if x['name']=='MaxDistance')
 assert np.allclose(values,expect,atol=1e-5,rtol=0)
 drive=next(x['Value']['Values'] for x in physical['WeightMaps'] if x['Key']=='4');assert len(drive)==len(auth['positions']) and all(v==1 for v in drive)
 pelvis=asset['UsedBoneNames'].index('pelvis')
 assert all(x['NumInfluences']==1 and x['BoneIndices']==pelvis and x['BoneWeights']==1 for x in physical['BoneData'])
 config=next(x['Properties'] for x in body if x['Type']=='ChaosClothConfig' and ':CA_Sui_Skirt_0' in x['Outer']['ObjectName'])
 def match(actual,expected):
  if isinstance(expected,dict):
   for k,v in expected.items():match(actual[k],v)
  elif isinstance(expected,bool):assert actual is expected
  else:assert abs(actual-expected)<1e-5,(actual,expected)
 for k,v in settings['config'].items():
  # Engine omits default-valued tagged properties. False defaults are verified by exact composed-export readback.
  if k in config:match(config[k],v)
  else:assert v is False,(k,v)
 shared=next(x['Properties'] for x in body if x['Type']=='ChaosClothSharedSimConfig')
 assert shared['IterationCount']==settings['iterations'] and shared['SubdivisionCount']==settings['substeps']
 bodies=[x for x in data[PA] if x['Type']=='SkeletalBodySetup'];assert len(bodies)==3
 assert sorted(x['Properties']['BoneName'] for x in bodies)==['pelvis','thigh_l','thigh_r']
 spec=read(W/'skirt-collision-spec.json')['bodies']
 for body in bodies:
  p=body['Properties'];s=next(x for x in spec if x['bone']==p['BoneName']);assert p['PhysicsType']=='PhysType_Kinematic'
  element=p['AggGeom']['SphereElems' if s['type']=='sphere' else 'SphylElems'];assert len(element)==1;v=element[0]
  assert abs(v['Radius']-s['radius'])<1e-5 and np.allclose([v['Center'][k] for k in ['X','Y','Z']],s['center'],atol=1e-4,rtol=0)
  if s['type']=='capsule':
   assert abs(v['Length']-s['length'])<1e-4
   angles=np.array([v['Rotation'][k] for k in ['Pitch','Yaw','Roll']])-s['rotation'];assert np.max(abs((angles+180)%360-180))<1e-3
 return dict(passed=True,physical_vertices=len(physical['Vertices']),physical_weights_pelvis_only=True,max_distance_cm=max(values),collision_bodies=len(bodies),solver=shared)
def package():
 assert snapshot()==read(W/'composition-baseline.json'),'New face work arrived; compose again before packing'
 container=W/'container';container.mkdir(exist_ok=True)
 run('pack',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',W/'legacy',container/(NAME+'.utoc')])
 listing=run('list',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
 paths={line.split()[-1].replace('\\','/').removeprefix('../../../') for line in listing.splitlines() if line.strip().endswith('.uasset')}
 assert paths=={relative_package(p)+'.uasset' for p in [BODY,PA]}
 write(W/'build-report.json',dict(passed=True,packages=[BODY,PA],files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())]))
 print('JK_SKIRT_PACKAGED_TWO_SCOPED_ASSETS',flush=True)
def verify(installed=False):
 label='installed' if installed else 'final';dirs=[MODS] if installed else [MODS,W/'container'];root=extract(label,dirs)
 # Decode the exact candidate with complete verification-only dependencies;
 # prove effective patch selection separately in the actual CUE mount context.
 target=W/(label+'-target-triple');target.mkdir(exist_ok=True)
 for row in read(W/'build-report.json')['files']:
  src=(MODS if installed else W/'container')/row['name'];assert sha(src)==row['sha256'];shutil.copy2(src,target/src.name)
 target_root=extract(label+'-target',[target,W/'dependency-context']);body=target_root/(relative_package(BODY)+'.uasset');doc=tojson(label,body);expect=tojson('composed',W/'legacy'/(relative_package(BODY)+'.uasset'));source=read(W/'native/latest.json')
 assert doc['Imports']==expect['Imports'] and doc['NameMap']==expect['NameMap']
 assert not any('Unknown' in x['ObjectName'] for x in doc['Imports'])
 assert sha(body.with_suffix('.uexp'))==sha((W/'legacy'/(relative_package(BODY)+'.uexp')))
 baseline_path=W/'independent/baseline-body.json'
 if not installed:write(baseline_path,cue('baseline-body',[MODS],False)[BODY])
 baseline=read(baseline_path);got=cue(label,dirs)
 old_mesh=next(x for x in baseline if x['Type']=='SkeletalMesh');new_mesh=next(x for x in got[BODY] if x['Type']=='SkeletalMesh')
 assert old_mesh['Properties']==new_mesh['Properties'] and old_mesh['SkeletalMaterials']==new_mesh['SkeletalMaterials'],'Body dependencies or latest face material changed'
 for old_export in baseline:
  if old_export['Type']=='ClothingAssetCommon' and old_export['Name']!='CA_Sui_Skirt_0':
   assert old_export==next(x for x in got[BODY] if x['Name']==old_export['Name'])
 write(W/'native'/(label+'-materials.json'),new_mesh['SkeletalMaterials'])
 actual=decode(doc);old=decode(source)
 target=target_positions(source,render_settings(read(W/'chosen-stage.json')['stage']))
 assert np.array_equal(actual[0],target) and actual[1]==old[1] and np.array_equal(actual[2],old[2]),'Face/geometry/skin/indices changed outside the chosen skirt shape'
 a=unpack(doc);b=unpack(source);allow=set();section=old[3]['sections'][14]
 start=old[3]['position_span']['offset']+12*section['base_vertex'];allow.update(range(start,start+12*section['vertices']))
 for i in range(section['vertices']):
  for start in [section['cloth_map_spans'][0]['offset']+64*i,old[3]['gpu_cloth_mapping_span']['offset']+64*(section['gpu_mapping_offset']+i)]:allow.update(range(start,start+64))
 changes={i for i,(x,y) in enumerate(zip(a,b)) if x!=y};assert len(a)==len(b) and changes and changes<=allow
 composition=read(W/'composition.json');wanted=set(composition['wanted_exports'])
 for i,(original,result) in enumerate(zip(source['Exports'],doc['Exports'])):
  assert result['Data']==expect['Exports'][i]['Data']
  if i not in wanted:
   assert original['Data']==result['Data']
   if original['ObjectName']!='Hun_Body_Simple':assert original['Extras']==result['Extras']
 skirt=next(e for e in doc['Exports'] if e['ObjectName']=='CA_Sui_Skirt_0');ref=next(p['Value'] for p in skirt['Data'] if p['Name']=='PhysicsAsset');assert import_path(doc,ref)==PA+'.'+PA.rsplit('/',1)[1]
 preserved=[]
 latest=W/'latest-legacy'
 for p in latest.rglob('*.uasset'):
  rel=p.relative_to(latest)
  if rel.as_posix()==relative_package(BODY)+'.uasset' or rel.as_posix() in REFERENCE_PACKAGES:continue
  for ext in ['.uexp','.ubulk','.uptnl']:
   before=p.with_suffix(ext);after=(root/rel).with_suffix(ext);assert before.exists()==after.exists(),str(rel)
   if before.exists():assert sha(before)==sha(after),str(rel)
  preserved.append(rel.as_posix())
 assert len(preserved)>=100
 independent=validate_independent(got);write(W/(label+'-cloth-readback.json'),independent)
 if not installed:assert cue('reverse-order',[W/'container',MODS])==got
 write(W/(label+'-verification.json'),dict(passed=True,latest_face_geometry_normals_uv_weights_and_indices_exact=True,all_native_bytes_outside_skirt_positions_and_mappings_exact=True,all_other_clothing_exports_exact=True,gameplay_physics_exact=True,cloth_guid_and_binding_identity_exact=True,preserved_packages=len(preserved),packages=[BODY,PA],container_files=read(W/'build-report.json')['files'],native_changed_bytes=len(changes),independent_cue_readback=True,game_runtime_tested=False))
 np.savez_compressed(W/'final-render.npz',positions=actual[0],indices=actual[2]);write(W/'final-sections.json',actual[3])
 print('JK_SKIRT_VERIFIED',label,len(preserved),flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['installed']:verify(True)
 else:package();verify()
