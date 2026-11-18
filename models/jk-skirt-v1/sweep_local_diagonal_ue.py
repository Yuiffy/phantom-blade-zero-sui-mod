"""Limit inversion near the reference surface, free the raised hem farther away."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'diagonal80/selection.json').read_text())
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
for tilt,radius,distance in [(.8,10,1.5),(.8,20,2),(.6,10,2)]:
 name=f'localdiag{round(tilt*100)}-r{radius}';sel=copy.deepcopy(base);sel['backstop'].update(radius=float(radius),distance=float(distance),down_tilt=tilt)
 (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']=name
 out=W/name;out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
 runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
