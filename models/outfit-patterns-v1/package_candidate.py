"""Two real VT packages only: no mesh, material or gameplay asset overrides."""
from common import *
import shutil

def inspect_mount(label,dirs,packages=PACKAGES):
 env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
 dest=ROOT/'independent'/label
 output=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,'json',*[relative_package(p) for p in packages]],env)
 assert not any(x in output for x in ['Failed to','Exception','[WRN]','[ERR]']),label
 return {p:read(dest/(relative_package(p)+'.json')) for p in packages}

def build():
 assert_baseline();assert not (ROOT/'build-report.json').exists()
 cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata';cook=read(ROOT/'cook-report.json');assert cook['passed']
 for row in cook['textures']:assert row['source_sha256']==sha(ROOT/f"{row['outfit']}-after.png")==read(ROOT/'atlas-report.json')['outfits'][row['outfit']]['output_sha256']
 ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True);rows=[]
 for package in PACKAGES:
  for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
   p=cooked/(relative_package(package)+ext)
   if p.exists():rows.append(f'"{p}" "../../../{relative_package(package)}{ext}" -compress')
 rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf8');commands=ctx/'commands.txt';commands.write_text(f'-Output="{fresh}/patterns.utoc" -ContainerName=patterns -ResponseFile="{rsp}"\n',encoding='utf8')
 run('pack-textures',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
 inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
 for folder in [fresh,ctx]:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
 legacy=ROOT/'legacy';run('extract-textures',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,legacy])
 assert {p.relative_to(legacy).as_posix() for p in legacy.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 container=ROOT/'container';container.mkdir(exist_ok=True)
 run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
 listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
 assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 write(ROOT/'build-report.json',dict(passed=True,packages=PACKAGES,package_count=2,textures=cook['textures'],container_files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],no_mesh_material_physics_or_gameplay_packages=True,game_runtime_tested=False))
 print('OUTFIT_PATTERNS_PACKAGED',flush=True)

def verify():
 assert_baseline();report=read(ROOT/'build-report.json')
 for r in report['container_files']:assert sha(ROOT/'container'/r['name'])==r['sha256']
 contexts=[MODS,ROOT/'container'];docs=inspect_mount('final',contexts)
 for r in report['textures']:
  assert sha(ROOT/f"{r['outfit']}-after.png")==r['source_sha256']
  tex,=docs[r['package']];assert tex['Type']=='Texture2D' and tex['Properties']['VirtualTextureStreaming'] and tex['Properties'].get('SRGB',True)
  vt=tex['VTData'];assert vt['Width']==vt['Height']==r['size'] and vt['NumMips']==(14 if r['size']==8192 else 13) and vt['LayerTypes']==['PF_DXT1']
 context=ROOT/'resolved-input';context.mkdir(exist_ok=True)
 for folder in contexts:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,context/p.name)
 for ext in ['.ucas','.utoc']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
 run('extract-resolved',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,ROOT/'resolved-legacy'])
 payloads={}
 for package in PACKAGES:
  payloads[package]={}
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=ROOT/'legacy'/(relative_package(package)+ext);b=ROOT/'resolved-legacy'/(relative_package(package)+ext);assert a.exists()==b.exists()
   if a.exists():assert sha(a)==sha(b);payloads[package][ext]=sha(a)
  bulk=ROOT/'resolved-legacy'/(relative_package(package)+'.ubulk')
  for chunk in docs[package][0]['VTData']['Chunks']:
   b=chunk['BulkData'];offset=int(b['OffsetInFile'],16);assert 0<=offset and offset+b['SizeOnDisk']<=bulk.stat().st_size
 write(ROOT/'verification.json',dict(passed=True,status='independent-final-container-verified-runtime-pending',package_count=2,packages=PACKAGES,container_files=report['container_files'],textures=report['textures'],resolved_payloads=payloads,no_mesh_material_physics_or_gameplay_packages=True,game_runtime_tested=False))
 print('OUTFIT_PATTERNS_INDEPENDENTLY_VERIFIED',flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['verify']:verify()
 else:build();verify()
