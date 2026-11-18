from common import *
from package_candidate import inspect_mount
import shutil

def main(installed=False):
 gate=read(ROOT/'verification.json');geometry=read(ROOT/'geometry-verification.json');assert gate['passed'] and geometry['passed'] and geometry['final_container_readback']
 expected={p:read(ROOT/'independent/json'/(relative_package(p)+'.json')) for p in PACKAGES}
 if installed:
  receipt=read(ROOT/'installation-receipt.json')
  assert {p.name:sha(p) for p in MODS.iterdir() if p.is_file()}=={r['name']:r['sha256'] for r in receipt['after']}
  assert inspect_mount('installed',[MODS])==expected
  # Metadata equality alone cannot distinguish the two mesh overlays. Read
  # the payload resolved from the actual installed container set as well.
  context=ROOT/'installed-input';context.mkdir(exist_ok=True)
  for p in MODS.iterdir():
   if p.suffix in ['.utoc','.ucas']:shutil.copy2(p,context/p.name)
  for ext in ['.utoc','.ucas']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
  run('read-installed-body',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel','--filter','Hun_Body_Simple',context,ROOT/'installed-readback'])
  assert sha(ROOT/'installed-readback'/(relative_package(BODY)+'.uexp'))==read(ROOT/'native-patch.json')['output_payload_sha256']
 else:
  assert_installed_baseline()
  for label,dirs in [('patch-last',[MODS,ROOT/'container']),('patch-first',[ROOT/'container',MODS])]:assert inspect_mount(label,dirs)==expected
 # Skin and iris must still resolve to the installed Face3 materials/texture.
 retained=['/HuaShira/Mods/SuiPBZ/Materials/MI_Jirai_Skin','/HuaShira/Mods/SuiPBZ/Materials/MI_Jirai_EyeIris','/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face3','/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_Iris']
 docs=inspect_mount('retained-installed' if installed else 'retained-preflight',[MODS] if installed else [MODS,ROOT/'container'],retained)
 for p in retained:assert docs[p]==read(FACE/'independent/json'/(relative_package(p)+'.json'))
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,installed=installed,directory_order_independent=not installed,installed_native_payload_readback_exact=installed,face3_skin_iris_exact=True,source_atlas_sha256=gate['source_atlas_sha256'],native_render_sha256=gate['native_render_sha256'],installed_mod_snapshot=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()],game_runtime_tested=False))
 print('HAIRPIN_MOUNT_VERIFIED','installed' if installed else 'preflight')
if __name__=='__main__':main(sys.argv[1:]==['installed'])
