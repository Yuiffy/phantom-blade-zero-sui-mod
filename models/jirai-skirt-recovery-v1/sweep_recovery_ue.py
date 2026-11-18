"""Compare configs in isolated worlds, never save a sweep or install it."""
import unreal,json,hashlib,os,copy
from pathlib import Path
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-recovery-v1';V=W/'variant'
E=unreal.EditorAssetLibrary;L=unreal.PBZModToolsLibrary
assert Path(unreal.Paths.project_dir()).resolve()==(V/'ue/ProjectPBZ').resolve()
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
detail=json.loads(L.dump_cloth_details(mesh));asset=next(a for a in detail['assets'] if a['name'].startswith('CA_Jirai_Skirt'))
BASE=W.parent/'jirai-skirt-v1'
original=next(r['config'] for r in json.loads((BASE/'cloth-spec.json').read_text()) if r['slot']=='MI_Jirai_Skirt')
presets={
 'r7-control':{},
 'drive-only':{'AnimDriveStiffness':{'Low':.14,'High':.14}},
 'balanced':{'GravityScale':1.,'AnimDriveStiffness':{'Low':.14,'High':.14},'BendingStiffnessWeighted':{'Low':.35,'High':.35},'AnimDriveDamping':{'Low':.7,'High':.7},'DampingCoefficient':.15,'LocalDampingCoefficient':.2,'FrictionCoefficient':.05,'LinearVelocityScale':{'X':.35,'Y':.35,'Z':.35},'AngularVelocityScale':.25},
 'firm':{'GravityScale':1.,'AnimDriveStiffness':{'Low':.28,'High':.28},'BendingStiffnessWeighted':{'Low':.55,'High':.55},'AnimDriveDamping':{'Low':.7,'High':.7},'DampingCoefficient':.15,'LocalDampingCoefficient':.2,'FrictionCoefficient':.05,'LinearVelocityScale':{'X':.25,'Y':.25,'Z':.25},'AngularVelocityScale':.2}}
presets['firm-compact']=dict(presets['firm'])
original_collision=json.loads((BASE/'variant/skirt-collision-spec.json').read_text())
pa=unreal.load_asset('/HuaShira/Mods/SuiPBZ/Physics/PA_Jirai_SkirtCollision')
contract=json.loads((W/'pose-contract.json').read_text());out=V/'sweep';out.mkdir(exist_ok=True)
names=[b['name'] for b in json.loads((V/'import-report.json').read_text())['actual_reference_bones']]
sequences={}
for profile,clip in contract['clips'].items():
 if not clip.get('recovery'):continue
 if profile not in os.environ.get('PBZ_SWEEP_PROFILES','walk-recover,jog-recover,crouch-recover').split(','):continue
 folder='/HuaShira/Mods/SuiPBZ/Tests';name='Recovery_'+profile.replace('-','_');path=folder+'/'+name
 if E.does_asset_exist(path):E.delete_asset(path)
 factory=unreal.AnimSequenceFactory();factory.target_skeleton=mesh.skeleton
 seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.AnimSequence,factory);ctrl=seq.controller
 ctrl.open_bracket('Three walk stop rest cycles',False);ctrl.set_frame_rate(unreal.FrameRate(clip['fps'],1),False);ctrl.set_number_of_frames(unreal.FrameNumber(len(clip['keys'])-1),False)
 for i,b in enumerate(clip['keys'][0]):
  n=b['name'];ctrl.add_bone_track(n,False);ctrl.set_bone_track_keys(n,[unreal.Vector(*f[i]['t']) for f in clip['keys']],[unreal.Quat(*f[i]['q']) for f in clip['keys']],[unreal.Vector(*f[i]['s']) for f in clip['keys']],False)
 ctrl.close_bracket(False);sequences[profile]=seq
for preset,updates in presets.items():
 if preset not in os.environ.get('PBZ_SWEEP_PRESETS',','.join(presets)).split(','):continue
 config=dict(original,**updates);assert L.tune_cloth_config(mesh,asset['name'],json.dumps(config))
 collision=copy.deepcopy(original_collision)
 if preset=='firm-compact':
  for b in collision['bodies']:
   if b['type']=='capsule' and b['radius']>10:b['radius']=9.5
 assert L.build_physics_asset(pa,mesh,json.dumps(collision)).startswith('ok')
 collision_text=json.dumps(collision,indent=2)
 (out/(preset+'-collision.json')).write_text(collision_text)
 (out/(preset+'-config.json')).write_text(json.dumps(config,indent=2))
 for profile,seq in sequences.items():
  for hz in map(int,os.environ.get('PBZ_SWEEP_HZ','30,60').split(',')):
   motion=W/f'component-{profile}-{hz}hz.json';steps=60+16*hz+1
   target=out/f'{preset}-{profile}-{hz}hz.json'
   if target.exists():
    previous=json.loads(target.read_text())
    assert previous['config']==config and previous['pose_contract_sha256']==hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest()
    if 'collision_spec_sha256' in previous:assert previous['collision_spec_sha256']==hashlib.sha256(collision_text.encode()).hexdigest()
    assert all(f.get('simulated_teleport_mode')==0 for f in previous['frames']),'Old harness output cannot be reused'
    unreal.log(f'RECOVERY_SWEEP_REUSED_VERIFIED {preset} {profile} {hz}Hz')
    continue
   data=json.loads(L.test_cloth_animation(mesh,seq,steps,1/hz,motion.read_text()))
   data.update(bone_names=names,profile=profile,preset=preset,config=config,collision_spec_sha256=hashlib.sha256(collision_text.encode()).hexdigest(),pose_contract_sha256=hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),component_motion_sha256=hashlib.sha256(motion.read_bytes()).hexdigest())
   target.write_text(json.dumps(data))
   unreal.log(f'RECOVERY_SWEEP_OK {preset} {profile} {hz}Hz')
assert L.tune_cloth_config(mesh,asset['name'],json.dumps(original))
assert L.build_physics_asset(pa,mesh,json.dumps(original_collision)).startswith('ok')
(out/'cloth-details.json').write_text(json.dumps(detail))
unreal.log('RECOVERY_SWEEP_COMPLETE_NOT_SAVED')
