"""Evaluate original-reference tracks through UE with per-character retarget modes."""
import unreal,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-secondary-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=ROOT/'variant'
contract=json.loads((ROOT/'shoulder-animation-contract.json').read_text());raw=json.loads((PBZ/'research/hun-skeleton.json').read_text(encoding='utf8'));bones=json.loads((PBZ/'research/hun-skeleton-raw.json').read_text())['bones']
export=next(e for e in raw['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');modes=next(d for d in export['Data'] if d['Name']=='BoneTree')['Value']
source=unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton');target_path='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton';EAL=unreal.EditorAssetLibrary
unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
target=unreal.load_asset(target_path);assert isinstance(target,unreal.Skeleton),target_path
changed={n.lower() for n in contract['skeleton_translation_bones']}
mode_by_name={b['name'].lower():m['Value'][0]['Value'] for b,m in zip(bones,modes)}
editor_bones=json.loads((W/'shoulder-rig/editor-bone-order.json').read_text())
for skeleton,is_target in [(source,False),(target,True)]:
 tree=skeleton.get_editor_property('bone_tree');assert len(tree)==len(bones)==len(modes)==1134
 # Read settings that were serialized with UAssetAPI while UE was closed.
 for index,bone in enumerate(editor_bones):
  text='Skeleton' if is_target and bone['name'].lower() in changed else mode_by_name[bone['name'].lower()]
  actual=str(skeleton.get_editor_property('bone_tree')[index].get_editor_property('translation_retargeting_mode')).split('.')[1].split(':')[0].replace('_','').lower()
  assert text.lower()==actual,(bone['name'],text,actual)
 if is_target:
  skeleton.add_compatible_skeleton(source);skeleton.set_editor_property('use_retarget_modes_from_compatible_skeleton',False);assert EAL.save_loaded_asset(skeleton)
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
factory=unreal.AnimSequenceFactory();factory.set_editor_property('target_skeleton',source)
path='/HuaShira/Mods/SuiPBZ/Tests/Shoulder_SourceReference'
if EAL.does_asset_exist(path):EAL.delete_asset(path)
seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset('Shoulder_SourceReference','/HuaShira/Mods/SuiPBZ/Tests',unreal.AnimSequence,factory)
ctrl=seq.controller;ctrl.open_bracket('Original reference shoulder test',False);ctrl.set_frame_rate(unreal.FrameRate(1,1),False);ctrl.set_number_of_frames(unreal.FrameNumber(3),False)
for i,b in enumerate(contract['keys'][0]):
 n=b['name'];ctrl.add_bone_track(n,False)
 ctrl.set_bone_track_keys(n,[unreal.Vector(*f[i]['t']) for f in contract['keys']],[unreal.Quat(*f[i]['q']) for f in contract['keys']],[unreal.Vector(*f[i]['s']) for f in contract['keys']],False)
ctrl.close_bracket(False)
results=[]
for name,skeleton in [('original_modes_control',source),('per_character_corrected_modes',target)]:
 mesh.skeleton=skeleton
 options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh);options.set_editor_property('should_retarget',True)
 for time,frame in enumerate(contract['expected']):
  pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(seq,float(time),options);errors={};positions={}
  for bone,want in frame['bones'].items():
   tr=unreal.AnimPoseExtensions.get_bone_pose(pose,bone,unreal.AnimPoseSpaces.WORLD);v=tr.translation;got=[v.x,v.y,v.z];positions[bone]=got;errors[bone]=math.dist(got,want)
  results.append({'configuration':name,'angle':frame['angle'],'positions_ue_cm':positions,'errors_cm':errors,'max_error_cm':max(errors.values())})
mesh.skeleton=target
# Verify moving marker tracks remain animated after the anatomical corrections.
name='IKMarker_Translation';path='/HuaShira/Mods/SuiPBZ/Tests/'+name
if EAL.does_asset_exist(path):EAL.delete_asset(path)
marker_seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,'/HuaShira/Mods/SuiPBZ/Tests',unreal.AnimSequence,factory)
c=marker_seq.controller;c.open_bracket('Dynamic IK marker test',False);c.set_frame_rate(unreal.FrameRate(1,1),False);c.set_number_of_frames(unreal.FrameNumber(1),False)
marker_names={'ik_hand_gun','ik_hand_l','ik_hand_r','ik_weapon_l','ik_weapon_r'}
for b in contract['keys'][0]:
 n=b['name'];c.add_bone_track(n,False);p=b['t'];end=[p[j]+([3,4,5][j] if n in marker_names else 0) for j in range(3)]
 c.set_bone_track_keys(n,[unreal.Vector(*p),unreal.Vector(*end)],[unreal.Quat(*b['q'])]*2,[unreal.Vector(*b['s'])]*2,False)
c.close_bracket(False)
options=unreal.AnimPoseEvaluationOptions();options.set_editor_property('optional_skeletal_mesh',mesh);options.set_editor_property('should_retarget',True)
marker_results=[]
for n in sorted(marker_names):
 v=[]
 for t in [0.,1.]:
  pose=unreal.AnimPoseExtensions.get_anim_pose_at_time(marker_seq,t,options);a=unreal.AnimPoseExtensions.get_bone_pose(pose,n,unreal.AnimPoseSpaces.LOCAL).translation;v.append([a.x,a.y,a.z])
 delta=[b-a for a,b in zip(*v)];err=math.dist(delta,[3,4,5]);assert err<.01,(n,delta,err);marker_results.append({'bone':n,'animated_translation_delta_cm':delta,'error_cm':err})
(W/'ik-marker-verification.json').write_text(json.dumps({'passed':True,'basis':'real UE retargeted animation evaluation','markers':marker_results,'game_grip_verified':False},indent=2))
assert EAL.save_loaded_asset(mesh,False)
assert mesh.skeleton.get_path_name()==target.get_path_name()
corrected=[r for r in results if r['configuration']=='per_character_corrected_modes'];passed=max(r['max_error_cm'] for r in corrected)<.03
report={'passed':passed,'basis':'real-UE-raw-animation-evaluation-original-reference-tracks','game_animations_tested':False,'game_runtime_tested':False,'fbx_sha256':contract['fbx_sha256'],'target_skeleton':target_path,'skeleton_translation_bones':sorted(changed),'results':results}
(W/'shoulder-retarget-verification.json').write_text(json.dumps(report,indent=2));assert passed,report
unreal.log('SHOULDER_RETARGET_UE_OK')
