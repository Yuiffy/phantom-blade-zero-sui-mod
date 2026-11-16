"""Sequential isolated build; no install, no game process operations."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
steps=[['run_blender.py','reconstruct_source_map','adjust_v8','audit_bound_model','verify_scope'],
       ['prepare_mod.py'],['run_ue.py','import'],['run_ue.py','cook'],
       ['package_mod.py'],['verify_mod.py','gather'],['verify_mod.py','validate'],['verify_mod.py','skin']]
for file,*args in steps:
    result=subprocess.run([sys.executable,str(ROOT/file),*args])
    print('STEP',file,args,result.returncode,flush=True)
    if result.returncode:raise SystemExit(result.returncode)
