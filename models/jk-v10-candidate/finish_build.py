"""Cook and independently verify the final reviewed FBX. Never installs."""
import subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
steps=[['run_blender.py','verify_scope'],['prepare_mod.py'],['run_ue.py','import'],['run_ue.py','cook'],['package_mod.py'],['verify_mod.py','gather'],['verify_mod.py','validate'],['verify_mod.py','skin']]
for file,*args in steps:
 r=subprocess.run([sys.executable,str(ROOT/file),*args]);print('STEP',file,args,r.returncode,flush=True)
 if r.returncode:raise SystemExit(r.returncode)
