"""Build editor-only cloth helpers in an isolated host at one action at a time."""
import subprocess,os,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2]
HOST=Path('F:/FTools/pbz-cloth-tools/host');HOST.mkdir(parents=True,exist_ok=True)
src=PBZ/'ue/ProjectPBZ/Plugins/PBZModTools';dst=HOST/'Plugins/PBZModTools'
if not dst.exists():shutil.copytree(src,dst)
project=HOST/'ClothTools.uproject'
project.write_text(json.dumps({'FileVersion':3,'EngineAssociation':'5.7','Plugins':[{'Name':'PBZModTools','Enabled':True}]}))
UE=Path('F:/FTools/UE57/UE_5.7/Engine')
cmd=[str(UE/'Binaries/ThirdParty/DotNet/8.0.412/win-x64/dotnet.exe'),str(UE/'Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll'),'UnrealEditor','Win64','Development','-Project='+str(project),'-Plugin='+str(dst/'PBZModTools.uplugin'),'-NoUBTMakefiles','-NoHotReload','-MaxParallelActions=1','-NoUBA','-NoXGE','-NoFASTBuild','-NoSNDBS','-Verbose']
log=ROOT/'editor-tools-build.log'
with log.open('wb') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,DOTNET_PROCESSOR_COUNT='2',OMP_NUM_THREADS='1',DOTNET_GCHeapHardLimit='C0000000'),timeout=1200,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
(ROOT/'editor-tools-build.json').write_text(json.dumps({'exit_code':p.returncode,'host':str(HOST),'log':str(log),'one_action':True,'priority':'BelowNormal'},indent=2));print('EDITOR_TOOLS',p.returncode);raise SystemExit(p.returncode)
