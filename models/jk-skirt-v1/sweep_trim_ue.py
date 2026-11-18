"""Filter JK-specific upper capsule placement against the lower skirt waist."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'candidate2/selection.json').read_text())
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
for top,backstop in [(90,False),(94,False),(98,False),(94,True)]:
 name='trim'+str(top)+('-backstop' if backstop else '');sel=copy.deepcopy(base);sel.update(iterations=24,substeps=6)
 sel['capsules']=[[bone,[side*(9.3+(107-top)*3.4/27),-5.5,top],[side*13.5,-5.5,70],10.5] for bone,side in [('thigh_l',1),('thigh_r',-1)]]
 sel['config'].update(bUseSelfCollisions=False,GravityScale=1.2,bUseLegacyBackstop=False)
 if backstop:sel['backstop']={'distance':3.,'radius':60.}
 (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']=name
 out=W/name;out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
 runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
