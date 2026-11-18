"""Stage R7 into the installed SkinEyes1/Fishnet1 outfit; preserve its 8K VT payload."""
from pathlib import Path
import importlib.util,json,shutil,sys,os,copy
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';V=W/'variant';OUT=W/'dual'
P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');BASE=R/'private/skin-eyes-v1/dual';MODS=Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
loader=importlib.util.spec_from_file_location('dual_tools',R/'models/dual-outfit-v2/build.py');B=importlib.util.module_from_spec(loader);loader.loader.exec_module(B);B.WORK=OUT
read=B.read;write=B.write;sha=B.sha;run=B.run;relative=B.relative_package;EXTS=B.EXTS
FISH=R/'private/fishnet-v1';ATLAS='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base'
OLD='/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple';NEW='/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple';NAME='z_Sui_DualOutfit_JK5_JiraiR7Skirt_P'
def jirai(p):return any(s in p for s in ['/JiraiVT/','/JiraiRig/','/Materials/MI_Jirai_']) or p.endswith('/Physics/PA_Jirai_ClothCollision') or p.endswith('/Physics/PA_Jirai_SkirtCollision') or p==NEW
def payload_equal(root,package,target=None):
 for ext in EXTS[1:]:
  a=root/(relative(package)+ext);b=OUT/'final-legacy'/(relative(target or package)+ext);assert a.exists()==b.exists()
  if a.exists():assert sha(a)==sha(b),(package,ext)
def substitute(value):
 if isinstance(value,dict):return {k:substitute(v) for k,v in value.items()}
 if isinstance(value,list):return [substitute(v) for v in value]
 return value.replace(OLD,NEW) if isinstance(value,str) else value
def build():
 OUT.mkdir(exist_ok=True);assert not (OUT/'build-report.json').exists(),'Already staged; verify existing candidate'
 shutil.copy2(BASE/'jk-material-spec.json',OUT/'jk-material-spec.json')
 a=read(FISH/'build-report.json');v=read(FISH/'verification.json');fresh=read(V/'build-report.json');assert v['status']=='independent-final-container-verified-runtime-pending';assert read(V/'verification.json')['status']=='independent-container-semantics-passed'
 assert v['texture_width']==8192 and v['preserved_packages']==98 and v['skin_and_closed_sclera_fixes_preserved']
 assert read(FISH/'atlas-report.json')['output_sha256']==v['source_atlas_sha256']==sha(FISH/'T_Jirai_Base.png')
 assert read(W/'source-preservation.json')['source_fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx');assert read(W/'source-preservation.json')['passed'];assert read(V/'ik-marker-verification.json')['passed']
 assert read(V/'cloth-assets-verification.json')['status']=='final-container-cloth-config-and-collision-readback-passed'
 native=read(V/'cloth-assets-verification.json');assert native['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and native['cloth_spec_sha256']==sha(W/'cloth-spec.json') and native['render_skin_blend_verified']
 deform=read(V/'render-deformation-review.json');assert deform['initial_reconstruction_max_error_cm']<.3 and deform['first_simulated_tick_max_displacement_cm']<.5
 assert read(W/'source-preservation.json')['skirt_and_safety_shorts_only_changes']
 assert read(V/'eye-geometry-verification.json')['passed']
 coverage=read(W/'coverage-verification.json');assert coverage['passed'] and coverage['continuous_crotch'] and coverage['opaque_black'] and coverage['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx')
 for filename in ['articulation-shape-gate.json','articulation-validation.json']:
  gate=read(V/filename);assert gate['passed'],filename
  assert gate['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and gate['cloth_spec_sha256']==sha(W/'cloth-spec.json'),('stale stability gate',filename)
 stamp=read(V/'combined-tests.json')
 assert all(Path(p).is_file() and sha(Path(p))==value for table in ['inputs','outputs'] for p,value in stamp[table].items()),'Stale author tests'
 reconstruction=read(V/'articulated-reconstruction.json')
 assert reconstruction['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and reconstruction['cloth_spec_sha256']==sha(W/'cloth-spec.json')
 assert reconstruction['combined_tests_sha256']==sha(V/'combined-tests.json') and reconstruction['cooked_mapping_sha256']==sha(V/'independent/cloth-native-details.json')
 visual=read(W/'visual-review.json');assert visual['reviewed'] and visual['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and visual['cloth_spec_sha256']==sha(W/'cloth-spec.json')
 assert visual['combined_tests_sha256']==sha(V/'combined-tests.json') and visual['cooked_mapping_sha256']==sha(V/'independent/cloth-native-details.json')
 assert all(sha(Path(p))==value for p,value in visual['images'].items()),'Changed review images'
 assert visual['source_atlas_sha256']==v['source_atlas_sha256']==read(V/'preview-atlas.json')['source_atlas_sha256']
 pin=read(V/'render-pin-authoring.json');assert pin['only_uint16_render_blends_changed'] and pin['physical_cloth_and_other_exports_exact']
 assert pin['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and pin['cloth_spec_sha256']==sha(W/'cloth-spec.json')
 audit=read(V/'articulated-surface-audit.json');assert {x['profile'] for x in audit}==set(read(W/'pose-contract.json')['clips'])
 for profile in audit:
  assert profile['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx') and profile['pose_contract_sha256']==sha(W/'pose-contract.json')
  assert max(x['visible_thigh_edges_crossing_skirt'] for x in profile['thigh_edge_intersections'])==0,('unresolved skirt contact',profile['profile'])
 fit=read(V/'suspender-fit-audit.json');assert fit['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx'),'stale suspender audit'
 assert len(fit['samples'])>100
 assert min(x['signed_min_cm'] for x in fit['samples'])>.015,'strap or buckle penetrated thigh'
 assert max(x['distance_max_cm'] for x in fit['samples'])<.5,'strap or buckle separated from thigh'
 for item in v['container_files']:
  assert sha(Path(item['path']))==sha(MODS/item['name'])==item['sha256'],'Current dual outfit changed'
 snapshot=[{'name':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(MODS.iterdir()) if f.is_file()];write(OUT/'installed-before.json',snapshot)
 keep=(set(a['packages'])-{p for p in a['packages'] if jirai(p)})|{ATLAS};new={p for p in fresh['packages'] if jirai(p)}-{ATLAS};assert OLD not in new and NEW not in new;new.add(NEW)
 for p in sorted(keep):B.copyasset(FISH/'legacy',p)
 for p in sorted(new-{NEW}):B.copyasset(V/'legacy',p)
 src=V/'legacy'/(relative(OLD)+'.uasset');original_json=OUT/'body-original.json';run('body-original',[B.diag.TOOLS/'UAssetGUI.exe','tojson',src,original_json,'VER_UE5_6','PBZ']);original=read(original_json);edited=B.replace(original,{OLD:NEW});assert edited['FolderName']==NEW
 path=OUT/'body-edited.json';write(path,edited);target=OUT/'legacy'/(relative(NEW)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True);run('body-relocate',[B.diag.TOOLS/'UAssetGUI.exe','fromjson',path,target,'PBZ']);generated=OUT/'body-generated.json';run('body-generated',[B.diag.TOOLS/'UAssetGUI.exe','tojson',target,generated,'VER_UE5_6','PBZ']);preservation=B.restore(src,target,original,read(generated))
 for ext in ['.ubulk','.uptnl']:
  if src.with_suffix(ext).exists():shutil.copy2(src.with_suffix(ext),target.with_suffix(ext))
 assert src.with_suffix('.uexp').read_bytes()==target.with_suffix('.uexp').read_bytes()
 packages=sorted(keep|new);assert {p.relative_to(OUT/'legacy').as_posix() for p in (OUT/'legacy').rglob('*.uasset')}=={relative(p)+'.uasset' for p in packages}
 container=OUT/'container';container.mkdir(exist_ok=True);run('pack',[B.diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',OUT/'legacy',container/(NAME+'.utoc')]);listing=run('list',[B.diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')]);listed={line.split()[-1].replace('\\','/').removeprefix('../../../') for line in listing.splitlines() if line.strip().endswith('.uasset')};assert listed=={relative(p)+'.uasset' for p in packages}
 inputs=OUT/'extract-input';inputs.mkdir(exist_ok=True)
 for folder,stem in [(container,NAME),(B.diag.PAKS,'global')]:
  for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),inputs/(stem+ext))
 run('extract',[B.diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inputs,OUT/'final-legacy'])
 for p in keep:payload_equal(FISH/'legacy',p)
 for p in new:payload_equal(V/'legacy',OLD if p==NEW else p,p)
 outfits=copy.deepcopy(a['outfits'])
 for row in outfits.values():
  if row['body']==NEW:row['model']='地雷岁 R7 裙摆侧片避让，保留 R6 吊带铁扣与头发'
 write(OUT/'build-report.json',{'status':'packaged-independent-verification-pending','packages':packages,'package_count':len(packages),'preserved_packages':sorted(keep),'jirai_packages':sorted(new),'outfits':outfits,'container_files':[{'name':p.name,'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(container.iterdir())],'body_relocation':preservation,'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'skin_eyes_v1_preserved':True,'fishnet_v1_8k_preserved':True,'source_atlas_sha256':v['source_atlas_sha256'],'installed':False,'game_runtime_tested':False})
def verify():
 report=read(OUT/'build-report.json');env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',RAYON_NUM_THREADS='1',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=B.diag.private_key(),PBZX_EXTRA=str(OUT/'container'))
 for mode,packages in [('json',report['packages']),('skel',[OLD,NEW])]:
  log=run('independent-'+mode,[B.diag.DOTNET,B.diag.DLL,B.diag.PAKS,B.diag.MAPPING,B.diag.TOOLS/'oo2core_9_win64.dll',OUT/'independent'/mode,mode,*[relative(p) for p in packages]],env);assert not any(x in log for x in ['Failed to','Exception','failed to','[WRN]','[ERR]']),mode
 for p in report['packages']:
  actual=read(OUT/'independent/json'/(relative(p)+'.json'));assert not any(e['Type']=='Material' for e in actual)
  root=FISH if p in report['preserved_packages'] else V;source=OLD if p==NEW else p;expected=read(root/'independent/json'/(relative(source)+'.json'))
  if p==NEW:expected=substitute(expected)
  assert expected==actual,('independent semantics mismatch',p)
 for p in [OLD,NEW]:
  got=read(OUT/'independent/skel'/(relative(p)+'.Hun_Body_Simple.skel.json'));source=BASE if p==OLD else V;sp=p if p==OLD else OLD;want=read(source/'independent/skel'/(relative(sp)+'.Hun_Body_Simple.skel.json'))
  assert got['bones']==want['bones'] and got['lods']==want['lods'],('body render or reference mismatch',p)
 for f in report['container_files']:assert sha(Path(f['path']))==f['sha256']
 atlas,=read(OUT/'independent/json'/(relative(ATLAS)+'.json'));assert atlas['VTData']['Width']==atlas['VTData']['Height']==8192 and atlas['Properties']['VirtualTextureStreaming']
 assert atlas==read(FISH/'independent/json'/(relative(ATLAS)+'.json'))[0]
 for ext in EXTS[1:]:
  src=FISH/'legacy'/(relative(ATLAS)+ext);dst=OUT/'final-legacy'/(relative(ATLAS)+ext);assert src.exists()==dst.exists()
  if src.exists():assert sha(src)==sha(dst)
 write(OUT/'verification.json',{'status':'independent-final-container-verified-runtime-pending','package_count':report['package_count'],'preserved_packages':len(report['preserved_packages']),'jk5_and_all_appearance_rows_unchanged':True,'jirai_source_payloads_and_semantics_verified':True,'fishnet_v1_8k_payload_exact':True,'source_atlas_sha256':report['source_atlas_sha256'],'outfits':report['outfits'],'container_files':report['container_files'],'game_runtime_tested':False,'installed':False});print('DUAL_JK5_JIRAI_R7_VERIFIED',report['package_count'])
if __name__=='__main__':
 if sys.argv[1:] == ['verify']:verify()
 else:build();verify()
