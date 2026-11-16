"""Freeze a passing renderer/physics combination; no installation."""
from pathlib import Path
import json,hashlib
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-recovery-v1';V=W/'variant'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
evaluation=read(V/'sweep/recovery-evaluation.json');preset='firm-compact';cap=.4
rows=[r for r in evaluation['records'] if r['preset']==preset]
assert len(rows)==6 and all(r['passed'] for r in rows)
assert evaluation['predicted_quantized_render_blend_cap']==cap
spec=read(W/'cloth-spec.json');row=next(r for r in spec if r['slot']=='MI_Jirai_Skirt')
row['config']=read(V/'sweep'/(preset+'-config.json'));row['render_pin_plane']['max_simulated_blend']=cap
(W/'cloth-spec.json').write_text(json.dumps(spec,indent=2))
collision=V/'sweep'/(preset+'-collision.json')
assert collision.read_bytes()==(V/'skirt-collision-spec.json').read_bytes(),'Copy the selected collision JSON byte-for-byte before freezing'
selection={'preset':preset,'max_simulated_blend':cap,'evaluation_sha256':sha(V/'sweep/recovery-evaluation.json'),'collision_spec_sha256':sha(collision),'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'cloth_spec_sha256':sha(W/'cloth-spec.json'),'game_runtime_tested':False}
(W/'selection.json').write_text(json.dumps(selection,indent=2));print('RECOVERY_SELECTION_FROZEN')
