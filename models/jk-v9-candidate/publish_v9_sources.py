"""Stage reviewed sources/evidence in the existing public repo; no git actions."""
from pathlib import Path
import json,shutil,hashlib
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];WORK=PBZ/'variants/new-jk-v9'
REPO=Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod');MODEL=REPO/'models/jk-v9-candidate';EVIDENCE=REPO/'evidence/jk-v9-offline'
MODEL.mkdir(exist_ok=True);EVIDENCE.mkdir(exist_ok=True)
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 if dst.suffix.lower() in {'.py','.json','.md','.ps1'}:dst.write_bytes(dst.read_bytes().replace(b'\r\n',b'\n'))
scripts=['adjust_v9.py','refine_ornaments.py','repair_atlas.py','export_atlas_provenance.py','refresh_texture.py','v7_helpers.py','audit_bound_model.py','verify_scope.py','review_motion.py','measure_motion.py','render_ornaments.py','render_details.py','render_final.py','compare_v9.py','build_candidate.py','finish_build.py','prepare_mod.py','import_mod_ue.py','run_blender.py','run_ue.py','package_mod.py','verify_mod.py','verify_texture_chain.py','offline_tools.py','game-materials.json','deliver_v9.py','publish_v9_sources.py']
for n in scripts+['sui-jk-hun-bound.blend','Sui_JK_Hun_Body.fbx','binding-report.json','model-audit.json','scope-check.json','ornament-refinement.json']:
 copy(ROOT/n,MODEL/n)
copy(ROOT/'RESULT.md',MODEL/'README.md');copy(ROOT/'textures/sui-jk-albedo-v9.png',MODEL/'textures/sui-jk-albedo-v9.png')
for n in ['binding-report.json','model-audit.json','scope-check.json','motion-comparison.json','atlas-repair.json','texture-chain.json','ornament-refinement.json','installed-state.json']:
 copy(ROOT/n,EVIDENCE/n)
for n in ['verification.json','skin-verification.json']:copy(WORK/n,EVIDENCE/n)
for p in (ROOT/'delivery').glob('*.jpg'):copy(p,EVIDENCE/p.name)
for n in ['bound-front.png','bound-side.png','bound-back.png','v9-charm-detail.png','v9-wing-detail.png']:
 copy(ROOT/n,EVIDENCE/n)
summary={'status':'offline-candidate-not-installed','baseline_installed_model':'JK v8','runtime_tested':False,'manual_blender_poses_only':True,'triangles':69117,'source_vertices':35459,'bones':264,'materials':10,'packages':43,'current_voice_untouched_by_this_task':True,'source_contract_sha256':json.loads((ROOT/'scope-check.json').read_text())['source_contract_sha256'],'final_cooked_weights_error_after_UE_quantization':0,'final_VT_not_independently_decoded_to_pixels':True,'user_feedback_implemented':['join cat head/body and enlarge body','remove messy stocking colors above wings'],'local_mod_archive_not_published':True}
(EVIDENCE/'summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode('utf8'))
manifest={'status':'offline-candidate-not-installed','baseline':'v8','game_build':'26367565','target':'adult Hun, black-wound-escape','runtime_tested':False,'files':{}}
for folder in [MODEL,EVIDENCE]:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and p.name!='candidate-manifest.json':manifest['files'][p.relative_to(REPO).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(MODEL/'candidate-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf8'))
readme=REPO/'README.md';s=readme.read_text(encoding='utf8');anchor='## 安装模型'
paragraph='另有 [v9 离线候选](models/jk-v9-candidate/README.md)：恢复手指与原骨骼转轴的对齐、清理裙子/后背串色和多余吊带，并参照立绘细化袜子羽翼与背带白猫；已处理预览中猫身体偏小和头身分离的问题。最终容器和 cooked 蒙皮已独立读回，**未安装、未游戏实测**；当前安装模型仍为 v8。见 [饰件对照](evidence/jk-v9-offline/ornaments-v8-v9.jpg) 和 [检查数据](evidence/jk-v9-offline/summary.json)。\n\n'
assert 'v9 离线候选' not in s
s=s.replace(anchor,paragraph+anchor,1);readme.write_bytes(s.replace('\r\n','\n').encode('utf8'))
readme=REPO/'models/README.md';s=readme.read_text(encoding='utf8')
s+='\n[v9 离线候选](jk-v9-candidate/README.md) 修复手指转轴偏移、裙/外套串色及重复吊带，重建白羽翼金心和背带白猫。已按用户近景反馈连好猫头、蝴蝶结与放大的身体，清理翼饰上方的旧贴图残影。保留 v8 肩颈、头、裙和腿的几何。未安装、未游戏实测；[对照图](../evidence/jk-v9-offline/ornaments-v8-v9.jpg)。\n'
readme.write_bytes(s.replace('\r\n','\n').encode('utf8'))
print(json.dumps({'repo':str(REPO),'manifest_files':len(manifest['files']),'mod_containers_copied':False}))
