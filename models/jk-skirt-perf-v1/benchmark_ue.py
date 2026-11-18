"""Matched sequential cost comparison, no game process or rendering."""
from pathlib import Path
import unreal, json, os, runpy, copy

W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1'
C=Path(__file__).resolve().parent
L=unreal.PBZModToolsLibrary
m=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
base=json.loads((W/'selection.json').read_text())
cases=[('cost8x2-a',8,2),('cost32x8',32,8),('cost8x2-b',8,2)]
os.environ.update(JK_PROFILES='jog',JK_HZ='60',JK_STEPS='241')
for stage,it,sub in cases:
    selection=copy.deepcopy(base);selection.update(iterations=it,substeps=sub)
    folder=W/stage;folder.mkdir(exist_ok=True)
    (folder/'selection.json').write_text(json.dumps(selection))
    (W/'selection.json').write_text(json.dumps(selection))
    assert L.set_cloth_solver(m,it,sub)==5
    os.environ['JK_SKIRT_STAGE']=stage
    runpy.run_path(str(C/'test_ue.py'),run_name='__main__')
    unreal.log('JK_COST_CASE_COMPLETE '+stage)
# Do not save benchmark config changes to the author mesh.
(W/'selection.json').write_text(json.dumps(base))
