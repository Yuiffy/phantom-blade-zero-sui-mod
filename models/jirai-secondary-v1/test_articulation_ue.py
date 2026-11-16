import unreal,json,hashlib,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';O=W/'variant';E=unreal.EditorAssetLibrary;L=unreal.PBZModToolsLibrary
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
source=unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton');data=json.loads((W/'pose-contract.json').read_text())
names=[b['name'] for b in json.loads((O/'import-report.json').read_text())['actual_reference_bones']]
for profile,clip in data['clips'].items():
 folder='/HuaShira/Mods/SuiPBZ/Tests';name='Synthetic_'+profile.replace('-','_');path=folder+'/'+name
 if E.does_asset_exist(path):E.delete_asset(path)
 factory=unreal.AnimSequenceFactory();factory.set_editor_property('target_skeleton',source)
 seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.AnimSequence,factory);ctrl=seq.controller
 ctrl.open_bracket('Synthetic articulated cloth stress',False);ctrl.set_frame_rate(unreal.FrameRate(clip['fps'],1),False);ctrl.set_number_of_frames(unreal.FrameNumber(len(clip['keys'])-1),False)
 for i,b in enumerate(clip['keys'][0]):
  n=b['name'];ctrl.add_bone_track(n,False);ctrl.set_bone_track_keys(n,[unreal.Vector(*f[i]['t']) for f in clip['keys']],[unreal.Quat(*f[i]['q']) for f in clip['keys']],[unreal.Vector(*f[i]['s']) for f in clip['keys']],False)
 ctrl.close_bracket(False)
 result=L.test_cloth_animation(mesh,seq,181,1/30);assert not result.startswith('ERROR'),result
 out=json.loads(result);out.update(bone_names=names,profile=profile,fbx_sha256=hashlib.sha256((W/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),pose_contract_sha256=hashlib.sha256((W/'pose-contract.json').read_bytes()).hexdigest(),basis='offline Chaos and synthetic animation, not gameplay capture')
 (O/('articulation-'+profile+'.json')).write_text(json.dumps(out))
 ix=names.index('calf_l' if profile!='head-arms' else 'head');a=out['frames'][0]['component_bones'][ix];b=out['frames'][-1]['component_bones'][ix]
 motion=max(math.dist(f['component_bones'][ix][:3],a[:3]) for f in out['frames']);rotation=max(math.dist(f['component_bones'][ix][3:],a[3:]) for f in out['frames'])
 assert motion>1 or rotation>.05,('animation did not evaluate',profile,motion,rotation)
 unreal.log('ARTICULATED_CLOTH_OK '+profile+' bone movement '+str(motion))
