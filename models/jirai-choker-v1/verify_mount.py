"""Check mount priority and every other installed model/audio package payload."""
from common import *
from package_candidate import inspect_mount,extract

def main(installed=False):
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');assert gate['passed'] and geometry['passed']
 assert gate['native_render_sha256']==geometry['native_render_sha256']==sha(ROOT/'final-render.npz')
 expected={BODY:read(ROOT/'independent/final'/(relative_package(BODY)+'.json'))}
 baseline=ROOT/'baseline-legacy'
 if not installed:
  assert_baseline();baseline=extract('baseline',[MODS])
  assert sha(baseline/(relative_package(BODY)+'.uexp'))==sha(PIN/'resolved-legacy'/(relative_package(BODY)+'.uexp'))
 retained=[]
 for f in baseline.rglob('*.uasset'):
  rel=f.relative_to(baseline).as_posix()
  if rel==relative_package(BODY)+'.uasset':continue
  if rel.startswith('ProjectPBZ/Plugins/HuaShira/Content/'):package='/HuaShira/'+rel.removeprefix('ProjectPBZ/Plugins/HuaShira/Content/').removesuffix('.uasset')
  elif rel.startswith('ProjectPBZ/Content/'):package='/Game/'+rel.removeprefix('ProjectPBZ/Content/').removesuffix('.uasset')
  else:raise AssertionError(rel)
  retained.append(package)
 retained=sorted(retained);assert len(retained)>=130
 if not installed:
  before=inspect_mount('retained-before',[MODS],retained)
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
   a=baseline/(relative_package(package)+ext);b=dest/(relative_package(package)+ext)
   assert a.exists()==b.exists(),(package,ext)
   if a.exists():assert sha(a)==sha(b),(package,ext)
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,installed=installed,directory_order_independent=not installed,native_render_sha256=gate['native_render_sha256'],retained_effective_packages=len(retained),retained_metadata_and_complete_export_payloads_exact=True,jk_face_skirt_cloth_patterns_and_voice_preserved=True,installed_payload_readback_exact=installed,installed_mod_snapshot=snapshot(),game_runtime_tested=False))
 print('CHOKER_MOUNT_VERIFIED','installed' if installed else 'candidate',len(retained),flush=True)
if __name__=='__main__':main(sys.argv[1:]==['installed'])
