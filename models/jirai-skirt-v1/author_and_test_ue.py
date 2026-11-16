"""One author process; save/reload verification still runs in a fresh process."""
from pathlib import Path
import runpy,json,hashlib
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-v1'
for script in ['author_cloth_ue.py','test_cloth_ue.py','test_articulation_ue.py']:
 runpy.run_path(str(C/script),run_name='__main__')
inputs=[W/'Sui_Jirai_Hun_Body.fbx',W/'cloth-spec.json',W/'pose-contract.json',W/'source-render-contract.json',W/'variant/ue/ProjectPBZ/Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll']+[C/n for n in ['author_cloth_ue.py','test_cloth_ue.py','test_articulation_ue.py']]
outputs=[W/'variant'/('simulation-'+n+'.json') for n in ['60hz','30hz','foreaft']]+[W/'variant'/('articulation-'+n+'.json') for n in json.loads((W/'pose-contract.json').read_text())['clips']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(W/'variant/combined-tests.json').write_text(json.dumps({'inputs':{str(p):sha(p) for p in inputs},'outputs':{str(p):sha(p) for p in outputs}},indent=2))
