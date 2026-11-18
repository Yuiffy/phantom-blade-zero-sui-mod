"""Full matched low-cost quality solve using the existing delivered guide."""
from pathlib import Path
import unreal,json,os,runpy,copy
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1'
C=Path(__file__).resolve().parent
L=unreal.PBZModToolsLibrary
m=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
base=json.loads((W/'selection.json').read_text())
for stage,it,sub,bend in [('low8x2',8,2,None)]:
    selection=copy.deepcopy(base);selection.update(iterations=it,substeps=sub)
    folder=W/stage;folder.mkdir(exist_ok=True)
    (folder/'selection.json').write_text(json.dumps(selection))
    (folder/'render-settings.json').write_bytes((W.parent/'jk-skirt-v1/delivery/render-settings.json').read_bytes())
    (W/'selection.json').write_text(json.dumps(selection))
    assert L.set_cloth_solver(m,it,sub)==5
    os.environ.update(JK_SKIRT_STAGE=stage,JK_PROFILES='walk,jog,crouch',JK_HZ='30,60')
    runpy.run_path(str(C/'test_ue.py'),run_name='__main__')
(W/'selection.json').write_text(json.dumps(base))
