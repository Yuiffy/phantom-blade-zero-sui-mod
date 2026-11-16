"""Stage reviewed sources/evidence in the authorized public repo; no git actions."""
from pathlib import Path
import json,hashlib,shutil
R=Path(__file__).resolve().parent;PBZ=R.parents[2];W=PBZ/'variants/new-jk-v10';REPO=Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod')
MODEL=REPO/'models/jk-v10-candidate';EVIDENCE=REPO/'evidence/jk-v10-offline';MODEL.mkdir(exist_ok=True);EVIDENCE.mkdir(exist_ok=True)
def copy(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 if dst.suffix.lower() in {'.py','.json','.md','.ps1'}:dst.write_bytes(dst.read_bytes().replace(b'\r\n',b'\n'))
scripts=['adjust_v10.py','repair_atlas_v10.py','refresh_texture.py','v7_helpers.py','audit_bound_model.py','verify_scope.py','review_guard.py','render_bag.py','render_final.py','render_details.py','compare_v10.py','build_candidate.py','finish_build.py','prepare_mod.py','import_mod_ue.py','run_blender.py','run_ue.py','package_mod.py','verify_mod.py','verify_texture_chain.py','offline_tools.py','game-materials.json','deliver_v10.py','publish_v10_sources.py']
reports=['binding-report.json','model-audit.json','scope-check.json','guard-comparison.json','atlas-repair.json','texture-chain.json']
for n in scripts+reports+['sui-jk-hun-bound.blend','Sui_JK_Hun_Body.fbx','sleeve-source-field.npy']:copy(R/n,MODEL/n)
copy(R/'RESULT.md',MODEL/'README.md');copy(R/'textures/sui-jk-albedo-v10.png',MODEL/'textures/sui-jk-albedo-v10.png')
for n in reports+['guard-after.json']:copy(R/n,EVIDENCE/n)
for n in ['verification.json','skin-verification.json']:copy(W/n,EVIDENCE/n)
for n in ['guard-after-high.png','guard-after-high-side.png','guard-after-forward.png','bag-inner-v9.png','bag-inner-v10.png','bound-front.png','bound-side.png','bound-back.png']:copy(R/n,EVIDENCE/n)
copy(R.parent/'tripo-refine-v9/guard-before.json',EVIDENCE/'guard-before.json')
copy(R/'delivery/guard-and-bag-v9-v10.jpg',EVIDENCE/'guard-and-bag-v9-v10.jpg')
summary={'status':'offline-candidate-not-installed','baseline_checkpoint':'v9 ce1a1de','baseline_installed_model_last_observed':'JK v8','runtime_tested':False,'manual_blender_poses_only':True,'source_vertices':35459,'triangles':69117,'bones':264,'materials':10,'packages':43,'voice_untouched':True,'final_cooked_weights_error_after_UE_quantization':0,'final_VT_not_independently_decoded_to_pixels':True,'no_claim_of_physical_shirt_layer_or_all_poses_fixed':True,'local_mod_archive_not_published':True}
(EVIDENCE/'summary.json').write_bytes((json.dumps(summary,indent=2)+'\n').encode('utf8'))
manifest={'status':'offline-candidate-not-installed','baseline':'v9 ce1a1de','game_build':'26367565','target':'adult Hun, black-wound-escape','runtime_tested':False,'files':{}}
for folder in [MODEL,EVIDENCE]:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and p.name!='candidate-manifest.json':manifest['files'][p.relative_to(REPO).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(MODEL/'candidate-manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode('utf8'))
readme=REPO/'README.md';s=readme.read_text(encoding='utf8');anchor='## 安装模型'
paragraph='新增 [v10 离线候选](models/jk-v10-candidate/README.md)：在 v9 基础上修正右腋下衣身误跟上臂造成的背部尖折，清理外套白灰/蓝色投影，并重绘书包朝向身体的粉色内侧。已独立读回最终容器和蒙皮，**未安装、未游戏实测**；人工抬臂预览不能保证实际长柄防御无穿插。见 [前后对照](evidence/jk-v10-offline/guard-and-bag-v9-v10.jpg)。\n\n'
if 'v10 离线候选' not in s:readme.write_bytes(s.replace(anchor,paragraph+anchor,1).replace('\r\n','\n').encode('utf8'))
p=REPO/'models/README.md';s=p.read_text(encoding='utf8')
if 'jk-v10-candidate' not in s:p.write_bytes((s+'\n[v10 离线候选](jk-v10-candidate/README.md) 修正右腋下衣身权重泄漏及对应表面位置，清理右背串色和书包内侧投影。保留 v9 手部、猫挂件与袜饰修复。未安装、未游戏实测；[离线对照](../evidence/jk-v10-offline/guard-and-bag-v9-v10.jpg)。\n').replace('\r\n','\n').encode('utf8'))
p=REPO/'NOTICE.md';s=p.read_text(encoding='utf8').replace('至 `models/jk-v9-candidate`','至 `models/jk-v10-candidate`').replace('图集有局部修复。','图集有局部修复；v10 继续修正抬臂衣身绑定与外套/书包内侧图集。');p.write_bytes(s.replace('\r\n','\n').encode('utf8'))
print(json.dumps({'repo':str(REPO),'manifest_files':len(manifest['files']),'mod_containers_copied':False}))
