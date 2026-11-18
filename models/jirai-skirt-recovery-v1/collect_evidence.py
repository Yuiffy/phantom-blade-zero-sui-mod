"""Publish compact provenance and reviewed offline views, never game exports."""
import json,hashlib,shutil
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-recovery-v1';V=W/'variant';D=W/'dual';O=R/'evidence/jirai-skirt-recovery-v1';O.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dual=read(D/'verification.json');recovery=read(V/'recovery-validation.json');inherit=read(V/'inheritance-verification.json');visual=read(W/'visual-review.json');overlay=read(D/'overlay-verification.json')
assert dual['status']=='independent-final-container-verified-runtime-pending' and recovery['passed'] and inherit['passed'] and visual['reviewed'] and overlay['passed']
assert visual['combined_tests_sha256']==sha(V/'combined-tests.json') and visual['cooked_mapping_sha256']==sha(V/'independent/cloth-native-details.json')
images=[]
for path,digest in visual['images'].items():
 p=Path(path);assert sha(p)==digest;dst=O/p.name;shutil.copy2(p,dst);images.append({'file':dst.name,'sha256':digest,'basis':'offline Blender render of continuous Chaos output through final cooked mapping'})
for name in ['recovery-contact.png','coverage-contact.png']:
 p=W/'preview'/name
 if p.exists():shutil.copy2(p,O/name)
for source,name in [(V/'recovery-validation.json','recovery-validation.json'),(V/'inheritance-verification.json','inheritance-verification.json'),(V/'simulation-validation.json','simulation-validation.json'),(V/'articulation-validation.json','articulation-validation.json'),(V/'cloth-assets-verification.json','cloth-assets-verification.json'),(V/'render-pin-authoring.json','render-pin-authoring.json'),(V/'render-deformation-review.json','render-deformation-review.json'),(D/'overlay-verification.json','overlay-verification.json'),(V/'texture-contract-verification.json','texture-contract-verification.json')]:
 shutil.copy2(source,O/name)
receipt=read(D/'installation-receipt.json') if (D/'installation-receipt.json').exists() else None
if receipt:
 for f in receipt['after']:assert sha(Path(receipt['target'])/f['name'])==f['sha256']
 assert read(D/'installed-overlay-verification.json')['passed']
 shutil.copy2(D/'installed-overlay-verification.json',O/'installed-overlay-verification.json')
selected=read(W/'selection.json');skirt=next(r for r in read(W/'cloth-spec.json') if r['slot']=='MI_Jirai_Skirt')
(O/'selected-parameters.json').write_text(json.dumps({'selection':selected,'skirt':skirt,'collision_change_cm':{'lower_thigh_capsules_before':13,'after':9.5},'geometry_source':'../../models/jirai-skirt-v1/Sui_Jirai_R7_Skirt_Editable.blend','geometry_and_continuous_shorts_unchanged':True},indent=2))
audit=read(V/'articulated-surface-audit.json');contacts={r['profile']:{k:max(f[k] for f in r['thigh_edge_intersections']) for k in ['visible_thigh_edges_crossing_skirt','raw_thigh_edge_intersections']} for r in audit}
result={'status':'installed-hash-and-overlay-verified-runtime-pending' if receipt else 'verified-candidate-not-installed','source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'cloth_spec_sha256':sha(W/'cloth-spec.json'),'package_count':dual['package_count'],'continuous_recovery_passed':recovery['passed'],'recovery_tests':len(recovery['records']),'repeated_cycles_per_test':3,'synthetic_input_rates_hz':[30,60],'shape_and_particle_gates_unchanged':True,'geometry_and_continuous_opaque_shorts_preserved':True,'jk5_preserved':True,'face2_overlay_verified':True,'voice_and_face_files_unchanged':bool(receipt and receipt['voice_unchanged'] and receipt['face_overlay_unchanged']),'container_files':[{k:f[k] for k in ['name','bytes','sha256']} for f in dual['container_files']],'installed_at':receipt['installed_at'] if receipt else None,'contacts':contacts,'contact_scope':'Sampled synthetic frames and finite occlusion rays; counts are not penetration area. Deep-motion clipping is allowed by user priority and retained explicitly.','images':images,'visual_observations':visual['observations'],'limitations':['No gameplay animations or runtime video captured; agent did not launch, control or stop the game.','Offline recovery is not a runtime guarantee. Some deep-action clipping remains.','Blender does not emulate native PBZ shading, wind, animation transitions, LOD or teleport behavior.'],'game_runtime_tested':False}
(O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(O/'README.md').write_text('# 地雷岁裙摆回落候选证据\n\n状态以 `result.json` 为准。六组连续走停/跑停/蹲起测试使用三个动作、30/60 Hz 与各三轮动作后站定；原 R7 初始化重置错误已经修正并记录状态。试算只用于选参数；本目录回落结论来自最终容器量化映射重建。\n\n所有预览为离线 Blender 渲染，来自真实连续 Chaos 输出及最终 cooked 表面，不是游戏截图。裆部连通不透明安全裤、几何、骨架、头发参数与 R7 完全保持。保留深动作穿裙统计，不声称全动作无穿模。Face2 独立补丁按两种目录顺序检查挂载，安装后再读回。用户实机复测尚待反馈。\n',encoding='utf8')
print('RECOVERY_EVIDENCE_SAVED',result['status'],len(images))
