"""Change one VT package in the installed 99-package skin/eye baseline."""
from common import *
import shutil

def snapshot():
    return [dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted((diag.PAKS/'~mods').iterdir()) if p.is_file()]

def build():
    assert not (ROOT/'build-report.json').exists(),'Candidate exists; use verify'
    baseline=read(BASE/'build-report.json');gate=read(BASE/'verification.json')
    assert gate['status']=='independent-final-container-verified-runtime-pending'
    for f in baseline['container_files']:
        assert sha(f['path'])==f['sha256']
        assert sha(diag.PAKS/'~mods'/f['name'])==f['sha256'],'Rebase onto the current installed model'
    write(ROOT/'installed-before.json',snapshot())
    assert read(ROOT/'cook-report.json')['passed']
    assert read(ROOT/'cook-report.json')['input_sha256']==sha(ROOT/'T_Jirai_Base.png')==read(ROOT/'atlas-report.json')['output_sha256']
    cooked=PROJECT.parent/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata'
    ctx=ROOT/'pack-context';ctx.mkdir(exist_ok=True);fresh=ROOT/'cooked-container';fresh.mkdir(exist_ok=True)
    rows=[]
    for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
        p=cooked/(relative_package(PACKAGE)+ext)
        if p.exists():rows.append(f'"{p}" "../../../{relative_package(PACKAGE)}{ext}" -compress')
    rsp=ctx/'response.txt';rsp.write_text('\n'.join(rows)+'\n',encoding='utf8')
    cmd=ctx/'commands.txt';cmd.write_text(f'-Output="{fresh}/fishnet.utoc" -ContainerName=fishnet -ResponseFile="{rsp}"\n',encoding='utf8')
    run('pack-fresh',[UE.parent/'UnrealPak.exe',PROJECT,f'-CreateGlobalContainer={ctx}/global.utoc',
        f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',
        f'-Commands={cmd}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle',
        '-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
    inputs=ROOT/'fresh-input';inputs.mkdir(exist_ok=True)
    for folder in [fresh,ctx]:
        for p in folder.iterdir():
            if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,inputs/p.name)
    extracted=ROOT/'fresh-legacy'
    run('extract-fresh',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,extracted])
    assert {p.relative_to(extracted).as_posix() for p in extracted.rglob('*.uasset')}=={relative_package(PACKAGE)+'.uasset'}
    legacy=ROOT/'legacy'
    for p in baseline['packages']:copyasset(extracted if p==PACKAGE else BASE/'legacy',legacy,p)
    container=ROOT/'container';container.mkdir(exist_ok=True)
    run('pack-final',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',legacy,container/(NAME+'.utoc')])
    listing=run('list-final',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
    assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in baseline['packages']}
    inputs=ROOT/'final-input';inputs.mkdir(exist_ok=True)
    for folder,stem in [(container,NAME),(diag.PAKS,'global')]:
        for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),inputs/(stem+ext))
    run('extract-final',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inputs,ROOT/'final-legacy'])
    for p in baseline['packages']:
        for ext in ['.uexp','.ubulk','.uptnl']:
            a=legacy/(relative_package(p)+ext);b=ROOT/'final-legacy'/(relative_package(p)+ext)
            assert a.exists()==b.exists()
            if a.exists():assert sha(a)==sha(b),(p,ext)
    report=dict(status='packaged-awaiting-independent-verification',game_build='26367565',
        packages=baseline['packages'],package_count=len(baseline['packages']),changed_packages=[PACKAGE],
        preserved_packages=[p for p in baseline['packages'] if p!=PACKAGE],outfits=baseline['outfits'],
        baseline_container_files=baseline['container_files'],source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),
        container_files=[dict(path=str(p.resolve()),name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],
        installed=False,game_runtime_tested=False)
    write(ROOT/'build-report.json',report)
    print('FISHNET_FINAL_PACKAGED',report['package_count'],flush=True)

def verify():
    report=read(ROOT/'build-report.json')
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',
        PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=str(ROOT/'container'))
    output=run('independent-json',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',
        ROOT/'independent/json','json',*[relative_package(p) for p in report['packages']]],env)
    assert not any(x in output for x in ['Failed to','Exception','[WRN]','[ERR]'])
    preserved=[]
    for p in report['preserved_packages']:
        want=read(BASE/'independent/json'/(relative_package(p)+'.json'))
        got=read(ROOT/'independent/json'/(relative_package(p)+'.json'))
        assert want==got,('unrelated semantic change',p)
        hashes={}
        for ext in ['.uexp','.ubulk','.uptnl']:
            a=BASE/'legacy'/(relative_package(p)+ext);b=ROOT/'final-legacy'/(relative_package(p)+ext)
            assert a.exists()==b.exists()
            if a.exists():assert sha(a)==sha(b);hashes[ext]=sha(b)
        preserved.append(dict(package=p,payload_sha256=hashes))
    e,=read(ROOT/'independent/json'/(relative_package(PACKAGE)+'.json'))
    assert e['Type']=='Texture2D' and e['Properties']['VirtualTextureStreaming']
    assert e['Properties'].get('SRGB',True)
    vt=e['VTData'];assert vt['Width']==vt['Height']==8192,vt
    assert vt['NumMips']>=13 and vt['Chunks'] and vt['LayerTypes']==['PF_DXT1']
    bulk=ROOT/'final-legacy'/(relative_package(PACKAGE)+'.ubulk')
    for ch in vt['Chunks']:
        b=ch['BulkData'];off=int(b['OffsetInFile'],16)
        assert 0<=off and off+b['SizeOnDisk']<=bulk.stat().st_size
    for f in report['container_files']:assert sha(f['path'])==f['sha256']
    write(ROOT/'preserved-payloads.json',preserved)
    write(ROOT/'verification.json',dict(status='independent-final-container-verified-runtime-pending',
        package_count=report['package_count'],modified_texture_packages=1,preserved_packages=len(preserved),
        all_meshes_uv_weights_and_cloth_payloads_unchanged=True,all_materials_and_appearance_rows_unchanged=True,
        skin_and_closed_sclera_fixes_preserved=True,jk_unchanged=True,texture_width=8192,texture_height=8192,
        virtual_texture=True,srgb=True,texture_format=vt['LayerTypes'],mips=vt['NumMips'],bulk_bounds_checked=True,
        source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),container_files=report['container_files'],
        installed=False,game_runtime_tested=False))
    print('FISHNET_INDEPENDENT_VERIFIED',len(preserved),'UNCHANGED_PACKAGES',flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['verify']:verify()
    else:build();verify()
