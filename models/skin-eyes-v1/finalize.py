"""Publish compact local evidence, without publishing extracted game assets."""
from common import *
import shutil
from datetime import datetime, timezone, timedelta

V=ROOT/'variant';D=ROOT/'dual';OUT=REPO/'evidence/skin-eyes-v1'
assert read(V/'eye-geometry-verification.json')['passed']
assert read(V/'texture-contract-verification.json')['passed']
verified=read(D/'verification.json')
assert verified['status']=='independent-final-container-verified-runtime-pending'
assert read(ROOT/'preview/manifest.json')['source_fbx_sha256']==sha(ROOT/'Sui_Jirai_Hun_Body.fbx')
OUT.mkdir(parents=True,exist_ok=True)
for source,name in [
    (D/'verification.json','verification.json'),
    (V/'eye-geometry-verification.json','eye-geometry-verification.json'),
    (V/'texture-contract-verification.json','texture-contract-verification.json'),
    (ROOT/'source-eye-rays.json','source-eye-rays.json'),
    (ROOT/'source-preservation.json','source-preservation.json'),
    (V/'cloth-native-verification.json','cloth-native-verification.json'),
    (V/'cloth-assets-verification.json','cloth-assets-verification.json'),
    (V/'simulation-validation.json','simulation-validation.json'),
    (V/'render-deformation-review.json','render-deformation-review.json'),
    (ROOT/'preview/manifest.json','preview-manifest.json')]:shutil.copy2(source,OUT/name)
for name in ['before-front','after-front','after-three-quarter','after-oblique']:
    shutil.copy2(ROOT/'preview'/(name+'.png'),OUT/(name+'.png'))
materials=read(V/'material-spec.json')['materials']+read(D/'jk-material-spec.json')['materials']
write(OUT/'material-changes.json',[{k:m[k] for k in ['slot','parent','layer_remap','textures','scalars']} for m in materials])
inputs=dict(
    basis='installed JK5 + Jirai R6 Detail; no R7 skirt research included',
    base_blend_sha256=sha(REPO/'private/jirai-detail-v1/sui-jirai-motion.blend'),
    original_game_skin_parent_json_sha256=sha(next((ROOT/'research/hun-skin').rglob('*.json'))),
    original_game_cloth_parent_json_sha256=sha(PBZ/'research/independent-native-audit/original-shaders/ProjectPBZ/Content/PBZContent/Characters/Hero/Hun_New_V2b/Material/MI_ZeroHun_Cloth_02_b.json'),
    native_parent_readbacks_remain_private=True,
    source_fbx_sha256=sha(ROOT/'Sui_Jirai_Hun_Body.fbx'),
    editable_blend_sha256=sha(ROOT/'sui-jirai-motion.blend'),
    frozen_r6_pipeline=read(CODE/'pipeline-source-hashes.json'))
write(OUT/'source-manifest.json',inputs)
receipt=read(D/'installation-receipt.json') if (D/'installation-receipt.json').is_file() else None
if receipt:
    assert receipt['status']=='installed-hash-verified-runtime-pending'
    for item in receipt['after']:assert sha(Path(receipt['target'])/item['name'])==item['sha256']
    shutil.copy2(D/'installation-receipt.json',OUT/'installation-summary.json')
summary=dict(status=receipt['status'] if receipt else 'offline-verified-not-installed',
    recorded_at=datetime.now(timezone(timedelta(hours=8))).isoformat(),game_build='26367565',
    package_count=verified['package_count'],container_files=verified['container_files'],
    source_fbx_sha256=inputs['source_fbx_sha256'],editable_blend='private/skin-eyes-v1/sui-jirai-motion.blend',
    native_skin_slots=verified['native_skin_slots'],closed_sclera_added=2,
    jk_base_uses_smooth_native_lit_shader=True,jk_has_dedicated_skin_split=False,
    jk_geometry_and_cloth_payloads_unchanged=True,all_appearance_rows_unchanged=True,
    original_jirai_positions_uv_weights_preserved=31516,
    source_position_max_error_cm=read(V/'cloth-native-verification.json')['source_position_max_error_cm'],
    quantized_weights_exact=True,custom_shaders=0,installed=receipt is not None,
    voice_unchanged=receipt['voice_unchanged'] if receipt else None,
    game_runtime_tested=False,preview_basis='offline Blender eye geometry; PBZ native skin shader needs gameplay feedback',
    excluded_parallel_work='Jirai R7 skirt research',
    rollback=receipt['backup'] if receipt else None)
write(OUT/'summary.json',summary)
print(json.dumps({k:summary[k] for k in ['status','package_count','installed','voice_unchanged','game_runtime_tested']},ensure_ascii=False))
