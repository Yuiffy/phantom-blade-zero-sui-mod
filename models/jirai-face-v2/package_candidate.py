"""Package isolated albedo and two native leaves; exclude mesh/physics/voice."""
from common import *
import shutil

def build():
 assert not (ROOT/'build-report.json').exists(),'Candidate exists; use verify'
 assert read(ROOT/'cook-report.json')['passed']
 assert read(ROOT/'cook-report.json')['input_sha256']==sha(ROOT/'T_Jirai_Base.png')==read(ROOT/'atlas-report.json')['output_sha256']
 cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata'
 ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True)
 rows=[]
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  p=cooked/(relative_package(PACKAGE)+ext)
  if p.exists():rows.append(f'"{p}" "../../../{relative_package(PACKAGE)}{ext}" -compress')
 rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf8')
 commands=ctx/'commands.txt';commands.write_text(f'-Output="{fresh}/face.utoc" -ContainerName=face -ResponseFile="{rsp}"\n',encoding='utf8')
 run('pack-fresh',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
 inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
 for folder in [fresh,ctx]:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
 extracted=ROOT/'fresh-legacy';legacy=ROOT/'legacy'
 run('extract-fresh',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,extracted])
 assert {p.relative_to(extracted).as_posix() for p in extracted.rglob('*.uasset')}=={relative_package(PACKAGE)+'.uasset'}
 for p in extracted.rglob('*'):
  if p.is_file():
   dest=legacy/p.relative_to(extracted);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
 import rebind_materials
 rebind_materials.build()
 packages=[PACKAGE]+MATERIALS
 assert {p.relative_to(legacy).as_posix() for p in legacy.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in packages}
 container=ROOT/'container';container.mkdir(exist_ok=True)
 run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
 listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
 assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in packages}
 inputs=ROOT/'final-input';inputs.mkdir(exist_ok=True)
 for folder,stem in [(container,NAME),(diag.PAKS,'global')]:
  for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),inputs/(stem+ext))
 run('extract-final',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inputs,ROOT/'final-legacy'])
 for package in packages:
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=legacy/(relative_package(package)+ext);b=ROOT/'final-legacy'/(relative_package(package)+ext)
   assert a.exists()==b.exists()
   if a.exists():assert sha(a)==sha(b),(package,ext)
 report=dict(status='packaged-independent-verification-pending',packages=packages,package_count=3,game_build='26367565',source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),baseline_atlas_sha256=read(ROOT/'atlas-report.json')['source_sha256'],container_files=[dict(path=str(p.resolve()),name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],installed=False,game_runtime_tested=False)
 write(ROOT/'build-report.json',report);print('FACE_PATCH_PACKAGED',flush=True)

def verify():
 report=read(ROOT/'build-report.json')
 env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in [BASE/'container',ROOT/'container']))
 output=run('independent-json',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',ROOT/'independent/json','json',*[relative_package(p) for p in report['packages']]],env)
 assert not any(x in output for x in ['Failed to','Exception','[WRN]','[ERR]'])
 e,=read(ROOT/'independent/json'/(relative_package(PACKAGE)+'.json'))
 assert e['Type']=='Texture2D' and e['Properties']['VirtualTextureStreaming'] and e['Properties'].get('SRGB',True)
 vt=e['VTData'];assert vt['Width']==vt['Height']==8192 and vt['NumMips']>=13 and vt['LayerTypes']==['PF_DXT1']
 bulk=ROOT/'final-legacy'/(relative_package(PACKAGE)+'.ubulk')
 for chunk in vt['Chunks']:
  b=chunk['BulkData'];offset=int(b['OffsetInFile'],16);assert 0<=offset and offset+b['SizeOnDisk']<=bulk.stat().st_size
 for f in report['container_files']:assert sha(f['path'])==f['sha256']
 import rebind_materials
 for package in MATERIALS:
  want=rebind_materials.replace(read(BASE/'independent/json'/(relative_package(package)+'.json')))
  got=read(ROOT/'independent/json'/(relative_package(package)+'.json'))
  assert want==got,('native material semantic change beyond Albedo',package)
  assert sha(BASE/'legacy'/(relative_package(package)+'.uexp'))==sha(ROOT/'final-legacy'/(relative_package(package)+'.uexp'))
 write(ROOT/'verification.json',dict(status='independent-atlas-container-verified-runtime-pending',package_count=3,packages=report['packages'],new_atlas_packages=1,native_material_albedo_rebindings=2,mesh_skeleton_cloth_and_voice_packages=0,geometry_and_physics_not_overridden=True,original_shared_atlas_not_overridden=True,original_material_export_bytes_preserved=True,virtual_texture=True,srgb=True,width=8192,height=8192,mips=vt['NumMips'],formats=vt['LayerTypes'],bulk_bounds_checked=True,source_atlas_sha256=report['source_atlas_sha256'],baseline_atlas_sha256=report['baseline_atlas_sha256'],container_files=report['container_files'],installed=False,game_runtime_tested=False))
 print('FACE_PATCH_INDEPENDENTLY_VERIFIED',flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['verify']:verify()
 else:build();verify()
