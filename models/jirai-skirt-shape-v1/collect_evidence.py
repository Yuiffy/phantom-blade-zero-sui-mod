"""Publish compact provenance and reviewed offline views, never game exports."""
import json,hashlib,shutil
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';V=W/'variant';D=W/'dual';O=R/'evidence/jirai-skirt-shape-v1';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dual=read(D/'verification.json');recovery=read(V/'recovery-validation.json');inherit=read(V/'inheritance-verification.json');visual=read(W/'visual-review.json');overlay=read(D/'overlay-verification.json')
assert dual['status']=='independent-final-container-verified-runtime-pending' and recovery['passed'] and inherit['passed'] and visual['reviewed'] and overlay['passed']
assert visual['combined_tests_sha256']==sha(V/'combined-tests.json') and visual['cooked_mapping_sha256']==sha(V/'independent/cloth-native-details.json')
images=[]
for path,digest in visual['images'].items():
 p=Path(path);assert sha(p)==digest;dst=O/p.name;shutil.copy2(p,dst);images.append({'file':dst.name,'sha256':digest,'basis':visual.get('image_basis',{}).get(path,'offline Blender render of continuous Chaos output through final cooked mapping')})
for name in ['recovery-contact.png','coverage-contact.png','shape-comparison.png']:
 p=W/'preview'/name
 if p.exists():shutil.copy2(p,O/name)
for source,name in [(V/'recovery-validation.json','recovery-validation.json'),(V/'inheritance-verification.json','inheritance-verification.json'),(V/'simulation-validation.json','simulation-validation.json'),(V/'articulation-validation.json','articulation-validation.json'),(V/'cloth-assets-verification.json','cloth-assets-verification.json'),(V/'render-pin-authoring.json','render-pin-authoring.json'),(V/'render-deformation-review.json','render-deformation-review.json'),(D/'overlay-verification.json','overlay-verification.json'),(V/'texture-contract-verification.json','texture-contract-verification.json')]:
 shutil.copy2(source,O/name)
shutil.copy2(W/'reference-review.json',O/'reference-review.json')
shutil.copy2(C/'render-settings.json',O/'render-settings.json')
shutil.copy2(V/'rejected-blend40/recovery-validation.json',O/'rejected-blend40-recovery.json')
for name in ['shape-preview.json','recovery-preview.json','coverage-preview.json']:
 shutil.copy2(V/name,O/name)
receipt=read(D/'installation-receipt.json') if (D/'installation-receipt.json').exists() else None
if receipt:
 for f in receipt['after']:assert sha(Path(receipt['target'])/f['name'])==f['sha256']
 assert read(D/'installed-overlay-verification.json')['passed']
 shutil.copy2(D/'installed-overlay-verification.json',O/'installed-overlay-verification.json')
selected=read(W/'selection.json');skirt=next(r for r in read(W/'cloth-spec.json') if r['slot']=='MI_Jirai_Skirt')
(O/'selected-parameters.json').write_text(json.dumps({'selection':selected,'skirt':skirt,'collision_radii_cm':{'lower_thigh_capsules':9.5,'same_as_recovery1':True},'geometry_source':'../../models/jirai-skirt-shape-v1/Sui_Jirai_R8_Shape_Editable.blend','shape_authoring':read(W/'shape-authoring.json'),'final_render_settings':read(C/'render-settings.json'),'continuous_shorts_unchanged':True},indent=2))
audit=read(V/'articulated-surface-audit.json');contacts={r['profile']:{k:max(f[k] for f in r['thigh_edge_intersections']) for k in ['visible_thigh_edges_crossing_skirt','raw_thigh_edge_intersections']} for r in audit}
result={'status':'installed-hash-and-overlay-verified-runtime-pending' if receipt else 'verified-candidate-not-installed','source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'cloth_spec_sha256':sha(W/'cloth-spec.json'),'package_count':dual['package_count'],'continuous_recovery_passed':recovery['passed'],'recovery_tests':len(recovery['records']),'repeated_cycles_per_test':3,'synthetic_input_rates_hz':[30,60],'shape_and_particle_gates_unchanged':True,'skirt_geometry_reshaped':True,'max_visible_simulated_blend':read(C/'render-settings.json')['skirt_max_simulated_blend'],'body_and_continuous_opaque_shorts_preserved':True,'jk5_preserved':True,'face2_overlay_verified':True,'voice_and_face_files_unchanged':bool(receipt and receipt['voice_unchanged'] and receipt['face_overlay_unchanged']),'container_files':[{k:f[k] for k in ['name','bytes','sha256']} for f in dual['container_files']],'installed_at':receipt['installed_at'] if receipt else None,'contacts':contacts,'contact_scope':'Sampled synthetic frames and finite occlusion rays; counts are not penetration area. Deep-motion clipping is allowed by user priority and retained explicitly.','images':images,'visual_observations':visual['observations'],'limitations':['No gameplay animations or runtime video captured; agent did not launch, control or stop the game.','Offline recovery is not a runtime guarantee. Some deep-action clipping remains.','Blender does not emulate native PBZ shading, wind, animation transitions, LOD or teleport behavior.'],'game_runtime_tested':False}
(O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(O/'README.md').write_text('# 地雷岁 R8 裙型修整证据\n\n状态以 `result.json` 为准。参考用户原立绘与生成四视图，撤回 R7 下半截 4 cm 外扩，收拢并压低外翘裙缘。尺寸与公式见 `selected-parameters.json`；最终可见混合上限为 35%，见 `render-settings.json`。首轮 40% 候选未通过 3 cm 局部回落门槛，失败报告保留为 `rejected-blend40-recovery.json`，该候选未安装。`shape-comparison.png` 使用同机位、同尺度的旧/新静态几何和新候选求解站定表面。\n\n裙面与 cage 改形后重新导入、绑定并实际连续求解；六组走停/跑停/蹲起检查使用三动作、30/60 Hz 与各三轮动作后站定。本目录结论来自新容器量化映射，沿用 Recovery1 的下摆顶点集合及原门槛，未用缩裙后重新筛选的高度段排除难测顶点。\n\n所有预览为离线 Blender 渲染，不是游戏截图。裆部连通不透明安全裤、身体、骨架、头发参数保留；仅裙子与导向几何变化。保留深动作穿裙统计，不声称全动作无穿模。Face2 独立补丁按两种目录顺序检查挂载，安装后再读回。用户实机复测尚待反馈。许可边界见根目录 NOTICE.md。\n',encoding='utf8')
print('RECOVERY_EVIDENCE_SAVED',result['status'],len(images))
