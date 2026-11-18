"""Record independently verified installation without claiming gameplay success."""
from common import *
import ast,shutil

gate=read(ROOT/'verification.json');surface=read(ROOT/'surface-verification.json')
visual=read(ROOT/'visual-review.json');mounted=read(ROOT/'installed-mount-verification.json')
receipt=read(ROOT/'installation-receipt.json')
digest=sha(ROOT/'T_Jirai_Base.png')
assert digest==gate['source_atlas_sha256']==surface['output_atlas_sha256']==visual['source_atlas_sha256']==mounted['source_atlas_sha256']==receipt['source_atlas_sha256']
assert surface['passed'] and mounted['passed'] and mounted['installed'] and visual['reviewed']
assert gate['package_count']==3 and gate['original_material_export_bytes_preserved'] and gate['original_shared_atlas_not_overridden']
for path,want in visual['images'].items():assert sha(path)==want
for f in gate['container_files']:assert sha(f['path'])==sha(diag.PAKS/'~mods'/f['name'])==f['sha256']
before={r['name']:r['sha256'] for r in receipt['before']};after={r['name']:r['sha256'] for r in receipt['after']}
assert all(after.get(name)==value for name,value in before.items())
assert set(after)-set(before)=={r['name'] for r in gate['container_files']}
for name,want in after.items():assert sha(diag.PAKS/'~mods'/name)==want
for path in CODE.glob('*.py'):ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
evidence=REPO/'evidence/jirai-face-v2';evidence.mkdir(exist_ok=True)
for name in ['atlas-report.json','surface-verification.json','material-rebinding.json','verification.json','mount-verification.json','installed-mount-verification.json','visual-review.json']:
 shutil.copy2(ROOT/name,evidence/name)
write(evidence/'reference-review.json',dict(basis='user gameplay screenshot and original Jirai outfit illustration; generated four-view images used only as secondary references',user_image_sha256=sha(Path('C:/Users/yuiffy/AppData/Local/Temp/codex-clipboard-904ec9b5-09af-45f3-9686-d5df1fb2c290.png')),original_illustration_sha256=sha(REPO/'private/tripo-bridge-20261115/original-jirai-design.png'),observations=['warm white sclera inside each eye','clean silver bangs with retained pink streak','fine existing eyebrows occluded by bangs'],reference_images_included=False))
write(evidence/'summary.json',dict(status='installed-independent-mount-verified-runtime-pending',installed_at=receipt['installed_at'],changes=['warm-white nasal eye backing on original skin surface','removed baked brow/lash/skin projections from bangs','isolated skin/hair albedo to protect reused clothing UVs'],original_eyebrows_preserved=True,original_iris_and_sclera_geometry_preserved=True,package_count=3,new_virtual_texture_packages=1,native_material_albedo_rebindings=2,original_shared_atlas_preserved=True,protected_surface_texels_changed=0,shared_clothing_uv_texels_protected=surface['shared_uv_changed_texels_kept_on_original_atlas'],all_preexisting_model_and_voice_files_hash_exact=True,geometry_skeleton_physics_and_cloth_packages_overridden=0,source_atlas_sha256=digest,container_files=[{k:f[k] for k in ['name','bytes','sha256']} for f in gate['container_files']],offline_preview='face-comparison.jpg',offline_preview_basis='same Blender geometry, cameras and lights; native PBZ shader/lighting not emulated',game_runtime_tested=False))
print('FACE2_INSTALLED_EVIDENCE_FINALIZED',receipt['installed_at'])
