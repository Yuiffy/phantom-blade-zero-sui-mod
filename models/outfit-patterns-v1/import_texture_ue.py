import unreal,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/outfit-patterns-v1'
assert Path(unreal.Paths.project_dir()).resolve()==(W/'ue/ProjectPBZ').resolve()
rows=[]
for outfit,package,size in [('jk','/HuaShira/Mods/SuiPBZ/JKVT/T_JK_Base',8192),('jirai','/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base',8192)]:
 source=W/f'{outfit}-after.png';task=unreal.AssetImportTask();task.filename=str(source);task.destination_path,task.destination_name=package.rsplit('/',1)
 task.automated=True;task.replace_existing=True;task.save=False;task.factory=unreal.TextureFactory()
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=unreal.load_asset(package);assert isinstance(tex,unreal.Texture2D)
 for key,value in dict(srgb=True,virtual_texture_streaming=True,compression_settings=unreal.TextureCompressionSettings.TC_DEFAULT,compression_no_alpha=True,lod_group=unreal.TextureGroup.TEXTUREGROUP_CHARACTER,max_texture_size=size).items():tex.set_editor_property(key,value)
 assert tex.blueprint_get_size_x()==tex.blueprint_get_size_y()==size
 assert unreal.EditorAssetLibrary.save_loaded_asset(tex)
 rows.append(dict(outfit=outfit,package=package,size=size,vt=True,source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
(W/'import-report.json').write_text(json.dumps(dict(passed=True,textures=rows),indent=2))
unreal.log('OUTFIT_PATTERNS_IMPORT_OK')
