import unreal,json,hashlib,math,os
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-recovery-v1';O=W/('baseline' if os.environ.get('PBZ_BASELINE')=='1' else 'variant');E=unreal.EditorAssetLibrary;L=unreal.PBZModToolsLibrary
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
source=unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton');data=json.loads((W/'pose-contract.json').read_text())
names=[b['name'] for b in json.loads((O/'import-report.json').read_text())['actual_reference_bones']]
for profile,clip in data['clips'].items():
 if clip.get('recovery') and os.environ.get('PBZ_REUSE_RECOVERY_SWEEP')=='1':
  selection=json.loads((W/'selection.json').read_text());config=next(r['config'] for r in json.loads((W/'cloth-spec.json').read_text()) if r['slot']=='MI_Jirai_Skirt')
  for hz in [30,60]:
   p=O/'sweep'/f"{selection['preset']}-{profile}-{hz}hz.json";out=json.loads(p.read_text())
   assert out['config']==config and out['bone_names']==names
   # Sweep hashes its JSON text before Windows newline translation. Validate
   # that normalized UTF-8 text, and retain byte hashes in the final manifest.
   assert out['collision_spec_sha256']==hashlib.sha256((O/'skirt-collision-spec.json').read_text().encode()).hexdigest()
   assert out['pose_contract_sha256']==hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest()
   motion=W/f'component-{profile}-{hz}hz.json';assert out['component_motion_sha256']==hashlib.sha256(motion.read_bytes()).hexdigest()
   assert all(f.get('simulated_teleport_mode')==0 for f in out['frames'])
   out.update(fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),cloth_spec_sha256=hashlib.sha256((W/'cloth-spec.json').read_bytes()).hexdigest(),reused_sweep={'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'basis':'same unchanged mesh, helper DLL, pose/component inputs, collision and hair configs; selected skirt config read back before save'})
   (O/('articulation-'+profile+('' if hz==30 else '-60hz')+'.json')).write_text(json.dumps(out))
  unreal.log('ARTICULATED_RECOVERY_REUSED '+profile)
  continue
 folder='/HuaShira/Mods/SuiPBZ/Tests';name='Synthetic_'+profile.replace('-','_');path=folder+'/'+name
 if E.does_asset_exist(path):E.delete_asset(path)
 factory=unreal.AnimSequenceFactory();factory.set_editor_property('target_skeleton',source)
 seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.AnimSequence,factory);ctrl=seq.controller
 ctrl.open_bracket('Synthetic articulated cloth stress',False);ctrl.set_frame_rate(unreal.FrameRate(clip['fps'],1),False);ctrl.set_number_of_frames(unreal.FrameNumber(len(clip['keys'])-1),False)
 for i,b in enumerate(clip['keys'][0]):
  n=b['name'];ctrl.add_bone_track(n,False);ctrl.set_bone_track_keys(n,[unreal.Vector(*f[i]['t']) for f in clip['keys']],[unreal.Quat(*f[i]['q']) for f in clip['keys']],[unreal.Vector(*f[i]['s']) for f in clip['keys']],False)
 ctrl.close_bracket(False)
 recovery=clip.get('recovery',False)
 motion=(W/f'component-{profile}-30hz.json').read_text() if recovery else ''
 result=L.test_cloth_animation(mesh,seq,clip.get('steps',181),1/30,motion);assert not result.startswith('ERROR'),result
 out=json.loads(result);out.update(bone_names=names,profile=profile,fbx_sha256=hashlib.sha256(((R/'private/jirai-detail-v1' if os.environ.get('PBZ_BASELINE')=='1' else W)/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),pose_contract_sha256=hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),cloth_spec_sha256=hashlib.sha256(((R/'private/jirai-detail-v1' if os.environ.get('PBZ_BASELINE')=='1' else W)/'cloth-spec.json').read_bytes()).hexdigest(),basis='offline Chaos and synthetic animation, not gameplay capture')
 (O/('articulation-'+profile+'.json')).write_text(json.dumps(out))
 if recovery:
  motion60=W/f'component-{profile}-60hz.json'
  extra=json.loads(L.test_cloth_animation(mesh,seq,1021,1/60,motion60.read_text()))
  extra.update({k:v for k,v in out.items() if k not in ['frames','dt','simulation_instances','motion_profile']})
  extra['component_motion_sha256']=hashlib.sha256(motion60.read_bytes()).hexdigest()
  (O/('articulation-'+profile+'-60hz.json')).write_text(json.dumps(extra))
 ix=names.index('calf_l' if profile!='head-arms' else 'head');a=out['frames'][0]['component_bones'][ix];b=out['frames'][-1]['component_bones'][ix]
 motion=max(math.dist(f['component_bones'][ix][:3],a[:3]) for f in out['frames']);rotation=max(math.dist(f['component_bones'][ix][3:],a[3:]) for f in out['frames'])
 assert motion>1 or rotation>.05,('animation did not evaluate',profile,motion,rotation)
 unreal.log('ARTICULATED_CLOTH_OK '+profile+' bone movement '+str(motion))
