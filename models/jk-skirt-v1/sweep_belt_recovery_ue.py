"""Recovery drive and local backstop after adding invisible suspension length."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'belt120/selection.json').read_text())
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
for name,drive,backstop in [('belt-drive90',.9,None),('belt-drive100',1.,None),('belt-local-backstop',.5,{'distance':3.,'radius':8.})]:
 sel=copy.deepcopy(base);sel['config']['AnimDriveStiffness']={'Low':drive,'High':drive}
 if backstop:sel['backstop']=backstop
 (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']=name
 out=W/name;out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
 runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
