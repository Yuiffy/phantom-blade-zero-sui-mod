"""Inspect the isolated editor skeleton's reflected retarget controls."""
import unreal,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-v1'
s=unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton')
r={'skeleton_class':str(type(s)),'methods':[x for x in dir(s) if any(t in x.lower() for t in ['retarget','compatib','bone'])]}
for name in ['bone_tree','compatible_skeletons','use_retarget_modes_from_compatible_skeleton','b_use_retarget_modes_from_compatible_skeleton']:
 try:
  v=s.get_editor_property(name);r[name]=str(v)[:1400]
  if name=='bone_tree':r['bone_node_methods']=dir(v[0])
 except Exception as e:r[name]=str(e)
(ROOT/'variant/retarget-probe.json').write_text(json.dumps(r,indent=2))
EAL=unreal.EditorAssetLibrary
target_path='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton'
target=unreal.load_asset(target_path) if EAL.does_asset_exist(target_path) else EAL.duplicate_asset(s.get_path_name().split('.')[0],target_path)
tree=target.get_editor_property('bone_tree');r['bone_tree_count']=len(tree)
try:
 r['first_mode']=str(tree[0].get_editor_property('translation_retargeting_mode'))
 r['mode_enum']=str(type(tree[0].get_editor_property('translation_retargeting_mode')))
 r['first_node_export']=tree[0].export_text()
except Exception as e:r['mode_error']=str(e)
r['anim_pose_options']=str(unreal.AnimPoseEvaluationOptions.__doc__)
r['factory_doc']=str(unreal.AnimSequenceFactory.__doc__)
r['controller_methods']=[x for x in dir(unreal.AnimDataController) if any(t in x for t in ['bone','frame','model','bracket'])]
(ROOT/'variant/retarget-probe.json').write_text(json.dumps(r,indent=2))
unreal.log('RETARGET_PROBE_OK')
