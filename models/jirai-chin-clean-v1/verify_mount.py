"""Check order, all retained effective exports, and the actual installed set."""
from common import *
from package_candidate import inspect_mount,extract

def main(installed=False):
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');assert gate['passed'] and geometry['passed']
 assert gate['native_render_sha256']==geometry['native_render_sha256']==sha(ROOT/'final-render.npz')
 expected={p:read(ROOT/'independent/final'/(relative_package(p)+'.json')) for p in PACKAGES}
 files=list((ROOT/'baseline-legacy').rglob('*.uasset'));retained=[]
 for f in files:
  rel=f.relative_to(ROOT/'baseline-legacy')
  if rel.as_posix() not in {relative_package(p)+'.uasset' for p in PACKAGES+['/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_LashLip1']}:
   # Relative game/plugin package path has a known prefix in this repository.
   if rel.as_posix().startswith('ProjectPBZ/Plugins/HuaShira/Content/'):
    package='/HuaShira/'+rel.as_posix().removeprefix('ProjectPBZ/Plugins/HuaShira/Content/').removesuffix('.uasset')
   elif rel.as_posix().startswith('ProjectPBZ/Content/'):
    package='/Game/'+rel.as_posix().removeprefix('ProjectPBZ/Content/').removesuffix('.uasset')
   else:raise AssertionError(str(rel))
   retained.append(package)
 retained=sorted(retained);assert len(retained)>=100
 if not installed:
  assert_baseline();before=inspect_mount('retained-before',[MODS],retained)
  for label,dirs in [('patch-first',[ROOT/'container',MODS]),('patch-last',[MODS,ROOT/'container'])]:assert inspect_mount(label,dirs)==expected
  assert inspect_mount('retained-after',[MODS,ROOT/'container'],retained)==before
  dest=ROOT/'resolved-legacy'
 else:
  receipt=read(ROOT/'installation-receipt.json');assert snapshot()==receipt['after']
  assert inspect_mount('installed',[MODS])==expected
  before={p:read(ROOT/'independent/retained-before'/(relative_package(p)+'.json')) for p in retained}
  assert inspect_mount('retained-installed',[MODS],retained)==before
  dest=extract('installed',[MODS])
  for package,exts in gate['resolved_payloads'].items():
   for ext,digest in exts.items():assert sha(dest/(relative_package(package)+ext))==digest
 for package in retained:
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=ROOT/'baseline-legacy'/(relative_package(package)+ext);b=dest/(relative_package(package)+ext)
   assert a.exists()==b.exists(),(package,ext)
   if a.exists():assert sha(a)==sha(b),(package,ext)
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,installed=installed,directory_order_independent=not installed,source_atlas_sha256=gate['source_atlas_sha256'],native_render_sha256=gate['native_render_sha256'],retained_effective_packages=len(retained),retained_metadata_and_complete_export_payloads_exact=True,jk_face_skirt_cloth_patterns_voice_preserved=True,installed_payload_readback_exact=installed,installed_mod_snapshot=snapshot(),game_runtime_tested=False))
 print('CHIN_MOUNT_VERIFIED','installed' if installed else 'candidate',len(retained),flush=True)

if __name__=='__main__':main(sys.argv[1:]==['installed'])
