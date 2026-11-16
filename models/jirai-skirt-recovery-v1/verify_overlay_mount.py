"""Verify the independently installed Face2 overlay with the new skirt body."""
from skin_material_support import *
from offline_tools import diagnostic_run
import shutil

V=ROOT/'variant';D=ROOT/'dual';FACE=REPO/'private/jirai-face-v2';MODS=diag.PAKS/'~mods'
installed='--installed' in sys.argv
face=read(FACE/'verification.json');dual=read(D/'verification.json')
assert face['status']=='independent-atlas-container-verified-runtime-pending'
assert dual['status']=='independent-final-container-verified-runtime-pending'
face_files=face['container_files']
for f in face_files:assert sha(MODS/f['name'])==f['sha256'],'Face overlay changed; re-evaluate compatibility'
packages=face['packages']+['/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base','/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple']
expected={p:read((FACE if p in face['packages'] else D)/'independent/json'/(relative_package(p)+'.json')) for p in packages}
if installed:
 orders=[('installed',[MODS])]
else:
 # Installation replaces the old outfit triple. Do not mount both versions:
 # equal-priority duplicates can resolve to R6 and are not the intended set.
 retained=D/'overlay-retained';retained.mkdir(exist_ok=True)
 before=read(D/'installed-before.json')
 unchanged=[f for f in before if not f['name'].startswith('z_Sui_DualOutfit_')]
 assert len(before)-len(unchanged)==3
 assert {p.name for p in MODS.iterdir() if p.is_file()}=={f['name'] for f in before}
 for f in before:assert sha(MODS/f['name'])==f['sha256'],'Installed inputs changed'
 for f in unchanged:
  shutil.copy2(MODS/f['name'],retained/f['name']);assert sha(retained/f['name'])==f['sha256']
 assert {p.name for p in retained.iterdir()}=={f['name'] for f in unchanged}
 orders=[('candidate-last',[retained,D/'container']),('candidate-first',[D/'container',retained])]
results=[]
for label,folders in orders:
 dest=V/'independent'/('overlay-'+label)
 env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in folders))
 diagnostic_run('overlay-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,'json',*[relative_package(p) for p in packages]],env)
 assert not read(V/'independent'/('overlay-'+label+'.result.json'))['parser_warnings_or_errors']
 actual={p:read(dest/(relative_package(p)+'.json')) for p in packages}
 assert actual==expected,('Final overlay precedence or body does not match',label)
 results.append({'order':label,'all_five_packages_match':True})
report={'passed':True,'installed':installed,'orders':results,'face_files':[{k:f[k] for k in ['name','bytes','sha256']} for f in face_files],'candidate_files':[{k:f[k] for k in ['name','bytes','sha256']} for f in dual['container_files']],'candidate_skirt_body_and_face_override_semantics_verified':True,'shared_8k_fishnet_atlas_preserved':True,'game_runtime_tested':False}
write(D/('installed-overlay-verification.json' if installed else 'overlay-verification.json'),report)
print('SKIRT_FACE_OVERLAY_MOUNT_VERIFIED',installed,flush=True)
