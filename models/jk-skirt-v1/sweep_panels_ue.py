"""Front/back recovery planes avoid inflating the raised hem circumference."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'diagonal80/selection.json').read_text())
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
for tilt in [.8,1.2]:
 name=f'panels{round(tilt*100)}';sel=copy.deepcopy(base);sel['backstop'].update(normal_mode=2,down_tilt=tilt)
 (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']=name
 out=W/name;out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
 runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
