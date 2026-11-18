from pathlib import Path
import unreal,json
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-v1'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
L=unreal.PBZModToolsLibrary
target=(W/'render-target.json')
result=L.reproject_cloth_mapping(mesh,'MI_JK_PleatedSkirt','CA_Sui_Skirt_0',target.read_text() if target.exists() else '')
assert not result.startswith('ERROR'),result
data=json.loads(result);assert len(data['mapping'])==1531
if target.exists():data['original_positions']=json.loads(target.read_text())['original_positions']
(W/'reprojected-mapping.json').write_text(json.dumps(data))
(W/'reprojected-cloth.json').write_text(L.dump_cloth_details(mesh))
unreal.log('JK_REPROJECT_OK')
