"""Rebind the changed skirt and solve every test afresh with the corrected helper."""
from pathlib import Path
import runpy,json,hashlib,os
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-shape-v1';V=W/'variant'
os.environ.pop('PBZ_REUSE_RECOVERY_SWEEP',None)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for script in ['author_cloth_ue.py','test_cloth_ue.py','test_articulation_ue.py']:
 runpy.run_path(str(C/script),run_name='__main__')
inputs=[W/'Sui_Jirai_Hun_Body.fbx',W/'cloth-spec.json',W/'pose-contract.json',W/'source-render-contract.json',W/'selection.json',V/'skirt-collision-spec.json',V/'ue/ProjectPBZ/Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll']+[C/n for n in ['author_cloth_ue.py','author_and_test_ue.py','test_cloth_ue.py','test_articulation_ue.py']]+list(W.glob('component-*.json'))
outputs=[V/('simulation-'+n+'.json') for n in ['60hz','30hz','foreaft']]+[V/('articulation-'+n+'.json') for n in json.loads((W/'pose-contract.json').read_text())['clips']]+[V/f'articulation-{n}-60hz.json' for n in ['walk-recover','jog-recover','crouch-recover']]
assert sha(V/'ue/ProjectPBZ/Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll')==json.loads((W/'editor-tools-build.json').read_text())['dll_sha256']
for p in outputs:
 d=json.loads(p.read_text());assert all(f.get('simulated_teleport_mode')==0 for f in d['frames'])
(V/'combined-tests.json').write_text(json.dumps({'inputs':{str(p):sha(p) for p in inputs},'outputs':{str(p):sha(p) for p in outputs}},indent=2))
print('RESHAPED_SKIRT_FRESH_CONTINUOUS_TESTS_SAVED')
