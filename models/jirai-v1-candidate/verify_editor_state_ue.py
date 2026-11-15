"""A fresh process must see the saved shoulder rig and all five cloth bindings."""
import unreal,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'private/jirai-v1';W=R/'variant'
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
target='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton.Hun_Skin_Skeleton'
assert mesh.skeleton.get_path_name()==target,mesh.skeleton.get_path_name()
d=json.loads(unreal.PBZModToolsLibrary.dump_cloth_details(mesh));spec=json.loads((R/'cloth-spec.json').read_text());assert len(d['assets'])==len(spec)
by_slot={s['slot']:s for s in d['sections']}
for row in spec:
 assert by_slot[row['slot']]['cloth_index']>=0 and not by_slot[row['slot']]['disabled']
 assert by_slot[row['mask']['sim_slot']]['disabled']
report={'passed':True,'fresh_process_reload':True,'skeleton':target,'cloth_assets':len(spec),'fbx_sha256':hashlib.sha256((R/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest()}
(W/'editor-reload-verification.json').write_text(json.dumps(report,indent=2));unreal.log('EDITOR_RELOAD_OK')
