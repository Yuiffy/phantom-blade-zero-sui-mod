import unreal,json,hashlib
from pathlib import Path
CODE=Path(__file__).resolve().parent;R=CODE.parents[1]/'private/jirai-skirt-shape-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=R/'variant'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
assert mesh.skeleton.get_path_name()=='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton.Hun_Skin_Skeleton'
count=len(json.loads((R/'cloth-spec.json').read_text()))
for name,steps,dt,travel in [('60hz',300,1/60,15),('30hz',180,1/30,25),('foreaft',360,1/60,-20)]:
 result=unreal.PBZModToolsLibrary.test_cloth_motion(mesh,steps,dt,travel)
 assert not result.startswith('ERROR'),result
 data=json.loads(result)
 data['fbx_sha256']=hashlib.sha256((R/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest()
 (W/('simulation-'+name+'.json')).write_text(json.dumps(data))
 assert data['simulation_instances']>0
 assert all(len(f['assets'])==count for f in data['frames']),(name,[(f['step'],len(f['assets'])) for f in data['frames']])
unreal.log('SUI_CLOTH_TEST_OK')
