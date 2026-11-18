"""Isolated solver experiment; requires a complete fresh build before promotion."""
from pathlib import Path
import unreal,json,runpy
C=Path(__file__).resolve().parent
W=C.parents[1]/'private/jirai-skirt-v1/variant'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
assert mesh
assert unreal.PBZModToolsLibrary.set_cloth_solver(mesh,32,8)==3
assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
(W/'cloth-details.json').write_text(unreal.PBZModToolsLibrary.dump_cloth_details(mesh))
for name in ['test_cloth_ue.py','test_articulation_ue.py']:
 runpy.run_path(str(C/name),run_name='__main__')
