"""Bounded low-budget guide candidates; preserve visible mesh and other cloth."""
from pathlib import Path
import unreal,json,os,runpy,copy,hashlib
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1';C=Path(__file__).resolve().parent
L=unreal.PBZModToolsLibrary
m=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
base=json.loads((W/'selection.json').read_text())
cases=json.loads(os.environ.get('JK_CASES','[["coarse128",8,2],["coarse96",8,2],["coarse96",12,2]]'))
for case in cases:
    guide,it,sub=case[:3];changes=case[3] if len(case)>3 else {}
    stage=f'{guide}-{it}x{sub}'+changes.get('suffix','');out=W/stage;out.mkdir(exist_ok=True)
    g=json.loads((W/(guide+'.json')).read_text())
    assert L.tune_cloth_guide(m,'CA_Sui_Skirt_0',json.dumps(g))
    assert L.tune_cloth_mask(m,'CA_Sui_Skirt_0',119,104,40,unreal.load_asset('/HuaShira/Mods/SuiPBZ/Physics/PA_JK_SkirtCollision1'))
    assert L.set_cloth_solver(m,it,sub)==5
    selection=copy.deepcopy(base);selection.update(iterations=it,substeps=sub,simulation_positions=g['positions'],simulation_indices=g['indices'])
    selection['config'].update(changes.get('config',{}))
    assert L.tune_cloth_config(m,'CA_Sui_Skirt_0',json.dumps(selection['config']))
    (out/'selection.json').write_text(json.dumps(selection));(W/'selection.json').write_text(json.dumps(selection))
    target=json.loads((W/'render-target.json').read_text());data=json.loads(L.reproject_cloth_mapping(m,'MI_JK_PleatedSkirt','CA_Sui_Skirt_0',json.dumps(target)))
    data['original_positions']=target['original_positions'];mp=out/'mapping.json';mp.write_text(json.dumps(data))
    (out/'render-settings.json').write_text(json.dumps(dict(render_pin_z=116,mapping_path=str(mp),mapping_sha256=hashlib.sha256(mp.read_bytes()).hexdigest(),render_blend_cap=.65)))
    if os.environ.get('JK_SAVE')=='1':assert unreal.EditorAssetLibrary.save_loaded_asset(m)
    os.environ.update(JK_SKIRT_STAGE=stage,JK_PROFILES=os.environ.get('JK_TEST_PROFILES','jog,crouch'),JK_HZ=os.environ.get('JK_TEST_HZ','30'))
    runpy.run_path(str(C/'test_ue.py'),run_name='__main__')
    unreal.log('JK_COARSE_CASE_COMPLETE '+stage)
if os.environ.get('JK_SAVE')!='1':(W/'selection.json').write_text(json.dumps(base))
