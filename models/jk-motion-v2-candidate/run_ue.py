import subprocess,sys,json,os
from pathlib import Path
R=Path(__file__).resolve().parent;PBZ=R.parents[2];W=PBZ/'variants/jk-motion-v2';stage=sys.argv[1]
assert stage in ['import','cloth','test','cook']
HOST=Path('F:/FTools/pbz-cloth-tools/host/Plugins/PBZModTools')
dest=W/'ue/ProjectPBZ/Plugins/PBZModTools'
if stage in ['import','cloth','test','cook']:
 import shutil
 shutil.copytree(HOST,dest,dirs_exist_ok=True,ignore=shutil.ignore_patterns('Intermediate'))
cmd=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',str(W/'ue/ProjectPBZ/ProjectPBZ.uproject'),'-unattended','-nop4','-stdout','-FullStdOutLogOutput','-onethread']
if stage=='cook':cmd+=['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps']
else:cmd+=['-run=pythonscript','-script='+str(R/({'import':'import_mod_ue.py','cloth':'author_cloth_ue.py','test':'test_cloth_ue.py'}[stage])),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
logs=W/'logs';logs.mkdir(parents=True,exist_ok=True)
with (logs/(stage+'.log')).open('wb') as f:
 p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS,env=dict(os.environ,OMP_NUM_THREADS='1',DOTNET_PROCESSOR_COUNT='2'))
(logs/(stage+'-exit.json')).write_text(json.dumps({'exit_code':p.returncode,'command':cmd},indent=2))
if p.returncode==0 and stage!='cook':
 marker={'import':'SUI_JK_IMPORT_OK','cloth':'SUI_CLOTH_AUTHOR_OK','test':'SUI_CLOTH_TEST_OK'}[stage]
 assert marker in (logs/(stage+'.log')).read_text(errors='replace'),('missing completion marker',stage)
print(stage,p.returncode);raise SystemExit(p.returncode)
