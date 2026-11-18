"""More hidden suspension length, retaining the original visible waist and hem."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'diagonal80/selection.json').read_text());positions=json.loads((W/'baseline-cloth.json').read_text())['assets'][2]['positions']
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
for belt,backstop in [(120,False),(120,True),(125,True)]:
 name=f'belt{belt}'+('-recover' if backstop else '');sel=copy.deepcopy(base);sel.pop('backstop',None)
 sel.update(pin_z=belt-1,full_z=104,render_pin_z=106,simulation_positions=[[x,y,belt if z>112 else z] for x,y,z in positions])
 if backstop:sel['backstop']={'distance':1.5,'radius':60.,'radial':True,'down_tilt':.8}
 (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']=name
 out=W/name;out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
 runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
