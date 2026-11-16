import unreal,json
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
for name,steps,dt,travel in [('60hz',300,1/60,15),('30hz',180,1/30,25),('foreaft',360,1/60,-20)]:
 result=unreal.PBZModToolsLibrary.test_cloth_motion(mesh,steps,dt,travel)
 assert not result.startswith('ERROR'),result
 data=json.loads(result)
 (W/('simulation-'+name+'.json')).write_text(json.dumps(data))
 assert data['simulation_instances']>0
 assert all(len(f['assets'])==5 for f in data['frames']),(name,[(f['step'],len(f['assets'])) for f in data['frames']])
unreal.log('SUI_CLOTH_TEST_OK')
