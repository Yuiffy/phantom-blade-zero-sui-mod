"""Check actual mod precedence with CUE4Parse before/after installation."""
from common import *
from rebind_materials import replace
MODS=diag.PAKS/'~mods'

def inspect(label,extras,packages):
 env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in extras))
 dest=ROOT/'mount-check'/label
 output=run('mount-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,'json',*[relative_package(p) for p in packages]],env)
 assert not any(x in output for x in ['Failed to','Exception','[WRN]','[ERR]'])
 return {p:read(dest/(relative_package(p)+'.json')) for p in packages}

def check(installed=False):
 gate=read(ROOT/'verification.json');assert gate['status']=='independent-atlas-container-verified-runtime-pending'
 assert read(ROOT/'surface-verification.json')['passed']
 expected={p:read(ROOT/'independent/json'/(relative_package(p)+'.json')) for p in gate['packages']}
 if not installed:
  original=inspect('baseline',[MODS],MATERIALS+[OLD_ATLAS])
  for p in MATERIALS+[OLD_ATLAS]:
   assert original[p]==read(BASE/'independent/json'/(relative_package(p)+'.json')),('Installed face material/atlas differs from supported baseline',p)
  for label,dirs in [('patch-last',[MODS,ROOT/'container']),('patch-first',[ROOT/'container',MODS])]:
   assert inspect(label,dirs,gate['packages'])==expected,'Mount priority depends on directory order'
 else:
  assert inspect('installed',[MODS],gate['packages'])==expected,'Installed resources do not resolve to the face patch'
  old=inspect('installed-old-atlas',[MODS],[OLD_ATLAS])
  assert old[OLD_ATLAS]==read(BASE/'independent/json'/(relative_package(OLD_ATLAS)+'.json'))
 report=dict(passed=True,installed=installed,packages=gate['packages'],patch_priority='numeric _1_P suffix; confirmed by independent mounting',directory_order_independent=not installed,shared_original_atlas_unchanged=True,source_atlas_sha256=gate['source_atlas_sha256'],game_runtime_tested=False,installed_mod_snapshot=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()])
 write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),report)
 print('FACE_MOUNT_VERIFIED', 'installed' if installed else 'preflight',flush=True)

if __name__=='__main__':check(sys.argv[1:]==['installed'])
