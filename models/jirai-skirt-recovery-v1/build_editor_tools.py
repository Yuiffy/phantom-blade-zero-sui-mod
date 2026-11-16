"""Build this revision's isolated editor helpers with one low priority action."""
import subprocess,os,json,shutil,hashlib
from pathlib import Path
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-recovery-v1'
host=W/'pose-tools-host';ue=Path('F:/FTools/UE57/UE_5.7/Engine')
plugin=host/'Plugins/PBZModTools'
for src in (C/'editor-tools/PBZModTools').rglob('*'):
 if src.is_file():
  dst=plugin/src.relative_to(C/'editor-tools/PBZModTools');dst.parent.mkdir(parents=True,exist_ok=True)
  if not dst.exists() or dst.read_bytes()!=src.read_bytes():shutil.copy2(src,dst)
host.mkdir(parents=True,exist_ok=True)
(host/'ClothTools.uproject').write_text(json.dumps({'FileVersion':3,'EngineAssociation':'5.7','Plugins':[{'Name':'PBZModTools','Enabled':True}]}))
cmd=[str(ue/'Binaries/ThirdParty/DotNet/8.0.412/win-x64/dotnet.exe'),str(ue/'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll'),'UnrealEditor','Win64','Development','-Project='+str(host/'ClothTools.uproject'),'-Plugin='+str(host/'Plugins/PBZModTools/PBZModTools.uplugin'),'-NoUBTMakefiles','-NoHotReload','-MaxParallelActions=1','-NoUBA','-NoXGE','-NoFASTBuild','-NoSNDBS']
with (W/'editor-tools-build.log').open('wb') as f:
 result=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',OMP_NUM_THREADS='1',DOTNET_GCHeapHardLimit='C0000000'),creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
if result.returncode==0:
 dll=plugin/'Binaries/Win64/UnrealEditor-PBZModTools.dll'
 (W/'editor-tools-build.json').write_text(json.dumps(dict(exit_code=0,dll_sha256=hashlib.sha256(dll.read_bytes()).hexdigest(),single_action=True,priority='BelowNormal'),indent=2))
print('ISOLATED_EDITOR_TOOLS',result.returncode);raise SystemExit(result.returncode)
