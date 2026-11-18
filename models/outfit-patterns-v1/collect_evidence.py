"""Export numerical verification only; references and derived pixels stay private."""
from common import *

def main():
 gate=read(ROOT/'verification.json');surface=read(ROOT/'surface-verification.json');mount=read(ROOT/'installed-mount-verification.json');receipt=read(ROOT/'installation-receipt.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and surface['passed'] and mount['passed'] and visual['reviewed']
 assert snapshot()==receipt['after']
 for row in gate['textures']:
  outfit=row['outfit'];digest=row['source_sha256'];assert sha(ROOT/f'{outfit}-after.png')==digest==mount['texture_hashes'][outfit]==visual['texture_hashes'][outfit]==surface['outfits'][outfit]['output_atlas_sha256']
 for path,digest in visual['images'].items():assert sha(path)==digest
 out=REPO/'evidence/outfit-patterns-v1'
 for name in ['verification.json','atlas-report.json','surface-verification.json']:write(out/name,read(ROOT/name))
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],files=receipt['after'],added=receipt['added'],previous_face3_r8_hairpin_voice_files_exact=receipt['previous_face3_r8_hairpin_voice_files_exact'],installed_mount_verified=mount['passed'],installed_texture_payload_readback_exact=mount['installed_texture_payload_readback_exact'],retained_effective_package_count=mount['retained_effective_package_count'],game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,views=visual['views'],observations=visual['observations'],texture_hashes=visual['texture_hashes'],native_hashes=visual['native_hashes'],private_image_sha256=list(visual['images'].values()),basis='frozen independently decoded installed geometry, unchanged by this two-texture overlay; source PNG shading preview',cooked_vt_independently_pixel_decoded=False,game_runtime_tested=False))
 source=read(ROOT/'sources.json')
 write(out/'source-hashes.json',dict(jk_original_4k_sha256=source['jk_original_4k_sha256'],jk_upscale=source['jk_upscale'],jk_reference_sha256=sha(source['jk_reference']),jirai_reference_sha256=sha(source['jirai_reference']),reference_and_derived_images_private=True))
 print('OUTFIT_PATTERNS_NUMERICAL_EVIDENCE_EXPORTED')
if __name__=='__main__':main()
