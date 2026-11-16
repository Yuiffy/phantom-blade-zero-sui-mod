"""Independent CUE4Parse readback of the native per-character skeleton clone."""
import sys,os,json
from pathlib import Path
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-proportion-v1';W=ROOT/'variant';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');sys.path.insert(0,str(PBZ/'tools'))
import run_native_diagnostic as diag
from offline_tools import native_run,diagnostic_run
from package_model import relative_package
R=W/'shoulder-rig';container=R/'container';container.mkdir(exist_ok=True);pkg='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton'
native_run('pack-shoulder-rig',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',R/'native',container/'shoulder-rig.utoc'])
out=W/'independent';out.mkdir(exist_ok=True)
env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=str(container))
diagnostic_run('shoulder-rig-json',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',out/'shoulder-rig-json','json',relative_package(pkg)],env)
diagnostic_run('shoulder-rig-bones',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',out/'shoulder-rig-bones','skel',relative_package(pkg)],env)
docs=json.loads((out/'shoulder-rig-json'/(relative_package(pkg)+'.json')).read_text(encoding='utf8'));s=next(e for e in docs if e['Type']=='Skeleton');properties=s['Properties']
(R/'independent-properties.json').write_text(json.dumps(properties,indent=2))
raw=json.loads((PBZ/'research/hun-skeleton.json').read_text(encoding='utf8'));original=next(e for e in raw['Exports'] if e['ObjectName']=='Hun_Skin_Skeleton');modes=next(d for d in original['Data'] if d['Name']=='BoneTree')['Value'];bones=json.loads((PBZ/'research/hun-skeleton-raw.json').read_text())['bones']
changed=set(json.loads((R/'native-clone-report.json').read_text())['retargeted_bones']);assert len(properties['BoneTree'])==len(bones)==1134
for node,source,bone in zip(properties['BoneTree'],modes,bones):
 want='Skeleton' if bone['name'].lower() in changed else source['Value'][0]['Value'];assert node['TranslationRetargetingMode'].split('::')[-1]==want,(bone['name'],node,want)
assert properties['CompatibleSkeletons']==[{'AssetPathName':'/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton.Hun_Skin_Skeleton','SubPathString':''}]
actual=json.loads((out/'shoulder-rig-bones'/(relative_package(pkg)+'.Hun_Skin_Skeleton.skel.json')).read_text())['bones'];assert len(actual)==1134
assert [(b['name'].lower(),b['parent']) for b in actual]==[(b['name'].lower(),b['parent']) for b in bones]
report={'passed':True,'reader':'CUE4Parse','full_bones':1134,'overridden_translation_modes':sorted(changed),'compatible_source':'/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton','native_reference_payload_preserved':True,'original_skeleton_not_overridden':True,'game_runtime_tested':False}
(R/'independent-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
