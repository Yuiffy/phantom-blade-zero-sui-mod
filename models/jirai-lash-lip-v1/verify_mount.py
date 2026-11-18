"""Verify overlay order and every retained effective package, including JK."""
from common import *
from package_candidate import inspect_mount,extract
def main(installed=False):
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');assert gate['passed'] and geometry['passed']
 assert gate['native_render_sha256']==geometry['native_render_sha256']==sha(ROOT/'final-render.npz')
 expected={p:read(ROOT/'independent/final'/(relative_package(p)+'.json')) for p in PACKAGES}
 packages=set()
 for folder in [REPO/'private/jirai-skirt-shape-v1/dual',REPO/'private/jirai-face-v3',REPO/'private/jirai-hairpin-v1',FACE,PAT]:packages.update(read(folder/'build-report.json')['packages'])
 packages.add('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
 # The old Hybrid1 albedo is retired with its container; the new Skin MI
 # references LashLip1. It is not a retained effective dependency.
 retired={'/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face2Hybrid1'}
 retained=sorted(packages-set(PACKAGES)-retired)
 if not installed:
  assert_baseline();before=inspect_mount('retained-before',[MODS],retained)
  for label,dirs in [('patch-first',[ROOT/'container',MODS]),('patch-last',[MODS,ROOT/'container'])]:assert inspect_mount(label,dirs)==expected
  assert inspect_mount('retained-after',[MODS,ROOT/'container'],retained)==before
 else:
  receipt=read(ROOT/'installation-receipt.json');assert snapshot()==receipt['after']
  assert inspect_mount('installed',[MODS])==expected
  before={p:read(ROOT/'independent/retained-before'/(relative_package(p)+'.json')) for p in retained}
  assert inspect_mount('retained-installed',[MODS],retained)==before
  dest=extract('installed',[MODS])
  for package,exts in gate['resolved_payloads'].items():
   for ext,digest in exts.items():assert sha(dest/(relative_package(package)+ext))==digest
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,installed=installed,directory_order_independent=not installed,source_atlas_sha256=gate['source_atlas_sha256'],native_render_sha256=gate['native_render_sha256'],retained_effective_packages=len(retained),retained_jk_hairpin_face_materials_patterns_cloth_appearance_metadata_exact=True,installed_payload_readback_exact=installed,installed_mod_snapshot=snapshot(),game_runtime_tested=False))
 print('LASHLIP_MOUNT_VERIFIED','installed' if installed else 'candidate',flush=True)
if __name__=='__main__':main(sys.argv[1:]==['installed'])
