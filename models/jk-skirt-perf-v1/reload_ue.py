"""Verify that the saved authoring asset survives a fresh editor process."""
from pathlib import Path
import unreal,json
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
stage=json.loads((W/'chosen-stage.json').read_text())['stage']
actual=json.loads(unreal.PBZModToolsLibrary.dump_cloth_details(mesh));expected=json.loads((W/stage/'cloth-details.json').read_text())
assert actual==expected,'Saved cloth settings changed after editor reload'
(W/'editor-reload-verification.json').write_text(json.dumps({'passed':True,'assets':len(actual['assets']),'guids':[a['guid'] for a in actual['assets']],'source':'fresh editor process'},indent=2))
