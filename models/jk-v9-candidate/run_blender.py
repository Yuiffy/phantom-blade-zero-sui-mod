import os,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
for name in sys.argv[1:]:
    script=ROOT/(name+'.py')
    assert script.is_file()
    with (ROOT/(name+'.log')).open('wb') as log:
        r=subprocess.run(['D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe','-b','-t','2','--python-exit-code','1','--python',str(script)],stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',PBZ_FIT_QUICK='0',PBZ_SKIP_AUDIT_RENDER='1'),creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    print(name,r.returncode,flush=True)
    if r.returncode:raise SystemExit(r.returncode)
