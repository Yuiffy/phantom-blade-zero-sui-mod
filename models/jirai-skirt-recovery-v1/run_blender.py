"""Run this candidate's Blender stages with fixed resource limits."""
import os,sys,subprocess
from pathlib import Path
CODE=Path(__file__).resolve().parent
ROOT=CODE.parents[1]/'private/jirai-skirt-recovery-v1'
for name in sys.argv[1:]:
 script=CODE/(name+'.py');assert script.is_file()
 with (ROOT/(name+('-baseline' if os.environ.get('PBZ_BASELINE')=='1' else '')+'.log')).open('wb') as log:
  result=subprocess.run(['D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe','-b','-t','2','--python-exit-code','1','--python',str(script)],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',PBZ_SKIP_AUDIT_RENDER='1'),creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 print(name,result.returncode,flush=True)
 if result.returncode:raise SystemExit(result.returncode)
