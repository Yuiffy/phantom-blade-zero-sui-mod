"""Whitelist three packages, independently read final metadata/native and bulk."""
from common import *
from patch_native import parse_doc,unpack,replace
import shutil,numpy as np
def inspect_mount(label,dirs,packages=PACKAGES,mode='json'):
 env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
 dest=ROOT/'independent'/label
 out=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,mode,*[relative_package(p) for p in packages]],env)
 assert not any(x in out for x in ['Failed to','Exception','[WRN]','[ERR]']),label
 return {p:read(dest/(relative_package(p)+'.json')) for p in packages} if mode=='json' else dest
def extract(label,dirs):
 context=ROOT/(label+'-input');context.mkdir(exist_ok=True)
 for folder in dirs:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,context/p.name)
 for ext in ['.ucas','.utoc']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
 dest=ROOT/(label+'-legacy')
 run('extract-'+label,[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,dest])
 return dest
def build():
 assert_baseline();assert not (ROOT/'build-report.json').exists()
 assert read(ROOT/'cook-report.json')['input_sha256']==sha(ROOT/'T_Jirai_Base.png')==read(ROOT/'author-report.json')['atlas_sha256']
 assert read(ROOT/'native-patch.json')['passed'];assert read(ROOT/'geometry-preflight.json')['passed']
 cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata';ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True)
 rows=[]
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  p=cooked/(relative_package(PACKAGE)+ext)
  if p.exists():rows.append(f'"{p}" "../../../{relative_package(PACKAGE)}{ext}" -compress')
 rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf8')
 commands=ctx/'commands.txt';commands.write_text(f'-Output="{fresh}/polish.utoc" -ContainerName=polish -ResponseFile="{rsp}"\n',encoding='utf8')
 run('pack-texture',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
 inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
 for folder in [fresh,ctx]:
  for p in folder.iterdir():
   if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
 dest=ROOT/'fresh-legacy';run('extract-texture',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,dest])
 assert {p.relative_to(dest).as_posix() for p in dest.rglob('*.uasset')}=={relative_package(PACKAGE)+'.uasset'}
 legacy=ROOT/'legacy'
 for p in dest.rglob('*'):
  if p.is_file():
   out=legacy/p.relative_to(dest);out.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,out)
 assert {p.relative_to(legacy).as_posix() for p in legacy.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 container=ROOT/'container';container.mkdir(exist_ok=True)
 run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
 listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
 assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
 write(ROOT/'build-report.json',dict(passed=True,packages=PACKAGES,package_count=3,source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),patched_render_sha256=sha(ROOT/'patched-render.npz'),container_files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())]))
 print('CHIN_PACKAGED',flush=True)
def verify():
 report=read(ROOT/'build-report.json');assert report['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png') and report['patched_render_sha256']==sha(ROOT/'patched-render.npz')
 for row in report['container_files']:assert sha(ROOT/'container'/row['name'])==row['sha256']
 got=inspect_mount('final',[MODS,ROOT/'container']);assert got[SKIN]==replace(read(FACE/'independent/final'/(relative_package(SKIN)+'.json')))
 assert got[BODY]==read(PIN/'independent/final'/(relative_package(BODY)+'.json'))
 texture,=got[PACKAGE];vt=texture['VTData'];assert texture['Type']=='Texture2D' and texture['Properties']['VirtualTextureStreaming'] and texture['Properties'].get('SRGB',True)
 assert vt['Width']==vt['Height']==8192 and vt['NumMips']==14 and vt['LayerTypes']==['PF_DXT1']
 skel=inspect_mount('skel',[MODS,ROOT/'container'],[BODY],'skel');skelfile=relative_package(BODY)+'.Hun_Body_Simple.skel.json'
 assert read(skel/skelfile)==read(PIN/'independent/skel'/skelfile)
 dest=extract('resolved',[MODS,ROOT/'container']);payloads={}
 for package in PACKAGES:
  payloads[package]={}
  for ext in ['.uexp','.ubulk','.uptnl']:
   a=ROOT/'legacy'/(relative_package(package)+ext);b=dest/(relative_package(package)+ext);assert a.exists()==b.exists()
   if a.exists():assert sha(a)==sha(b),(package,ext);payloads[package][ext]=sha(b)
 bulk=dest/(relative_package(PACKAGE)+'.ubulk')
 for chunk in vt['Chunks']:
  bd=chunk['BulkData'];offset=int(bd['OffsetInFile'],16);assert 0<=offset and offset+bd['SizeOnDisk']<=bulk.stat().st_size
 native=ROOT/'independent/native.json';run('native-final',[diag.TOOLS/'UAssetGUI.exe','tojson',dest/(relative_package(BODY)+'.uasset'),native,'VER_UE5_6','PBZ'])
 doc=read(native);pos,w,idx,detail=parse_doc(doc);raw=unpack(doc);original=read(PIN/'independent/native.json');op,ow,oi,od=parse_doc(original);oldraw=unpack(original)
 assert len(raw)==len(oldraw) and {k:v for k,v in detail.items() if k!='raw_native_export_sha256'}=={k:v for k,v in od.items() if k!='raw_native_export_sha256'}
 changed=np.frombuffer(raw,'u1')!=np.frombuffer(oldraw,'u1');assert np.all(np.load(ROOT/'allowed-bytes.npz')['mask'][changed])
 selections=np.load(ROOT/'author-selections.npz');copies=dict(selections['weight_copies'].tolist())
 for i in range(len(w)):assert w[i]==ow[copies.get(i,i)],('Weight readback',i)
 wanted=np.load(ROOT/'patched-render.npz');assert np.array_equal(pos,wanted['positions']) and np.array_equal(idx,wanted['indices'])
 s=detail['tangent_span'];frames=np.frombuffer(raw,'u1',count=s['bytes'],offset=s['offset']).reshape(len(pos),8).copy()
 s=detail['uv_span'];tex=np.frombuffer(raw,'<f2',count=s['count']*2,offset=s['offset']).reshape(len(pos),2,2).copy()
 assert np.array_equal(frames,wanted['packed_tangents']) and np.array_equal(tex,wanted['uv'])
 fields={k:wanted[k] for k in wanted.files};fields.update(positions=pos,indices=idx,packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127,uv=tex)
 np.savez_compressed(ROOT/'final-render.npz',**fields)
 write(ROOT/'verification.json',dict(passed=True,package_count=3,packages=PACKAGES,container_files=report['container_files'],source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),native_render_sha256=sha(ROOT/'final-render.npz'),patched_render_sha256=sha(ROOT/'patched-render.npz'),bounded_native_changes_exact=True,uv1_exact=True,original_weights_elsewhere_exact=True,copied_weights_readback_exact=True,skeleton_sections_cloth_physics_exact=True,skin_native_shader_export_exact=True,vt_size=8192,vt_mips=14,resolved_payloads=payloads,game_runtime_tested=False))
 print('CHIN_FINAL_VERIFIED',flush=True)
if __name__=='__main__':
 if sys.argv[1:]==['verify']:verify()
 else:build();verify()
