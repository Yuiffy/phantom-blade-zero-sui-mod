import sys,subprocess,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];sys.path.insert(0,str(PBZ/'tools'))
from ue_pipeline import game_pids
from offline_tools import isolated
isolated()
WORK=PBZ/'variants/new-jk-v11';PROJECT=WORK/'ue/ProjectPBZ/ProjectPBZ.uproject';stage=sys.argv[1]
cmd=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',str(PROJECT),'-unattended','-nop4','-stdout','-FullStdOutLogOutput','-onethread']
if stage=='import':cmd+=['-run=pythonscript','-script='+str(ROOT/'import_mod_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='cook':
    assert (WORK/'import-report.json').exists();cmd+=['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps']
else:raise ValueError(stage)
logs=WORK/'logs';logs.mkdir(parents=True,exist_ok=True)
with (logs/(stage+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
(logs/(stage+'-exit.json')).write_text(json.dumps({'exit_code':r.returncode,'command':cmd},indent=2),encoding='utf8')
print(stage,r.returncode);raise SystemExit(r.returncode)
