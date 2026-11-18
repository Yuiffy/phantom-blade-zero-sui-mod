from pathlib import Path
import unreal,json
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-v1'
L=unreal.PBZModToolsLibrary
m=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert m
(W/'reference-bones.json').write_text(L.dump_ref_skeleton(m))
(W/'baseline-cloth.json').write_text(L.dump_cloth_details(m))
unreal.log('JK_SKIRT_INSPECT_OK')
