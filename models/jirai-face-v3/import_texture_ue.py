import unreal,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v3'
assert Path(unreal.Paths.project_dir()).resolve()==(W/'ue/ProjectPBZ').resolve()
items=[('/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face3',W/'T_Jirai_Base.png',8192,True),
    ('/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_Iris',W/'T_Face3_Iris.png',1024,True),
    ('/HuaShira/Mods/SuiPBZ/JiraiVT/T_Face3_EyeMix',W/'T_Face3_EyeMix.png',64,False)]
records=[]
for package,source,size,srgb in items:
    task=unreal.AssetImportTask();task.filename=str(source);task.destination_path,task.destination_name=package.rsplit('/',1)
    task.automated=True;task.replace_existing=True;task.save=False;task.factory=unreal.TextureFactory()
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex=unreal.load_asset(package);assert isinstance(tex,unreal.Texture2D)
    for key,value in dict(srgb=srgb,virtual_texture_streaming=True,
        compression_settings=unreal.TextureCompressionSettings.TC_DEFAULT if srgb else unreal.TextureCompressionSettings.TC_MASKS,
        compression_no_alpha=True,lod_group=unreal.TextureGroup.TEXTUREGROUP_CHARACTER,max_texture_size=size).items():tex.set_editor_property(key,value)
    assert tex.blueprint_get_size_x()==tex.blueprint_get_size_y()==size
    assert unreal.EditorAssetLibrary.save_loaded_asset(tex)
    records.append(dict(package=package,width=size,height=size,virtual_texture_streaming=True,srgb=srgb,
        source_sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
(W/'import-report.json').write_text(json.dumps(dict(source_sha256=records[0]['source_sha256'],textures=records),indent=2))
unreal.log('FISHNET_IMPORT_OK')
