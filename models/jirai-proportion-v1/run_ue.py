import sys,subprocess,json
from pathlib import Path
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-proportion-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');sys.path.insert(0,str(PBZ/'tools'))
from ue_pipeline import game_pids
from offline_tools import isolated
isolated()
WORK=ROOT/'variant';PROJECT=WORK/'ue/ProjectPBZ/ProjectPBZ.uproject';stage=sys.argv[1]
cmd=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',str(PROJECT),'-unattended','-nop4','-stdout','-FullStdOutLogOutput','-onethread']
if stage=='import':cmd+=['-run=pythonscript','-script='+str(CODE/'import_mod_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage in ['cloth','test']:
    cmd+=['-run=pythonscript','-script='+str(CODE/('author_cloth_ue.py' if stage=='cloth' else 'test_cloth_ue.py')),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='retarget':
    cmd+=['-run=pythonscript','-script='+str(CODE/'probe_retarget_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='shoulder':
    cmd+=['-run=pythonscript','-script='+str(CODE/'test_shoulder_retarget_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='editorcheck':
    cmd+=['-run=pythonscript','-script='+str(CODE/'verify_editor_state_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='solver':
    cmd+=['-run=pythonscript','-script='+str(CODE/'tune_solver_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
elif stage=='cook':
    assert (WORK/'import-report.json').exists();cmd+=['-run=Cook','-TargetPlatform=Windows','-NoDefaultMaps']
else:raise ValueError(stage)
logs=WORK/'logs';logs.mkdir(parents=True,exist_ok=True)
with (logs/(stage+'.log')).open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
(logs/(stage+'-exit.json')).write_text(json.dumps({'exit_code':r.returncode,'command':cmd},indent=2),encoding='utf8')
print(stage,r.returncode);raise SystemExit(r.returncode)
