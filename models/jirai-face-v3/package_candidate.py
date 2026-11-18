"""Package three VT textures, three native leaves and one bounded face mesh."""
from common import *
from patch_native import BODY,parse_doc,unpack
from rebind_materials import IRIS,EYE_MIX,replace
import shutil
import numpy as np

TEXTURES=[PACKAGE,IRIS,EYE_MIX]
PACKAGES=TEXTURES+MATERIALS+[BODY]

def inspect_mount(label,dirs,packages=PACKAGES,mode='json'):
    env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),
        PBZX_EXTRA=';'.join(str(d) for d in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
    dest=ROOT/'independent'/label
    output=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,mode,*[relative_package(p) for p in packages]],env)
    assert not any(t in output for t in ['Failed to','Exception','[WRN]','[ERR]']),label
    if mode=='json':return {p:read(dest/(relative_package(p)+'.json')) for p in packages}
    return dest

def build():
    assert not (ROOT/'build-report.json').exists(),'Candidate exists; use verify'
    assert read(ROOT/'cook-report.json')['passed']
    assert read(ROOT/'cook-report.json')['input_sha256']==sha(ROOT/'T_Jirai_Base.png')==read(ROOT/'atlas-report.json')['output_sha256']
    for name,value in read(ROOT/'cook-report.json')['texture_sources'].items():assert sha(ROOT/name)==value
    assert read(ROOT/'native/patch-report.json')['source_surface_sha256']==sha(ROOT/'surface.npz')
    cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata'
    ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True)
    rows=[]
    for package in TEXTURES:
        for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
            p=cooked/(relative_package(package)+ext)
            if p.exists():rows.append(f'"{p}" "../../../{relative_package(package)}{ext}" -compress')
    rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf-8')
    commands=ctx/'commands.txt';commands.write_text(f'-Output="{fresh}/face.utoc" -ContainerName=face -ResponseFile="{rsp}"\n',encoding='utf-8')
    run('pack-fresh',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
    inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
    for folder in [fresh,ctx]:
        for p in folder.iterdir():
            if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
    extracted=ROOT/'fresh-legacy';legacy=ROOT/'legacy'
    run('extract-fresh',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,extracted])
    assert {p.relative_to(extracted).as_posix() for p in extracted.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in TEXTURES}
    for p in extracted.rglob('*'):
        if p.is_file():
            dest=legacy/p.relative_to(extracted);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    import rebind_materials
    rebind_materials.build()
    assert {p.relative_to(legacy).as_posix() for p in legacy.rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
    container=ROOT/'container';container.mkdir(exist_ok=True)
    run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
    listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
    assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in PACKAGES}
    inputs=ROOT/'final-input';inputs.mkdir(exist_ok=True)
    for folder,stem in [(container,NAME),(diag.PAKS,'global')]:
        for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),inputs/(stem+ext))
    run('extract-final',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inputs,ROOT/'final-legacy'])
    for package in PACKAGES:
        for ext in ['.uexp','.ubulk','.uptnl']:
            a=legacy/(relative_package(package)+ext);b=ROOT/'final-legacy'/(relative_package(package)+ext)
            assert a.exists()==b.exists()
            if a.exists():assert sha(a)==sha(b),(package,ext)
    write(ROOT/'build-report.json',dict(status='packaged-independent-verification-pending',packages=PACKAGES,package_count=len(PACKAGES),
        source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),source_iris_sha256=sha(ROOT/'T_Face3_Iris.png'),
        source_mix_sha256=sha(ROOT/'T_Face3_EyeMix.png'),surface_sha256=sha(ROOT/'surface.npz'),
        container_files=[dict(path=str(p.resolve()),name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],
        installed=False,game_runtime_tested=False))
    print('FACE3_PACKAGED',flush=True)

def verify():
    report=read(ROOT/'build-report.json')
    assert report['surface_sha256']==sha(ROOT/'surface.npz')
    assert report['source_atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
    assert report['source_iris_sha256']==sha(ROOT/'T_Face3_Iris.png')
    assert report['source_mix_sha256']==sha(ROOT/'T_Face3_EyeMix.png')
    expected=inspect_mount('json',[MODS,ROOT/'container'])
    texture_records=[]
    for package,size,srgb in [(PACKAGE,8192,True),(IRIS,1024,True),(EYE_MIX,64,False)]:
        e,=expected[package];assert e['Type']=='Texture2D' and e['Properties']['VirtualTextureStreaming']
        assert e['Properties'].get('SRGB',True)==srgb
        vt=e['VTData']
        # UE expands a sub-tile constant mask to the VT tile dimension. Its
        # source is 64 square; the cooked logical VT is 128 square/8 mips.
        cooked_size=max(size,vt['TileSize'])
        assert vt['Width']==vt['Height']==cooked_size and vt['NumMips']>=int(np.log2(cooked_size))+1
        assert vt['LayerTypes']==['PF_DXT1']
        bulk=ROOT/'final-legacy'/(relative_package(package)+'.ubulk')
        for chunk in vt['Chunks']:
            b=chunk['BulkData'];offset=int(b['OffsetInFile'],16);assert 0<=offset and offset+b['SizeOnDisk']<=bulk.stat().st_size
        texture_records.append(dict(package=package,source_width=size,cooked_width=cooked_size,srgb=srgb,mips=vt['NumMips'],format=vt['LayerTypes']))
    for package in MATERIALS:
        want=replace(read(MODEL/'independent/json'/(relative_package(package)+'.json')),package.endswith('MI_Jirai_EyeIris'))
        assert expected[package]==want,('Native leaf changed beyond texture imports',package)
    assert expected[BODY]==read(MODEL/'independent/json'/(relative_package(BODY)+'.json')),'Non-render skeletal metadata changed'
    skel=inspect_mount('skel',[MODS,ROOT/'container'],[BODY],'skel')
    got=read(skel/(relative_package(BODY)+'.Hun_Body_Simple.skel.json'))
    original=read(MODEL/'independent/skel'/(relative_package(BODY)+'.Hun_Body_Simple.skel.json'))
    assert got==original,'Skeleton/section/cloth metadata changed'
    # Retoc needs the retained base packages present when resolving the mesh's
    # external material/skeleton imports. Keep the standalone extraction as
    # payload evidence, and independently require the context dump to contain
    # the exact new payload (never silently select the old duplicate mesh).
    context=ROOT/'resolved-input';context.mkdir(exist_ok=True)
    for folder,stem in [(ROOT/'container',NAME),(MODEL/'container',MODEL_NAME),(diag.PAKS,'global')]:
        for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),context/(stem+ext))
    run('extract-resolved',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel','--filter','Hun_Body_Simple',context,ROOT/'resolved-legacy'])
    final=ROOT/'resolved-legacy'/(relative_package(BODY)+'.uasset');docpath=ROOT/'native/final.json'
    assert sha(final.with_suffix('.uexp'))==sha(ROOT/'final-legacy'/(relative_package(BODY)+'.uexp'))==sha(ROOT/'legacy'/(relative_package(BODY)+'.uexp'))
    run('native-final-json',[diag.TOOLS/'UAssetGUI.exe','tojson',final,docpath,'VER_UE5_6','PBZ'])
    doc=read(docpath);pos,weights,indices,details=parse_doc(doc)
    baseline=read(ROOT/'native/source.json');bp,bw,bi,bd=parse_doc(baseline)
    want=np.load(ROOT/'native/patched-render.npz')
    assert np.array_equal(pos,want['positions']) and np.array_equal(indices,want['indices'])
    assert weights==bw and np.array_equal(indices,bi)
    assert {k:v for k,v in details.items() if k!='raw_native_export_sha256'}=={k:v for k,v in bd.items() if k!='raw_native_export_sha256'}
    raw=unpack(doc);before=unpack(baseline)
    assert raw!=before and len(raw)==len(before)
    allowed=np.zeros(len(raw),bool)
    for key in ['position_span','tangent_span','uv_span']:
        s=details[key];allowed[s['offset']:s['offset']+s['bytes']]=True
    changed=np.frombuffer(raw,'u1')!=np.frombuffer(before,'u1');assert np.all(allowed[changed])
    assert sha(MODEL/'final-legacy'/(relative_package(BODY)+'.uasset'))==sha(final)
    n=len(pos);s=details['tangent_span'];packed=np.frombuffer(raw,'u1',count=s['bytes'],offset=s['offset']).reshape(n,8).copy()
    assert np.array_equal(packed,want['packed_tangents'])
    s=details['uv_span'];dt='<f2' if s['bytes']//s['count']==4 else '<f4'
    tex=np.frombuffer(raw,dt,count=s['count']*2,offset=s['offset']).reshape(n,2,2).copy()
    assert np.array_equal(tex,want['uv'])
    fields={k:want[k] for k in want.files};fields.update(positions=pos,indices=indices,packed_tangents=packed,normals=packed[:,4:7].view('i1').astype(float)/127,uv=tex)
    np.savez_compressed(ROOT/'native/final-render.npz',**fields)
    for row in report['container_files']:assert sha(row['path'])==row['sha256']
    write(ROOT/'verification.json',dict(status='independent-final-container-verified-runtime-pending',passed=True,package_count=len(PACKAGES),packages=PACKAGES,
        textures=texture_records,surface_sha256=report['surface_sha256'],source_atlas_sha256=report['source_atlas_sha256'],
        source_iris_sha256=report['source_iris_sha256'],source_mix_sha256=report['source_mix_sha256'],
        positions_normals_iris_uv_final_readback_exact=True,all_other_native_bytes_exact=True,
        skirt_weights_physics_skeleton_indices_exact=True,native_material_payloads_retained=True,
        independent_cue_skeleton_and_sections_exact=True,original_shared_atlas_not_overridden=True,
        container_files=report['container_files'],installed=False,game_runtime_tested=False))
    print('FACE3_INDEPENDENTLY_VERIFIED',flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['verify']:verify()
    else:build();verify()
