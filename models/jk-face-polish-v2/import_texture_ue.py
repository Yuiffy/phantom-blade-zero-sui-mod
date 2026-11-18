import unreal,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jk-face-polish-v2'
assert Path(unreal.Paths.project_dir()).resolve()==(W/'ue/ProjectPBZ').resolve()
source=W/'T_Jirai_Base.png';package='/HuaShira/Mods/SuiPBZ/JKVT/T_JK_FacePolish2'
task=unreal.AssetImportTask();task.filename=str(source);task.destination_path,task.destination_name=package.rsplit('/',1)
task.automated=True;task.replace_existing=True;task.save=False;task.factory=unreal.TextureFactory()
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=unreal.load_asset(package);assert isinstance(tex,unreal.Texture2D)
for key,value in dict(srgb=True,virtual_texture_streaming=True,compression_settings=unreal.TextureCompressionSettings.TC_DEFAULT,compression_no_alpha=True,lod_group=unreal.TextureGroup.TEXTUREGROUP_CHARACTER,max_texture_size=8192).items():tex.set_editor_property(key,value)
assert tex.blueprint_get_size_x()==tex.blueprint_get_size_y()==8192
assert unreal.EditorAssetLibrary.save_loaded_asset(tex)
(W/'import-report.json').write_text(json.dumps(dict(package=package,width=8192,virtual_texture_streaming=True,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()),indent=2))
unreal.log('FISHNET_IMPORT_OK')
