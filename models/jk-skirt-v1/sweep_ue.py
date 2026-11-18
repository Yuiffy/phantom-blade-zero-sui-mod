"""Isolated skirt-only filtering; selected settings require fresh full-mesh tests."""
from pathlib import Path
import unreal,json,os,runpy,copy
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jk-skirt-v1'
base=json.loads((W/'selection.json').read_text());(W/'candidate2/selection.json').write_text(json.dumps(base,indent=2))
presets={
 'recover':dict(drive=.5,bend=.55,gravity=1.2,self_collisions=False),
 'recover-soft':dict(drive=.5,bend=.35,gravity=1.2,self_collisions=False),
 'recover-strong':dict(drive=.7,bend=.55,gravity=1.5,self_collisions=False),
 'recover-self':dict(drive=.45,bend=.55,gravity=1.2,self_collisions=True),
}
os.environ.update(PBZ_SKIRT_ONLY='1',JK_PROFILES='jog,crouch',JK_HZ='60')
try:
 for name,preset in presets.items():
  sel=copy.deepcopy(base);sel.update(radius=9.5,lower_radius=10.8,iterations=24,substeps=6)
  sel['config'].update(AnimDriveStiffness={'Low':preset['drive'],'High':preset['drive']},AnimDriveDamping={'Low':.85,'High':.85},BendingStiffnessWeighted={'Low':preset['bend'],'High':preset['bend']},GravityScale=preset['gravity'],bUseSelfCollisions=preset['self_collisions'])
  (W/'selection.json').write_text(json.dumps(sel,indent=2));os.environ['JK_SKIRT_STAGE']='sweep-'+name
  out=W/('sweep-'+name);out.mkdir(exist_ok=True);(out/'selection.json').write_text(json.dumps(sel,indent=2))
  runpy.run_path(str(C/'author_ue.py'),run_name='__main__')
finally:(W/'selection.json').write_text(json.dumps(base,indent=2))
