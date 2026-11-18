"""Verify priority, retained materials and real texture bulk from the installed set."""
from common import *
from package_candidate import inspect_mount
import shutil

def main(installed=False):
 gate=read(ROOT/'verification.json');surface=read(ROOT/'surface-verification.json');assert gate['passed'] and surface['passed']
 for r in gate['textures']:assert r['source_sha256']==surface['outfits'][r['outfit']]['output_atlas_sha256']==sha(ROOT/f"{r['outfit']}-after.png")
 expected={p:read(ROOT/'independent/final'/(relative_package(p)+'.json')) for p in PACKAGES}
 # Compare all other effective packages from the R8, Face3 and Hairpin1 stack.
 packages=set()
 for root in [REPO/'private/jirai-skirt-shape-v1/dual',REPO/'private/jirai-face-v3',REPO/'private/jirai-hairpin-v1']:
  packages.update(read(root/'build-report.json')['packages'])
 retained=sorted(packages-set(PACKAGES))
 if not installed:
  assert_baseline();before=inspect_mount('retained-before',[MODS],retained)
  for label,dirs in [('patch-first',[ROOT/'container',MODS]),('patch-last',[MODS,ROOT/'container'])]:assert inspect_mount(label,dirs)==expected
  assert inspect_mount('retained-after',[MODS,ROOT/'container'],retained)==before
 else:
  receipt=read(ROOT/'installation-receipt.json');assert snapshot()==receipt['after']
  assert inspect_mount('installed',[MODS])==expected
  previous={p:read(ROOT/'independent/retained-before'/(relative_package(p)+'.json')) for p in retained}
  assert inspect_mount('retained-installed',[MODS],retained)==previous
  context=ROOT/'installed-input';context.mkdir(exist_ok=True)
  for p in MODS.iterdir():
   if p.suffix in ['.utoc','.ucas']:shutil.copy2(p,context/p.name)
  for ext in ['.utoc','.ucas']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
  run('read-installed-textures',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,ROOT/'installed-readback'])
  for package,exts in gate['resolved_payloads'].items():
   for ext,digest in exts.items():assert sha(ROOT/'installed-readback'/(relative_package(package)+ext))==digest
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,installed=installed,directory_order_independent=not installed,installed_texture_payload_readback_exact=installed,retained_effective_package_count=len(retained),retained_mesh_material_face_hairpin_cloth_appearance_metadata_exact=True,texture_hashes={r['outfit']:r['source_sha256'] for r in gate['textures']},installed_mod_snapshot=snapshot(),game_runtime_tested=False))
 print('OUTFIT_PATTERNS_MOUNT_VERIFIED','installed' if installed else 'preflight')
if __name__=='__main__':main(sys.argv[1:]==['installed'])
