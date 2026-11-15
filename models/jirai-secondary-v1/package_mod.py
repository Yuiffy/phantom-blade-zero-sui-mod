"""Build a self-contained model-only candidate using the verified native shader recipe."""
from pathlib import Path
import sys,json,shutil,os,subprocess
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-secondary-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');sys.path.insert(0,str(PBZ/'tools'))
import build_native_shader_assets as native
from package_model import relative_package
from ue_pipeline import game_pids,sha
WORK=ROOT/'variant';BASE=PBZ/'variants/native-shaders-v1';LEGACY=WORK/'legacy';TOOLS=native.TOOLS
NAME='z_Sui_HeiShang_Jirai_v1_P'
native.WORK=WORK;native.LEGACY=LEGACY
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2),encoding='utf8')
from offline_tools import native_run,isolated
native.run=native_run
run=native_run
def copyasset(source,dest):
    dest.parent.mkdir(parents=True,exist_ok=True)
    for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
        p=source.with_suffix(ext)
        if p.exists():shutil.copy2(p,dest.with_suffix(ext))
def main():
    if read(ROOT/'binding-report.json').get('runtime_retarget_verification_required'):
        gate=read(WORK/'shoulder-retarget-verification.json')
        assert gate.get('passed') and gate.get('fbx_sha256')==sha(ROOT/'Sui_Jirai_Hun_Body.fbx'), 'Moved shoulder pivots require animation retarget verification before packaging'
        assert read(WORK/'shoulder-rig/independent-verification.json')['passed']
    isolated();assert read(WORK/'logs/cook-exit.json')['exit_code']==0
    reload=read(WORK/'editor-reload-verification.json');assert reload['passed'] and reload['fbx_sha256']==sha(ROOT/'Sui_Jirai_Hun_Body.fbx')
    assert read(WORK/'simulation-validation.json')['fbx_sha256']==sha(ROOT/'Sui_Jirai_Hun_Body.fbx')
    spec=read(WORK/'material-spec.json');source=read(WORK/'source-spec.json')
    assert read(WORK/'import-report.json')['fbx_sha256']==source['fbx_sha256']==sha(Path(source['fbx']))
    fresh=[source['body_package'],'/HuaShira/Mods/SuiPBZ/Physics/PA_Jirai_ClothCollision']+[r['package'] for r in spec['textures']]
    project=WORK/'ue/ProjectPBZ';cooked=project/'Saved/Cooked/Windows';meta=cooked/'ProjectPBZ/Metadata'
    out=WORK/'cooked-container';out.mkdir(exist_ok=True);ctx=WORK/'pack-context';ctx.mkdir(exist_ok=True)
    response=[]
    for package in fresh:
        rel=relative_package(package);assert (cooked/(rel+'.uasset')).exists()
        for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
            p=cooked/(rel+ext)
            if p.exists():response.append(f'"{p}" "../../../{rel}{ext}" -compress')
    rsp=ctx/'response.txt';rsp.write_text('\n'.join(response)+'\n',encoding='utf8')
    commands=ctx/'commands.txt';commands.write_text(f'-Output="{out}/new_jirai.utoc" -ContainerName=new_jirai -ResponseFile="{rsp}"\n',encoding='utf8')
    run('pack-fresh',['F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealPak.exe',project/'ProjectPBZ.uproject',f'-CreateGlobalContainer={ctx}/global.utoc',f'-PackageStoreManifest={meta}/packagestore.manifest',f'-CookedDirectory={cooked}',f'-Commands={commands}',f'-ScriptObjects={meta}/scriptobjects.bin','-compressionformats=Oodle','-compresslevel=4','-compressmethod=Kraken','-platform=Windows','-unattended','-multiprocess=1'])
    inputs=WORK/'cooked-extract-input';inputs.mkdir(exist_ok=True)
    for folder in [out,ctx]:
        for p in folder.iterdir():
            if p.suffix in ['.utoc','.ucas']:shutil.copy2(p,inputs/p.name)
    extracted=WORK/'fresh-legacy';run('extract-fresh',[TOOLS/'retoc.exe','to-legacy','--version','UE5_7','--no-shaders','--no-parallel',inputs,extracted])
    assert {p.relative_to(extracted).as_posix() for p in extracted.rglob('*.uasset')}=={relative_package(n)+'.uasset' for n in fresh}
    for package in fresh:
        # A partial IoStore roundtrip cannot resolve external skeleton/physics/
        # material exports absent from the temporary container. Keep the new
        # mesh's original legacy cooked header and payload, including imports.
        src=cooked if package in [source['body_package'],'/HuaShira/Mods/SuiPBZ/Physics/PA_Jirai_ClothCollision'] else extracted
        copyasset(src/(relative_package(package)+'.uasset'),LEGACY/(relative_package(package)+'.uasset'))
    assert sha(LEGACY/(relative_package(source['body_package'])+'.uexp'))==sha(cooked/(relative_package(source['body_package'])+'.uexp'))
    # Keep the same proven outfit selectors and hidden mesh assets. Body geometry
    # is newly cooked; no stale native render payload is transplanted into it.
    baseline=read(BASE/'build-report.json')
    kept=[p for p in baseline['packages'] if ('/EscapeOnly/' in p and p!=source['body_package']) or p.endswith('/DT_PBZAppearanceTable')]
    hidden=next(m for m in read(BASE/'material-spec.json')['materials'] if m['slot']=='M_Sui_Hidden')
    kept+=['/HuaShira/Mods/SuiPBZ/Materials/M_Sui_Hidden']+list(hidden['textures'].values())
    assert len(kept)==len(set(kept))==11
    for package in kept:copyasset(BASE/'legacy'/(relative_package(package)+'.uasset'),LEGACY/(relative_package(package)+'.uasset'))
    native.materials()
    rig='/HuaShira/Mods/SuiPBZ/JiraiRig/Hun_Skin_Skeleton'
    copyasset(WORK/'shoulder-rig/native'/(relative_package(rig)+'.uasset'),LEGACY/(relative_package(rig)+'.uasset'))
    packages=sorted(fresh+kept+[rig]+['/HuaShira/Mods/SuiPBZ/Materials/'+m['slot'] for m in spec['materials']])
    assert len(packages)==len(set(packages))
    assert {p.relative_to(LEGACY).as_posix() for p in LEGACY.rglob('*.uasset')}=={relative_package(n)+'.uasset' for n in packages}
    container=WORK/'container';container.mkdir(exist_ok=True)
    run('pack-final',[TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',LEGACY,container/(NAME+'.utoc')])
    listing=run('list-final',[TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
    actual={line.split()[-1].replace('\\','/').removeprefix('../../../') for line in listing.splitlines() if line.strip().endswith('.uasset')}
    assert actual=={relative_package(n)+'.uasset' for n in packages}
    finalinput=WORK/'final-extract-input';finalinput.mkdir(exist_ok=True)
    for folder,stem in [(container,NAME),(Path('F:/FGames/steam/steamapps/common/PBZ/ProjectPBZ/Content/Paks'),'global')]:
        for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),finalinput/(stem+ext))
    final=WORK/'final-legacy';run('extract-final',[TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',finalinput,final])
    for package in packages:
        for ext in ['.uexp','.ubulk','.uptnl']:
            a=LEGACY/(relative_package(package)+ext);b=final/(relative_package(package)+ext)
            assert a.exists()==b.exists()
            if a.exists():assert a.read_bytes()==b.read_bytes(),(package,ext)
    write(WORK/'build-report.json',{'status':'packaged-awaiting-independent-verification','packages':packages,'package_count':len(packages),'reused_baseline_packages':kept,'body':source['body_package'],'triangles':source['expected_triangles'],'game_build':'26367565','installed':False,'runtime_tested':False,'container_files':[{'path':str(p.resolve()),'name':p.name,'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(container.iterdir())]})
    print(json.dumps({'packages':len(packages),'native_materials':len(spec['materials'])+1,'new_VT':len(spec['textures']),'installed':False}))
if __name__=='__main__':main()
