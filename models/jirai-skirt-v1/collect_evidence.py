"""Publish only reviewed previews and compact validation, never game exports."""
from pathlib import Path
import json,shutil,hashlib
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';V=W/'variant';O=R/'evidence/jirai-r7-skirt'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dual=read(W/'dual/verification.json');assert dual['status']=='independent-final-container-verified-runtime-pending' and dual['fishnet_v1_8k_payload_exact']
visual=read(W/'visual-review.json');assert visual['reviewed'] and visual['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and visual['cloth_spec_sha256']==sha(W/'cloth-spec.json')
editable=read(R/'models/jirai-skirt-v1/source-manifest.json')
assert editable['source_fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx')
assert editable['sha256']==sha(R/'models/jirai-skirt-v1'/editable['file'])
atlas=read(V/'preview-atlas.json');assert atlas['source_atlas_sha256']==editable['atlas']['source_atlas_sha256']==dual['source_atlas_sha256']
assert atlas['width']==atlas['height']==8192
assert read(V/'rest-preview.json')['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx')
assert all(x['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') for x in read(V/'coverage-preview.json'))
O.mkdir(parents=True,exist_ok=True);images=[]
for file,digest in visual['images'].items():
 p=Path(file);assert sha(p)==digest;dst=O/p.name;shutil.copy2(p,dst);images.append(dict(file=dst.name,sha256=digest,basis='offline Blender rendering of cooked mesh/actual Chaos reconstruction'))
for source,name in [(W/'source-preservation.json','source-preservation.json'),(W/'coverage-verification.json','coverage-verification.json'),(V/'simulation-validation.json','simulation-validation.json'),(V/'articulation-shape-gate.json','articulation-shape-gate.json'),(V/'articulation-validation.json','articulation-validation.json'),(V/'cloth-assets-verification.json','cloth-assets-verification.json'),(V/'render-pin-authoring.json','render-pin-authoring.json'),(V/'render-deformation-review.json','render-deformation-review.json'),(V/'suspender-fit-audit.json','suspender-fit-audit.json'),(V/'eye-geometry-verification.json','eye-geometry-verification.json'),(V/'texture-contract-verification.json','texture-contract-verification.json'),(V/'coverage-preview.json','coverage-preview.json'),(V/'preview-atlas.json','preview-atlas.json'),(V/'rest-preview.json','rest-preview.json')]:
 shutil.copy2(source,O/name)
before=read(W/'baseline/articulated-surface-audit.json');after=read(V/'articulated-surface-audit.json')
def counts(rows):
 return {row['profile']:{key:max(f[key] for f in row['thigh_edge_intersections']) for key in ['visible_thigh_edges_crossing_skirt','raw_thigh_edge_intersections']} for row in rows}
a=counts(after);assert all(v['visible_thigh_edges_crossing_skirt']==0 for v in a.values())
fit=read(V/'suspender-fit-audit.json');shape=read(V/'articulation-validation.json')
receipt=read(W/'dual/installation-receipt.json') if (W/'dual/installation-receipt.json').exists() else None
if receipt:
 assert receipt['status']=='installed-hash-verified-runtime-pending'
 for f in dual['container_files']:assert sha(Path(receipt['target'])/f['name'])==f['sha256']
result=dict(status='installed-runtime-pending' if receipt else 'verified-candidate-not-installed',fbx_sha256=sha(W/'Sui_Jirai_Hun_Body.fbx'),cloth_spec_sha256=sha(W/'cloth-spec.json'),basis='installed R6 SkinEyes1 and Fishnet1 8K atlas preserved; skirt and opaque safety shorts revised',package_count=dual['package_count'],before=counts(before),after=a,contact_scope='64 occlusion rays per contact, 19 sampled frames per synthetic clip; not all gameplay cameras or animations',shape_passed=shape['passed'],shorts_continuous_and_opaque=read(W/'coverage-verification.json')['passed'],suspender_min_signed_cm=min(x['signed_min_cm'] for x in fit['samples']),suspender_max_gap_cm=max(x['distance_max_cm'] for x in fit['samples']),skin_eyes_v1_preserved=True,fishnet_v1_8k_payload_exact=dual['fishnet_v1_8k_payload_exact'],source_atlas_sha256=dual['source_atlas_sha256'],jk5_unchanged=dual['jk5_and_all_appearance_rows_unchanged'],voice_unchanged=receipt['voice_unchanged'] if receipt else None,installed_at=receipt['installed_at'] if receipt else None,container_files=[{k:f[k] for k in ['name','bytes','sha256']} for f in dual['container_files']],images=images,visual_review_observations=visual['observations'],limitations=visual['limitations'],game_runtime_tested=False,game_animation_library_included=False)
(O/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
(O/'README.md').write_text('# 地雷岁 R7 离线证据\n\n`result.json` 记录本次输入、独立读回、安装状态和旧版对比。全部预览均为离线 Blender 渲染，来自真实 Chaos 输出及最终 cooked 网格重建，不是游戏截图。作者合成动作不覆盖原游戏全部动画。\n\n`coverage-*.png` 隐藏了裙子和其他衣饰，用于检查安全裤裤底与分腿覆盖。腿/裙交线同时保留原始统计和有限视线遮挡后的统计；这些数量不是穿模面积，也不能证明所有游戏视角完全无穿模。模型与预览沿用根目录 NOTICE.md 的许可边界。\n',encoding='utf8')
print('COMPACT_EVIDENCE_SAVED',result['status'],len(images))
