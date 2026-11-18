from pathlib import Path
import json
import unreal

work=Path(__file__).resolve().parents[2]/'private/jk-skirt-stable-v1/soft-edge'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
mapping=unreal.PBZModToolsLibrary.reproject_cloth_mapping(mesh,'MI_JK_PleatedSkirt','CA_Sui_Skirt_0',(work/'target.json').read_text())
assert len(json.loads(mapping)['mapping'])==1531
(work/'remap.json').write_text(mapping)
