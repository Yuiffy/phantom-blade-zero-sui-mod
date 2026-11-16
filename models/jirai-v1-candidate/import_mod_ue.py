import unreal,json,sys,math,hashlib
from pathlib import Path
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');WORK=ROOT/'variant';PROJECT=WORK/'ue/ProjectPBZ'
assert Path(unreal.Paths.project_dir()).resolve()==PROJECT.resolve()
sys.path.insert(0,str(PBZ/'ue'));from native_helpers import NativeEditorTools as LIB
EAL=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools()
spec=json.loads((WORK/'material-spec.json').read_text());source=json.loads((WORK/'source-spec.json').read_text())
assert hashlib.sha256(Path(source['fbx']).read_bytes()).hexdigest()==source['fbx_sha256']
unreal.AssetRegistryHelpers.get_asset_registry().search_all_assets(True)
unreal.SystemLibrary.execute_console_command(None,'Interchange.FeatureFlags.Import.FBX 0')
texture_records=[]
for row in spec['textures']:
    task=unreal.AssetImportTask();task.filename=row['path'];task.destination_path,task.destination_name=row['package'].rsplit('/',1)
    task.automated=True;task.replace_existing=True;task.save=False;task.factory=unreal.TextureFactory();tools.import_asset_tasks([task])
    tex=unreal.load_asset(row['package']);assert isinstance(tex,unreal.Texture2D)
    tex.set_editor_property('srgb',row['kind']=='albedo');tex.set_editor_property('virtual_texture_streaming',True)
    tex.set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP if row['kind']=='normal' else unreal.TextureCompressionSettings.TC_DEFAULT)
    tex.set_editor_property('compression_no_alpha',row['kind']!='normal')
    tex.set_editor_property('lod_group',unreal.TextureGroup.TEXTUREGROUP_CHARACTER_SPECULAR if row['kind']=='mask' else unreal.TextureGroup.TEXTUREGROUP_CHARACTER)
    assert EAL.save_loaded_asset(tex)
    texture_records.append({'package':row['package'],'width':tex.blueprint_get_size_x(),'height':tex.blueprint_get_size_y(),'vt':tex.get_editor_property('virtual_texture_streaming')})
materials={}
for m in spec['materials']:
    package='/HuaShira/Mods/SuiPBZ/Materials/'+m['slot'];folder,name=package.rsplit('/',1)
    mi=unreal.load_asset(package) if EAL.does_asset_exist(package) else tools.create_asset(name,folder,unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    assert mi and EAL.save_loaded_asset(mi);materials[m['slot']]=mi
for row in json.loads((ROOT/'cloth-spec.json').read_text()):materials[row['mask']['sim_slot']]=materials['MI_Jirai_Hair']
path=source['body_package']
if EAL.does_asset_exist(path):assert EAL.delete_asset(path)
opt=unreal.FbxImportUI()
for k,v in {'import_mesh':True,'import_as_skeletal':True,'mesh_type_to_import':unreal.FBXImportType.FBXIT_SKELETAL_MESH,'import_materials':False,'import_textures':False,'import_animations':False,'create_physics_asset':False,'automated_import_should_detect_type':False}.items():opt.set_editor_property(k,v)
opt.set_editor_property('skeleton',unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton'))
data=opt.get_editor_property('skeletal_mesh_import_data')
for k,v in {'import_morph_targets':False,'normal_import_method':unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS,'use_t0_as_ref_pose':False,'preserve_smoothing_groups':True,'convert_scene':True,'force_front_x_axis':False,'convert_scene_unit':False,'import_uniform_scale':1.,'update_skeleton_reference_pose':False,'import_meshes_in_bone_hierarchy':True}.items():data.set_editor_property(k,v)
task=unreal.AssetImportTask();task.filename=source['fbx'];task.destination_path,task.destination_name=path.rsplit('/',1);task.replace_existing=True;task.automated=True;task.save=False;task.options=opt;tools.import_asset_tasks([task])
mesh=unreal.load_asset(path);assert isinstance(mesh,unreal.SkeletalMesh)
slots=[]
for slot in mesh.get_editor_property('materials'):
    name=str(slot.get_editor_property('material_slot_name'));assert name in materials,name
    slot.set_editor_property('material_interface',materials[name]);slots.append(slot)
mesh.set_editor_property('materials',slots)
LIB.set_mesh_physics_asset(mesh,unreal.load_asset('/HuaShira/Characters/Hero/Hero_Hun/PA_Hun'))
LIB.set_post_process_anim_blueprint(mesh,EAL.load_blueprint_class('/HuaShira/Characters/Hero/Hero_Hun/Rig/ABP_Hun_PostProcess'))
actual=json.loads(LIB.dump_ref_skeleton(mesh));expected=json.loads((ROOT/'intended-reference-skeleton.json').read_text())['bones']
assert len(actual)==len(expected)==264
lookup={b['name'].lower():b for b in actual};distance=angle=scale=0
for b in expected:
    a=lookup[b['name'].lower()]
    assert (actual[a['parent']]['name'].lower() if a['parent']>=0 else None)==(expected[b['parent']]['name'].lower() if b['parent']>=0 else None)
    distance=max(distance,math.dist(a['t'],b['t']));scale=max(scale,max(abs(x-y) for x,y in zip(a['s'],b['s'])))
    dot=abs(sum(x*y for x,y in zip(a['q'],b['q'])))/math.sqrt(sum(x*x for x in a['q'])*sum(x*x for x in b['q']))
    angle=max(angle,math.degrees(2*math.acos(min(1,dot))))
assert distance<.02 and angle<.1 and scale<.001,(distance,angle,scale)
geometry=LIB.dump_geometry(mesh);assert geometry['triangles']==source['expected_triangles'],geometry
assert EAL.save_loaded_asset(mesh)
report={'status':'imported-reference-verified-runtime-retarget-unverified','bones':264,'distance_cm':distance,'rotation_degrees':angle,'scale_error':scale,'geometry':geometry,'textures':texture_records,'material_slots':[str(x.material_slot_name) for x in slots],'fbx_sha256':source['fbx_sha256'],'reference_contract':'intended-reference-skeleton.json','runtime_retarget_verified':False,'actual_reference_bones':actual}
(WORK/'import-report.json').write_text(json.dumps(report,indent=2),encoding='utf8');unreal.log('SUI_JIRAI_IMPORT_OK')
