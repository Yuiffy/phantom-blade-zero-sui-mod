"""Stage Jirai R6 into the current JK5 dual outfit, preserving all other packages."""
from pathlib import Path
import importlib.util,json,shutil,sys,os,copy
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';V=W/'variant';OUT=W/'dual'
P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');BASE=P/'variants/dual-jk-motion-v5';MODS=Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks/~mods')
loader=importlib.util.spec_from_file_location('dual_tools',R/'models/dual-outfit-v2/build.py');B=importlib.util.module_from_spec(loader);loader.loader.exec_module(B);B.WORK=OUT
read=B.read;write=B.write;sha=B.sha;run=B.run;relative=B.relative_package;EXTS=B.EXTS
OLD='/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple';NEW='/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple';NAME='z_Sui_DualOutfit_JK5_JiraiR6Detail_P'
def jirai(p):return any(s in p for s in ['/JiraiVT/','/JiraiRig/','/Materials/MI_Jirai_']) or p.endswith('/Physics/PA_Jirai_ClothCollision') or p==NEW
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
 a=read(BASE/'build-report.json');v=read(BASE/'verification.json');fresh=read(V/'build-report.json');assert v['status']=='independent-final-container-verified-runtime-pending';assert read(V/'verification.json')['status']=='independent-container-semantics-passed'
 assert read(W/'source-preservation.json')['source_fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx');assert read(W/'source-preservation.json')['passed'];assert read(V/'ik-marker-verification.json')['passed']
 assert read(V/'cloth-assets-verification.json')['status']=='final-container-cloth-config-and-collision-readback-passed'
 deform=read(V/'render-deformation-review.json');assert deform['initial_reconstruction_max_error_cm']<.3 and deform['first_simulated_tick_max_displacement_cm']<.5
 assert read(W/'source-preservation.json')['all_hair_and_skirt_positions_weights_exactly_preserved']
 assert read(W/'cloth-spec.json')==read(R/'private/jirai-proportion-v1/cloth-spec.json'),'R5 cloth settings changed'
 fit=read(V/'suspender-fit-audit.json');assert fit['fbx_sha256']==sha(W/'Sui_Jirai_Hun_Body.fbx'),'stale suspender audit'
 assert len(fit['samples'])>100
 assert min(x['signed_min_cm'] for x in fit['samples'])>.015,'strap or buckle penetrated thigh'
 assert max(x['distance_max_cm'] for x in fit['samples'])<.5,'strap or buckle separated from thigh'
 for item in v['container_files']:
  assert sha(Path(item['path']))==sha(MODS/item['name'])==item['sha256'],'Current dual outfit changed'
 snapshot=[{'name':f.name,'bytes':f.stat().st_size,'sha256':sha(f)} for f in sorted(MODS.iterdir()) if f.is_file()];write(OUT/'installed-before.json',snapshot)
 keep=set(a['packages'])-{p for p in a['packages'] if jirai(p)};new={p for p in fresh['packages'] if jirai(p)};assert OLD not in new and NEW not in new;new.add(NEW)
 for p in sorted(keep):B.copyasset(BASE/'legacy',p)
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
 for p in keep:payload_equal(BASE/'legacy',p)
 for p in new:payload_equal(V/'legacy',OLD if p==NEW else p,p)
 outfits=copy.deepcopy(a['outfits'])
 for row in outfits.values():
  if row['body']==NEW:row['model']='地雷岁 R6 细节修复，保留 R5 裙摆与头发'
 write(OUT/'build-report.json',{'status':'packaged-independent-verification-pending','packages':packages,'package_count':len(packages),'preserved_packages':sorted(keep),'jirai_packages':sorted(new),'outfits':outfits,'container_files':[{'name':p.name,'path':str(p.resolve()),'bytes':p.stat().st_size,'sha256':sha(p)} for p in sorted(container.iterdir())],'body_relocation':preservation,'source_fbx_sha256':sha(W/'Sui_Jirai_Hun_Body.fbx'),'installed':False,'game_runtime_tested':False})
def verify():
 report=read(OUT/'build-report.json');env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',RAYON_NUM_THREADS='1',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=B.diag.private_key(),PBZX_EXTRA=str(OUT/'container'))
 for mode,packages in [('json',report['packages']),('skel',[OLD,NEW])]:
  log=run('independent-'+mode,[B.diag.DOTNET,B.diag.DLL,B.diag.PAKS,B.diag.MAPPING,B.diag.TOOLS/'oo2core_9_win64.dll',OUT/'independent'/mode,mode,*[relative(p) for p in packages]],env);assert not any(x in log for x in ['Failed to','Exception','failed to','[WRN]','[ERR]']),mode
 for p in report['packages']:
  actual=read(OUT/'independent/json'/(relative(p)+'.json'));assert not any(e['Type']=='Material' for e in actual)
  root=BASE if p in report['preserved_packages'] else V;source=OLD if p==NEW else p;expected=read(root/'independent/json'/(relative(source)+'.json'))
  if p==NEW:expected=substitute(expected)
  assert expected==actual,('independent semantics mismatch',p)
 for p in [OLD,NEW]:
  got=read(OUT/'independent/skel'/(relative(p)+'.Hun_Body_Simple.skel.json'));source=BASE if p==OLD else V;sp=p if p==OLD else OLD;want=read(source/'independent/skel'/(relative(sp)+'.Hun_Body_Simple.skel.json'))
  assert got['bones']==want['bones'] and got['lods']==want['lods'],('body render or reference mismatch',p)
 for f in report['container_files']:assert sha(Path(f['path']))==f['sha256']
 write(OUT/'verification.json',{'status':'independent-final-container-verified-runtime-pending','package_count':report['package_count'],'preserved_packages':len(report['preserved_packages']),'jk5_and_all_appearance_rows_unchanged':True,'jirai_source_payloads_and_semantics_verified':True,'outfits':report['outfits'],'container_files':report['container_files'],'game_runtime_tested':False,'installed':False});print('DUAL_JK5_JIRAI_R6_VERIFIED',report['package_count'])
if __name__=='__main__':
 if sys.argv[1:] == ['verify']:verify()
 else:build();verify()
