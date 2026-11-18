"""Build a three-package overlay and independently read the installed native data."""
from common import *
from patch import replace
from patch_native import parse_doc,unpack
import shutil,numpy as np

def inspect_mount(label,dirs,packages=PACKAGES,mode='json'):
 env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
 dest=ROOT/'independent'/label
 output=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,mode,*[relative_package(p) for p in packages]],env)
 assert not any(x in output for x in ['Failed to','Exception','[WRN]','[ERR]']),label
 return {p:read(dest/(relative_package(p)+'.json')) for p in packages} if mode=='json' else dest

def build():
 assert_installed_baseline();assert not (ROOT/'build-report.json').exists()
 assert read(ROOT/'cook-report.json')['passed']
 assert read(ROOT/'cook-report.json')['input_sha256']==sha(ROOT/'T_Jirai_Base.png')==read(ROOT/'author-report.json')['texture_sha256']
 assert read(ROOT/'native-patch.json')['passed']
 cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata'
 ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True)
 rows=[]
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  p=cooked/(relative_package(PACKAGE)+ext)
  if p.exists():rows.append(f'"{p}" "../../../{relative_package(PACKAGE)}{ext}" -compress')
 rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf8')
 commands=ctx/'commands.txt';commands.write_text(f'-Output="{fresh}/pin.utoc" -ContainerName=pin -ResponseFile="{rsp}"\n',encoding='utf8')
 run('pack-texture',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
 inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
 for folder in [fresh,ctx]:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
 extracted=ROOT/'fresh-legacy';legacy=ROOT/'legacy'
 run('extract-texture',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,extracted])
 assert {p.relative_to(extracted).as_posix() for p in extracted.rglob('*.uasset')}=={relative_package(PACKAGE)+'.uasset'}
 for p in extracted.rglob('*'):
  if p.is_file():
   target=legacy/p.relative_to(extracted);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
 assert {p.relative_to(legacy).as_posix() for p in legacy.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 container=ROOT/'container';container.mkdir(exist_ok=True)
 run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
 listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
 assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 write(ROOT/'build-report.json',dict(passed=True,packages=PACKAGES,package_count=3,source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),authored_geometry_sha256=sha(ROOT/'authored-geometry.npz'),patched_render_sha256=sha(ROOT/'patched-render.npz'),container_files=[dict(name=p.name,path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],game_runtime_tested=False))
 print('HAIRPIN_PACKAGED',flush=True)

def verify():
 report=read(ROOT/'build-report.json');assert report['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 assert report['patched_render_sha256']==sha(ROOT/'patched-render.npz')
 for row in report['container_files']:assert sha(row['path'])==row['sha256']
 got=inspect_mount('json',[MODS,ROOT/'container'])
 assert got[HAIR]==replace(read(FACE/'independent/json'/(relative_package(HAIR)+'.json')))
 assert got[BODY]==read(FACE/'independent/json'/(relative_package(BODY)+'.json'))
 texture,=got[PACKAGE];assert texture['Type']=='Texture2D' and texture['Properties']['VirtualTextureStreaming'] and texture['Properties'].get('SRGB',True)
 vt=texture['VTData'];assert vt['Width']==vt['Height']==8192 and vt['NumMips']==14 and vt['LayerTypes']==['PF_DXT1']
 skel=inspect_mount('skel',[MODS,ROOT/'container'],[BODY],'skel')
 skelfile=relative_package(BODY)+'.Hun_Body_Simple.skel.json'
 assert read(skel/skelfile)==read(FACE/'independent/skel'/skelfile),'Skeleton, sections or cloth metadata changed'
 # Include the retained R8 and Face3 contexts solely to resolve external
 # imports. Assert the extracted body is the new payload, never a duplicate.
 context=ROOT/'resolved-input';context.mkdir(exist_ok=True)
 for p in MODS.iterdir():
  if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,context/p.name)
 for p in (ROOT/'container').iterdir():
  if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,context/p.name)
 for ext in ['.ucas','.utoc']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
 run('extract-resolved',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,ROOT/'resolved-legacy'])
 final=ROOT/'resolved-legacy'/(relative_package(BODY)+'.uasset')
 for package in PACKAGES:
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=ROOT/'legacy'/(relative_package(package)+ext);b=ROOT/'resolved-legacy'/(relative_package(package)+ext)
   assert a.exists()==b.exists()
   if a.exists():assert sha(a)==sha(b),(package,ext)
 bulk=ROOT/'resolved-legacy'/(relative_package(PACKAGE)+'.ubulk')
 for chunk in vt['Chunks']:
  b=chunk['BulkData'];offset=int(b['OffsetInFile'],16);assert 0<=offset and offset+b['SizeOnDisk']<=bulk.stat().st_size
 native=ROOT/'independent/native.json';native.parent.mkdir(exist_ok=True)
 run('native-json',[diag.TOOLS/'UAssetGUI.exe','tojson',final,native,'VER_UE5_6','PBZ'])
 doc=read(native);p,w,indices,detail=parse_doc(doc);raw=unpack(doc);old=unpack(read(FACE/'native/final.json'))
 op,ow,oi,od=parse_doc(read(FACE/'native/final.json'))
 assert w==ow and len(raw)==len(old)
 assert {k:v for k,v in detail.items() if k!='raw_native_export_sha256'}=={k:v for k,v in od.items() if k!='raw_native_export_sha256'}
 allowed=np.load(ROOT/'allowed-bytes.npz')['mask'];changed=np.frombuffer(raw,'u1')!=np.frombuffer(old,'u1')
 assert np.all(allowed[changed]) and changed.any()
 want=np.load(ROOT/'patched-render.npz');assert np.array_equal(p,want['positions']) and np.array_equal(indices,want['indices'])
 n=len(p);s=detail['tangent_span'];frames=np.frombuffer(raw,'u1',count=s['bytes'],offset=s['offset']).reshape(n,8).copy()
 s=detail['uv_span'];tex=np.frombuffer(raw,'<f2',count=s['count']*2,offset=s['offset']).reshape(n,2,2).copy()
 assert np.array_equal(frames,want['packed_tangents']) and np.array_equal(tex,want['uv'])
 fields={k:want[k] for k in want.files};fields.update(positions=p,indices=indices,packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127,uv=tex)
 np.savez_compressed(ROOT/'final-render.npz',**fields)
 write(ROOT/'verification.json',dict(passed=True,status='independent-final-container-verified-runtime-pending',package_count=3,packages=PACKAGES,container_files=report['container_files'],source_atlas_sha256=report['source_atlas_sha256'],authored_geometry_sha256=report['authored_geometry_sha256'],native_render_sha256=sha(ROOT/'final-render.npz'),all_non_accessory_bytes_exact=True,face3_geometry_frames_uv_exact=True,uv1_weights_skeleton_cloth_physics_exact=True,native_hair_material_export_payload_exact=True,vt_size=8192,vt_mips=14,game_runtime_tested=False))
 print('HAIRPIN_INDEPENDENTLY_VERIFIED',flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['verify']:verify()
 else:build();verify()
