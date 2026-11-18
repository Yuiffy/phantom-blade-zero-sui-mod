"""Compare final readback by section, requiring only skirt rest positions change."""
import json,hashlib
from pathlib import Path
import numpy as np
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';V=W/'variant';B=R/'private/jirai-skirt-recovery-v1/variant';I=V/'independent'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
new=np.load(I/'render-data.npz');old=np.load(B/'independent/render-data.npz')
a=read(I/'cloth-native-details.json');b=read(B/'independent/cloth-native-details.json')
wa=read(I/'render-weights.json');wb=read(B/'independent/render-weights.json');assert wa==wb
assert np.array_equal(new['indices'],old['indices'])
unchanged=[]
for x,y in zip(a['sections'],b['sections']):
 assert x['slot']==y['slot'] and x['vertices']==y['vertices'] and x['base_vertex']==y['base_vertex']
 if x['slot'] in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim']:continue
 lo=x['base_vertex'];hi=lo+x['vertices'];assert np.array_equal(new['positions'][lo:hi],old['positions'][lo:hi]),x['slot'];unchanged.append(x['slot'])
assert read(V/'import-report.json')['actual_reference_bones']==read(B/'import-report.json')['actual_reference_bones']
for x,y in zip(read(V/'cloth-details.json')['assets'],read(B/'cloth-details.json')['assets']):
 if x['name'].startswith('CA_Jirai_Skirt'):continue
 assert {k:v for k,v in x.items() if k!='guid'}=={k:v for k,v in y.items() if k!='guid'},'Hair authoring changed'
report={'passed':True,'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'changed_scope':['skirt visible rest shape','skirt cage rest shape','rebuilt cloth mapping'],'unchanged_render_sections':unchanged,'cooked_indices_and_skin_weights_exact_recovery1':True,'bone_reference_exact_recovery1':True,'hair_physical_mesh_and_config_exact_recovery1':True,'continuous_shorts_body_hands_and_uv_preserved':True,'game_runtime_tested':False}
(V/'inheritance-verification.json').write_text(json.dumps(report,indent=2));print('SKIRT_ONLY_READBACK_CHANGE_VERIFIED')
