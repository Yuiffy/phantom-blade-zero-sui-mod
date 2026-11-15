"""Prepare a separate UE experiment from the frozen static v11 candidate."""
from pathlib import Path
import json, shutil, hashlib
R=Path(__file__).resolve().parent; STATIC=R.parent/'tripo-refine-v11'; PBZ=R.parents[2]
W=PBZ/'variants/jk-motion-v1'; PROJECT=W/'ue/ProjectPBZ'
base=PBZ/'variants/new-jk-v11/ue/ProjectPBZ'
for rel in ['ProjectPBZ.uproject','Config/DefaultEngine.ini','Config/DefaultGame.ini','Plugins/HuaShira/HuaShira.uplugin']+['Plugins/HuaShira/Content/Characters/Hero/Hero_Hun/'+s for s in ['Hun_Skin_Skeleton.uasset','PA_Hun.uasset','Rig/ABP_Hun_PostProcess.uasset']]:
 p=PROJECT/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/rel,p)
d=json.loads((PROJECT/'ProjectPBZ.uproject').read_text())
for p in d['Plugins']:
 if p['Name']=='PBZModTools':p['Enabled']=True
if not any(p['Name']=='ChaosCloth' for p in d['Plugins']):d['Plugins'].append({'Name':'ChaosCloth','Enabled':True})
(PROJECT/'ProjectPBZ.uproject').write_text(json.dumps(d,indent=2))
for fn in ['material-spec.json']:
 d=json.loads((PBZ/'variants/new-jk-v11'/fn).read_text());(W/fn).write_text(json.dumps(d,indent=2))
source=json.loads((PBZ/'variants/new-jk-v11/source-spec.json').read_text());draft=json.loads((R/'source-preparation.json').read_text())
source.update(source_root=str(R),fbx=str(R/'Sui_JK_Hun_Body_Motion.fbx'),fbx_sha256=hashlib.sha256((R/'Sui_JK_Hun_Body_Motion.fbx').read_bytes()).hexdigest(),expected_triangles=69041+sum(c['triangles'] for c in draft['simulation_cages']))
(W/'source-spec.json').write_text(json.dumps(source,indent=2))
s=(STATIC/'import_mod_ue.py').read_text().replace("variants/new-jk-v11","variants/jk-motion-v1")
s=s.replace("path=source['body_package']", "\nfor sim in "+repr([c['slot'] for c in draft['simulation_cages']])+": materials[sim]=materials['MI_JK_Ponytail']\npath=source['body_package']")
(R/'import_mod_ue.py').write_text(s)
spec=json.loads((R/'cloth-spec-draft.json').read_text())
for row in spec:
 row['config']['LinearVelocityScale']={'X':.55,'Y':.55,'Z':.55}
 if row['name']=='CA_Sui_Charm':
  row['mask'].update(bend_soft_z=142.3,bend_stiff_z=139)
  row['config']['BendingStiffnessWeighted']={'Low':.06,'High':.99}
(R/'cloth-spec.json').write_text(json.dumps(spec,indent=2))
print(json.dumps({'project':str(PROJECT),'import_triangles':source['expected_triangles'],'visible_triangles':69041}))
