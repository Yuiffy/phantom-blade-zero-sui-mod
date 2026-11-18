"""Export reviewed numeric/hash evidence; keep game and reference assets private."""
from common import *

def main():
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json')
 receipt=read(ROOT/'installation-receipt.json');mount=read(ROOT/'installed-mount-verification.json');visual=read(ROOT/'visual-review.json')
 assert gate['passed'] and geometry['passed'] and mount['passed'] and visual['reviewed']
 for report in [geometry,mount,visual]:
  assert report['source_atlas_sha256']==gate['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
  assert report['native_render_sha256']==gate['native_render_sha256']==sha(ROOT/'final-render.npz')
 assert {p.name:sha(p) for p in MODS.iterdir() if p.is_file()}=={r['name']:r['sha256'] for r in receipt['after']}
 for path,digest in visual['images'].items():assert sha(path)==digest
 out=REPO/'evidence/jirai-hairpin-v1'
 for name in ['verification.json','geometry-verification.json','author-report.json','atlas-report.json','native-patch.json']:
  doc=read(ROOT/name)
  if name=='verification.json':doc['container_files']=[{k:v for k,v in row.items() if k!='path'} for row in doc['container_files']]
  write(out/name,doc)
 write(out/'installation.json',dict(status=receipt['status'],installed_at=receipt['installed_at'],base_model='Face3 + R8 Shape1',files=receipt['after'],added=receipt['added'],previous_face3_r8_voice_files_exact=receipt['previous_face3_r8_voice_files_exact'],installed_mount_verified=mount['passed'],installed_native_payload_readback_exact=mount['installed_native_payload_readback_exact'],game_runtime_tested=False))
 write(out/'visual-review.json',dict(reviewed=True,views=visual['views'],observations=visual['observations'],source_atlas_sha256=visual['source_atlas_sha256'],native_render_sha256=visual['native_render_sha256'],private_image_sha256=list(visual['images'].values()),renderer='Blender Cycles; independently decoded native geometry with source PNG albedo',cooked_vt_independently_pixel_decoded=False,game_runtime_tested=False))
 print('HAIRPIN_NUMERICAL_EVIDENCE_EXPORTED')

if __name__=='__main__':main()
