"""Offline rebuild from v9 + authored sleeve provenance. No installation."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
steps=[['run_blender.py','adjust_v10'],['repair_atlas_v10.py'],['run_blender.py','refresh_texture','audit_bound_model','verify_scope']]
for args in steps:
 p=subprocess.run([sys.executable,str(R/args[0]),*args[1:]])
 if p.returncode:raise SystemExit(p.returncode)
