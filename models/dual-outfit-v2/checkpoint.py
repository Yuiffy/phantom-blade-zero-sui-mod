"""Export the user-approved local baseline, without original game assets or keys."""
import json,hashlib,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/dual-outfit-v2';S=R/'private/jirai-proportion-v1';E=R/'evidence/jirai-r5-dual-v2';M=R/'models/jirai-r5-checkpoint'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
def scrub(x):
 if isinstance(x,dict):return {k:scrub(v) for k,v in x.items()}
 if isinstance(x,list):return [scrub(v) for v in x]
 if isinstance(x,str):
  x=x.replace('\\','/')
  for root in ['D:/workspace/myrepo/phantom-blade-zero-sui-mod','D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui','F:/FGames/steam/steamapps/common/PBZ']:
   x=x.replace(root,'<local-workspace>' if 'workspace' in root else '<game-root>')
 return x
receipt=read(W/'installation-receipt.json')
installed_root=W
if not (Path(receipt['target'])/receipt['after'][0]['name']).exists():
 # A later JK-only upgrade preserved all Jirai assets. Check that provenance
 # instead of reinstalling or mislabelling the current combined package.
 installed_root=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui/variants/dual-jk-motion-v5')
 newer=read(installed_root/'installation-receipt.json');verified=read(installed_root/'verification.json')
 assert verified['changed_source_equivalent_packages']==['/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple','/HuaShira/Mods/SuiPBZ/Physics/PA_Sui_ClothCollision']
 for package in read(W/'build-report.json')['packages']:
  if package in verified['changed_source_equivalent_packages']:continue
  rel=('ProjectPBZ/Content/'+package.removeprefix('/Game/')) if package.startswith('/Game/') else 'ProjectPBZ/Plugins/HuaShira/Content/'+package.removeprefix('/HuaShira/')
  assert read(W/'independent/json'/(rel+'.json'))==read(installed_root/'independent/json'/(rel+'.json')),package
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=W/'final-legacy'/(rel+ext);b=installed_root/'final-legacy'/(rel+ext)
   assert a.exists()==b.exists()
   if a.exists():assert sha(a)==sha(b)
 receipt=dict(newer,target=newer['mods_directory'],outfits=verified['outfits'],game_build='26367565')
for f in receipt['after']:assert sha(Path(receipt['target'])/f['name'])==f['sha256']
E.mkdir(parents=True,exist_ok=True);M.mkdir(parents=True,exist_ok=True)
for name in ['verification.json','cloth-native-verification.json','cloth-assets-verification.json','simulation-validation.json','shoulder-retarget-verification.json','render-deformation-review.json']:
 write(E/name,scrub(read(S/'variant'/name)))
for name in ['revision-report.json','revision-pose-audit.json']:
 write(E/name,scrub(read(S/name)))
for name in ['front.png','back.png']:
 shutil.copy2(S/'review-final'/name,E/name)
for name in ['hand-curl.png','shoulder-raised.png','stride-back.png']:
 shutil.copy2(S/'review'/name,E/name)
for source,name in [('codex-clipboard-92204603-e10f-4eca-be95-c49c2af052bd.png','runtime-crouch.png'),('codex-clipboard-66b30c91-cbf5-4c4e-92bb-45cf2c4ed6a1.png','runtime-grip.png')]:
 shutil.copy2(Path('C:/Users/yuiffy/AppData/Local/Temp')/source,E/name)
shutil.copy2(S/'review-final/Sui_Jirai_R5_Editable.blend',M/'Sui_Jirai_R5_Editable.blend')
write(E/'dual-container-verification.json',scrub(read(installed_root/'verification.json')))
write(E/'installation-summary.json',{'status':'installed-hash-verified-user-quality-approved-with-known-issues','installed_at':receipt['installed_at'],'game_build':receipt['game_build'],'outfits':receipt['outfits'],'installed_files':receipt['after'],'voice_unchanged':True,'backed_up_previous_model':True})
feedback={'date':'2026-11-16','user_quote':'现在地雷服质量不错哦，提交远端一版。','build':'26367565','baseline':'dual outfit v2 / Jirai R5','reported_issues':['蹲下或者跑动时大腿穿过裙子','希望侧发与双马尾有不插入衣服的物理运动','一只手仍未贴合刀柄'],'evidence':['runtime-crouch.png','runtime-grip.png'],'unreported_tests_not_inferred':True}
feedback['reported_issues']+=['左大腿后侧竖向暗痕','左腿前吊带附近肉色凸起']
for filename,name in [('codex-clipboard-3f0247ea-b8e4-4051-b21a-ae7a4293a0c7.png','runtime-thigh-back.png'),('codex-clipboard-cf884432-3f65-407c-821b-49cf0dad9637.png','runtime-suspender.png')]:
 shutil.copy2(Path('C:/Users/yuiffy/AppData/Local/Temp')/filename,E/name);feedback['evidence'].append(name)
write(E/'runtime-feedback.json',feedback);write(W/'runtime-user-feedback.json',feedback)
write(M/'manifest.json',{'baseline':'Jirai R5 / dual outfit v2','editable_source':{'name':'Sui_Jirai_R5_Editable.blend','bytes':(M/'Sui_Jirai_R5_Editable.blend').stat().st_size,'sha256':sha(M/'Sui_Jirai_R5_Editable.blend')},'fbx_sha256':read(S/'binding-report.json')['fbx_sha256'],'source_origin':'user-provided Tripo export e23d0709-08fd-4812-b7fa-e0bed31d6672; native skeletal adaptation and local refinements','license':'character/model/texture/native rig derivative excluded from code MIT; see NOTICE.md','no_original_visible_game_mesh_or_animation_included':True})
write(W/'checkpoint-freeze.json',{'baseline':'Jirai R5 / dual outfit v2','installed_files':receipt['after'],'source_fbx_sha256':read(S/'binding-report.json')['fbx_sha256'],'checkpoint_model_sha256':sha(M/'Sui_Jirai_R5_Editable.blend'),'further_experiments_must_use_separate_root':True})
print('CHECKPOINT_READY',len(receipt['after']),'installed files verified')
