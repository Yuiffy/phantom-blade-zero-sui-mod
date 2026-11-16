"""Rebuild using the documented local v6/v8 checkpoints and tool environment."""
import subprocess,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def run(file,*args):
 subprocess.run([sys.executable,str(ROOT/file),*args],check=True)
run('run_blender.py','export_atlas_provenance')
run('repair_atlas.py')
run('run_blender.py','adjust_v9')
shutil.copy2(ROOT/'sui-jk-hun-bound.blend',ROOT/'sui-jk-v9-core.blend')
run('run_blender.py','refine_ornaments','refresh_texture','audit_bound_model','verify_scope')
run('finish_build.py')
run('verify_texture_chain.py')
