"""Use the R6 import, animation, cloth and independent readback gates."""
from common import *
import subprocess

steps = [['prepare_mod.py'],['prepare_shoulder_animation.py'],['run_ue.py','import'],
    ['prepare_shoulder_skeleton.py'],['run_ue.py','shoulder'],['run_ue.py','cloth'],
    ['run_ue.py','editorcheck'],['run_ue.py','test'],['run_ue.py','articulation'],
    ['validate_simulation.py'],['verify_shoulder_skeleton.py'],['run_ue.py','cook'],
    ['package_mod.py'],['verify_mod.py','gather'],['verify_mod.py','body'],
    ['verify_mod.py','validate'],['decode_cloth_body.py'],['verify_cloth_assets.py'],
    ['deform_readback.py','60hz'],['deform_readback.py','30hz'],['deform_readback.py','foreaft']]
if len(sys.argv)>1:
    assert sys.argv[1]=='--from' and len(sys.argv)==3
    requested=sys.argv[2].split(':')
    steps=steps[next(i for i,s in enumerate(steps) if s[:len(requested)]==requested):]
for name,*args in steps:
    print('OFFLINE_STAGE',name,*args,flush=True)
    result = subprocess.run([sys.executable,str(CODE/name),*args],capture_output=True,
        creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    (ROOT/'logs'/('stage-'+name.removesuffix('.py')+('-'+'-'.join(args) if args else '')+'.log')).write_bytes(result.stdout+result.stderr)
    if result.returncode:
        print((result.stdout+result.stderr).decode('utf8',errors='replace')[-3000:],flush=True)
        raise SystemExit(result.returncode)
print('SKIN_EYES_CANDIDATE_BUILT_NOT_INSTALLED',flush=True)
