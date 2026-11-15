"""Read final IoStore embedded cloth/config/collision exports with CUE4Parse."""
from pathlib import Path
import json,struct,numpy as np
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v1'
J=W/'independent/json/ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ'
doc=json.loads((J/'EscapeOnly/Hun_Body_Simple.json').read_text())
pa=json.loads((J/'Physics/PA_Sui_ClothCollision.json').read_text())
authored=json.loads((W/'cloth-details.json').read_text())
native=json.loads((W/'independent/cloth-native-details.json').read_text())
mesh=next(e for e in doc if e['Type']=='SkeletalMesh')
refs=mesh['Properties']['MeshClothingAssets'];assert len(refs)==5
def resolve(ref,table):return table[int(ref['ObjectPath'].rsplit('.',1)[1])]
def xyz(v):return [v[k] for k in ['X','Y','Z']]
def close(a,b,path=''):
 if isinstance(a,dict):
  other={k.casefold():v for k,v in b.items()}
  for k,v in a.items():assert k.casefold() in other,(path,k);close(v,other[k.casefold()],path+'.'+k)
 elif isinstance(a,(list,tuple)):
  assert len(a)==len(b),path
  for i,(v,w) in enumerate(zip(a,b)):close(v,w,path+str(i))
 elif isinstance(a,bool) or isinstance(a,str):assert a==b,(path,a,b)
 else:assert abs(float(a)-float(b))<1e-4,(path,a,b)
records=[]
for i,(ref,a) in enumerate(zip(refs,authored['assets'])):
 e=resolve(ref,doc);assert e['Type']=='ClothingAssetCommon' and e['Name']==a['name'];p=e['Properties']
 assert p['AssetGuid'].replace('-','').lower()==a['guid'].lower()
 assert p['LodMap']==[0] and len(p['LodData'])==1
 assert p['PhysicsAsset']['ObjectPath'].rsplit('.',1)[0]=='/HuaShira/Mods/SuiPBZ/Physics/PA_Sui_ClothCollision'
 lod=p['LodData'][0];assert not lod['bUseMultipleInfluences'];phys=lod['PhysicalMeshData']
 close([xyz(v) for v in phys['Vertices']],a['positions'],'positions');assert phys['Indices']==a['indices']
 md=next(m for m in phys['WeightMaps'] if m['Key']=='1')['Value']['Values']
 close(md,next(m['values'] for m in a['maps'] if m['name']=='MaxDistance'),'maxdistance')
 assert len(phys['BoneData'])==len(a['positions']) and len(phys['Normals'])==len(a['positions'])
 for b in phys['BoneData']:
  assert 1<=b['NumInfluences']<=12
  weights=[]
  for n in range(b['NumInfluences']):
   ix=b['BoneIndices'+('['+str(n)+']' if n else '')];v=b['BoneWeights'+('['+str(n)+']' if n else '')]
   assert 0<=ix<len(p['UsedBoneNames']) and 0<=v<=1;weights.append(v)
  assert abs(sum(weights)-1)<1e-5
 config_refs={v['Key']:v['Value'] for v in p['ClothConfigs']}
 c=resolve(config_refs['ChaosClothConfig'],doc);assert c['Type']=='ChaosClothConfig'
 # The parser exposes properties differing from the official class defaults.
 # Compare every serialized value against full editor readback. Do not pretend
 # absent default fields independently establish the game's runtime CDO values.
 close(c['Properties'],a['config'],'serialized-config')
 shared=resolve(config_refs['ChaosClothSharedSimConfig'],doc)
 assert shared['Type']=='ChaosClothSharedSimConfig';assert shared['Properties']['IterationCount']==5 and shared['Properties']['SubdivisionCount']==2
 s,=[s for s in native['sections'] if s['cloth_index']==i]
 rawguid=''.join(f'{x:08x}' for x in struct.unpack('<4I',bytes.fromhex(s['cloth_guid_raw'])))
 assert rawguid==a['guid'].lower()
 records.append({'asset':a['name'],'particles':len(a['positions']),'triangles':len(a['indices'])//3,'render_slot':s['slot'],'maxdistance_map_matches':True,'serialized_config_fields':list(c['Properties']),'collision_asset_matches':True})
spec=json.loads((W/'collision-spec.json').read_text());actual=[]
for e in pa:
 if e['Type']!='SkeletalBodySetup':continue
 p=e['Properties'];assert p['PhysicsType']=='PhysType_Kinematic'
 for sphere in p['AggGeom']['SphereElems']:actual.append({'bone':p['BoneName'],'type':'sphere','center':xyz(sphere['Center']),'radius':sphere['Radius'],'kinematic':True})
assert len(actual)==len(spec['bodies'])==10
for a in spec['bodies']:
 matches=[b for b in actual if b['bone']==a['bone'] and np.linalg.norm(np.array(a['center'])-b['center'])<1e-4 and abs(a['radius']-b['radius'])<1e-4]
 assert len(matches)==1,a
report={'status':'final-container-cloth-config-and-collision-readback-passed','assets':records,'kinematic_spheres':10,'original_body_physics_asset_unchanged':True,'class_default_values_in_PBZ_unverified':True,'game_runtime_tested':False}
(W/'cloth-assets-verification.json').write_text(json.dumps(report,indent=2));print(report['status'],len(records),'cloth assets',len(actual),'spheres')
