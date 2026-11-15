"""Smaller substeps stabilize short cotton shell edges in the 30 Hz test."""
import unreal,json
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';W=R/'variant'
m=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert m
assert m.skeleton.get_path_name()=='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton.Hun_Skin_Skeleton'
assert unreal.PBZModToolsLibrary.set_cloth_solver(m,8,4)==len(json.loads((R/'cloth-spec.json').read_text()))
assert unreal.EditorAssetLibrary.save_loaded_asset(m,False)
(W/'cloth-details.json').write_text(unreal.PBZModToolsLibrary.dump_cloth_details(m))
unreal.log('COTTON_SOLVER_SUBSTEPS_4_SAVED')
