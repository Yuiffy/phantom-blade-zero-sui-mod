"""Require unchanged R7 geometry, skin weights and bone references after cook."""
import json,hashlib
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-recovery-v1';V=W/'variant';B=R/'private/jirai-skirt-v1';I=V/'independent'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
for name in ['Sui_Jirai_Hun_Body.fbx','sui-jirai-motion.blend','source-render-contract.json']:
 assert sha(W/name)==sha(B/name),('Authored geometry or source weights changed',name)
new=np.load(I/'render-data.npz');old=np.load(B/'variant/independent/render-data.npz')
for name in ['positions','indices']:assert np.array_equal(new[name],old[name]),('Cooked geometry changed',name)
assert read(I/'render-weights.json')==read(B/'variant/independent/render-weights.json')
assert read(V/'import-report.json')['actual_reference_bones']==read(B/'variant/import-report.json')['actual_reference_bones']
a=read(V/'cloth-details.json');b=read(B/'variant/cloth-details.json')
for old_asset,new_asset in zip(b['assets'],a['assets']):
 assert {k:v for k,v in old_asset.items() if k!='config'}=={k:v for k,v in new_asset.items() if k!='config'}
 if not old_asset['name'].startswith('CA_Jirai_Skirt'):assert old_asset==new_asset,'Hair simulation config changed'
# The marker test evaluates retargeted bone translations, not cloth. Reuse it
# only after requiring the complete native skeleton and mesh references exact.
native=V/'shoulder-rig/native';source=B/'variant/shoulder-rig/native'
files=sorted(p for p in native.rglob('*') if p.is_file());assert files
for p in files:assert sha(p)==sha(source/p.relative_to(native)),('Retarget skeleton changed',p)
marker_source=B/'variant/ik-marker-verification.json';marker=read(marker_source)
assert marker['passed'] and len(marker['markers'])==5
marker['reuse_provenance']={'source':str(marker_source),'sha256':sha(marker_source),'native_skeleton_exact_r7':True,'mesh_reference_exact_r7':True,'scope':'retargeted marker translations only; no cloth stability claim'}
(V/'ik-marker-verification.json').write_text(json.dumps(marker,indent=2))
report={'passed':True,'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'source_geometry_weights_and_continuous_shorts_exact_r7':True,'cooked_positions_indices_and_skin_weights_exact_r7':True,'bone_reference_exact_r7':True,'hair_physical_mesh_and_config_exact_r7':True,'skirt_physical_cage_positions_weights_and_guid_exact_r7':True,'changed_scope':['skirt config','two skirt-only capsule radii','skirt render blend cap'],'game_runtime_tested':False}
(V/'inheritance-verification.json').write_text(json.dumps(report,indent=2));print('R7_GEOMETRY_SHORTS_RIG_HAIR_PRESERVED')
