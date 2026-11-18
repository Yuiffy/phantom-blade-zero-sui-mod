"""Ordered offline build only. Does not install, launch a game or open windows."""
import subprocess,sys
from pathlib import Path
C=Path(__file__).resolve().parent
steps=[
 ['prepare_shoulder_animation.py'],['run_ue.py','import'],['run_ue.py','shoulder'],
 ['run_ue.py','cloth'],['run_ue.py','editorcheck'],
 ['validate_simulation.py'],['verify_shoulder_skeleton.py'],['run_ue.py','cook'],
 ['package_mod.py'],['verify_mod.py','gather'],['verify_mod.py','body'],
 ['verify_mod.py','validate'],['decode_cloth_body.py'],['verify_cloth_assets.py'],
 ['deform_readback.py','60hz'],['deform_readback.py','30hz'],['deform_readback.py','foreaft'],
 ['validate_articulation.py'],['reconstruct_articulation.py'],['evaluate_recovery.py','--final'],
 ['verify_inheritance.py'],['verify_eyes.py']]
if len(sys.argv)>1:
 assert sys.argv[1]=='--from' and len(sys.argv)==3
 start=next(i for i,s in enumerate(steps) if s[0]==sys.argv[2]);steps=steps[start:]
logs=C.parents[1]/'private/jirai-skirt-shape-v1/variant/logs'
logs.mkdir(parents=True,exist_ok=True)
for name,*args in steps:
 print('OFFLINE_STAGE',name,*args,flush=True)
 p=subprocess.run([sys.executable,str(C/name),*args],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
 (logs/('stage-'+name.removesuffix('.py')+('-'+'-'.join(args) if args else '')+'.log')).write_bytes(p.stdout)
 if p.returncode:
  print(p.stdout.decode('utf8',errors='replace')[-3500:],flush=True);raise SystemExit(p.returncode)
print('OFFLINE_CANDIDATE_BUILT_NOT_INSTALLED',flush=True)
