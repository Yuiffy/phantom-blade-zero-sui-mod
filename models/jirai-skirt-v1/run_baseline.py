"""Read the installed R6 author mesh without saving asset changes."""
from pathlib import Path
import subprocess,os,shutil
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-v1';O=W/'baseline';B=R/'private/jirai-detail-v1/variant';O.mkdir(exist_ok=True)
for n in ['import-report.json','source-spec.json']:shutil.copy2(B/n,O/n)
cmd=['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe',str(B/'ue/ProjectPBZ/ProjectPBZ.uproject'),'-unattended','-nop4','-stdout','-onethread','-run=pythonscript','-script='+str(C/'test_articulation_ue.py'),'-NullRHI','-NoShaderCompile','-NoShaderWorker']
with (O/'test.log').open('wb') as f:p=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env=dict(os.environ,PBZ_BASELINE='1'),creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
print('BASELINE_TEST',p.returncode);raise SystemExit(p.returncode)
