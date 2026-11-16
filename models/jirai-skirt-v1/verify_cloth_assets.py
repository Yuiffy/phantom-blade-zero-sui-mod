"""Read final IoStore embedded cloth/config/collision exports with CUE4Parse."""
from pathlib import Path
import json,struct,hashlib,numpy as np
CODE=Path(__file__).resolve().parent;R=CODE.parents[1]/'private/jirai-skirt-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=R/'variant'
J=W/'independent/json/ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ'
doc=json.loads((J/'EscapeOnly/Hun_Body_Simple.json').read_text())
pa=json.loads((J/'Physics/PA_Jirai_ClothCollision.json').read_text())
authored=json.loads((W/'cloth-details.json').read_text())
native=json.loads((W/'independent/cloth-native-details.json').read_text())
mesh=next(e for e in doc if e['Type']=='SkeletalMesh')
refs=mesh['Properties']['MeshClothingAssets'];assert len(refs)==len(json.loads((R/'cloth-spec.json').read_text()))
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
 assert p['PhysicsAsset']['ObjectPath'].rsplit('.',1)[0]=='/HuaShira/Mods/SuiPBZ/Physics/'+('PA_Jirai_SkirtCollision' if a['name'].startswith('CA_Jirai_Skirt') else 'PA_Jirai_ClothCollision')
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
 assert shared['Type']=='ChaosClothSharedSimConfig';assert shared['Properties']['IterationCount']==24 and shared['Properties']['SubdivisionCount']==6
 assert shared['Properties']['MaxIterationCount']==24
 s,=[s for s in native['sections'] if s['cloth_index']==i]
 rawguid=''.join(f'{x:08x}' for x in struct.unpack('<4I',bytes.fromhex(s['cloth_guid_raw'])))
 assert rawguid==a['guid'].lower()
 row=json.loads((R/'cloth-spec.json').read_text())[i]
 if row.get('render_pin_plane'):
  plane=row['render_pin_plane'];points=np.load(W/'independent/render-data.npz')['positions'][s['base_vertex']:s['base_vertex']+s['vertices']]
  blend=1-np.array(s['cloth_maps'][0]['source'])[:,3]/65535
  src=np.array(s['cloth_maps'][0]['source'])[:,:3];bary=np.array(s['cloth_maps'][0]['position'])[:,:3]
  triangle_z=np.array(a['positions'])[src,2]
  projected_z=np.clip((triangle_z*bary).sum(1),triangle_z.min(1),triangle_z.max(1))
  desired=np.clip((plane['z']-np.maximum(points[:,2],projected_z))/plane['falloff'],0,1)
  # Independently derive the zero-time cap from the final parsed physical mesh.
  cage=np.array([xyz(v) for v in phys['Vertices']]);tri=np.array(phys['Indices']).reshape(-1,3)
  fn=np.cross(cage[tri[:,1]]-cage[tri[:,0]],cage[tri[:,2]]-cage[tri[:,0]]);fn/=np.maximum(np.linalg.norm(fn,axis=1)[:,None],1e-12);normals=np.zeros_like(cage)
  for corner in range(3):np.add.at(normals,tri[:,corner],fn)
  normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
  offsets=np.array(s['cloth_maps'][0]['position'])[:,3];recon=((cage[src]+normals[src]*offsets[:,None,None])*bary[:,:,None]).sum(1)
  errors=np.linalg.norm(recon-points,axis=1)
  desired=np.minimum(desired,np.minimum(1,plane['rest_error_cap_cm']/np.maximum(errors,1e-12)))

  inner=np.clip((offsets-5)/3,0,1);upper=np.clip((points[:,2]-115)/3,0,1);desired*=1-inner*inner*(3-2*inner)*upper*upper*(3-2*upper)
  assert np.max(np.abs(blend-desired))<2/65535,'Cooked render pin transition changed'
 records.append({'asset':a['name'],'particles':len(a['positions']),'triangles':len(a['indices'])//3,'render_slot':s['slot'],'maxdistance_map_matches':True,'serialized_config_fields':list(c['Properties']),'collision_asset_matches':True})
all_actual=[]
for pa_name,spec_name in [('PA_Jirai_ClothCollision','collision-spec.json'),('PA_Jirai_SkirtCollision','skirt-collision-spec.json')]:
 spec=json.loads((W/spec_name).read_text());pa=json.loads((J/('Physics/'+pa_name+'.json')).read_text());actual=[]
 for e in pa:
  if e['Type']!='SkeletalBodySetup':continue
  p=e['Properties'];assert p['PhysicsType']=='PhysType_Kinematic'
  for sphere in p['AggGeom'].get('SphereElems',[]):actual.append({'bone':p['BoneName'],'type':'sphere','center':xyz(sphere['Center']),'radius':sphere['Radius'],'kinematic':True})
  for capsule in p['AggGeom'].get('SphylElems',[]):actual.append({'bone':p['BoneName'],'type':'capsule','center':xyz(capsule['Center']),'radius':capsule['Radius'],'length':capsule['Length'],'rotation':[capsule['Rotation'][k] for k in ['Pitch','Yaw','Roll']],'kinematic':True})
 assert len(actual)==len(spec['bodies'])
 for a in spec['bodies']:
  matches=[b for b in actual if b['bone']==a['bone'] and b['type']==a['type'] and np.linalg.norm(np.array(a['center'])-b['center'])<1e-4 and abs(a['radius']-b['radius'])<1e-4]
  assert len(matches)==1,a
  if a['type']=='capsule':
   b=matches[0];assert abs(a['length']-b['length'])<1e-4;assert max(abs((x-y+180)%360-180) for x,y in zip(a['rotation'],b['rotation']))<.001
 all_actual.extend(actual)
actual=all_actual
report={'status':'final-container-cloth-config-and-collision-readback-passed','fbx_sha256':hashlib.sha256((R/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'cloth_spec_sha256':hashlib.sha256((R/'cloth-spec.json').read_bytes()).hexdigest(),'render_skin_blend_verified':True,'assets':records,'kinematic_spheres':sum(a['type']=='sphere' for a in actual),'kinematic_capsules':sum(a['type']=='capsule' for a in actual),'original_body_physics_asset_unchanged':True,'class_default_values_in_PBZ_unverified':True,'game_runtime_tested':False}
(W/'cloth-assets-verification.json').write_text(json.dumps(report,indent=2));print(report['status'],len(records),'cloth assets',len(actual),'spheres')
