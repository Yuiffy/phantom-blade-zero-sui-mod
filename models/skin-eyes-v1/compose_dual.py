"""Compose the verified eye repair and both outfits' material correction."""
from common import *
from material_recipe import configure, build_rows, SKIN
import importlib.util, shutil, copy

BASE = REPO/'private/jirai-detail-v1/dual'
V = ROOT/'variant'; OUT = ROOT/'dual'
MODS = diag.PAKS/'~mods'
OLD = '/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'
NEW = '/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple'
NAME = 'z_Sui_DualOutfit_JK5_JiraiR6_SkinEyes1_P'
EXTS = ['.uasset','.uexp','.ubulk','.uptnl']
loader=importlib.util.spec_from_file_location('dual_tools',REPO/'models/dual-outfit-v2/build.py')
B=importlib.util.module_from_spec(loader);loader.loader.exec_module(B);B.WORK=OUT

def jirai(p):
    return any(s in p for s in ['/JiraiVT/','/JiraiRig/','/Materials/MI_Jirai_']) or p.endswith('/Physics/PA_Jirai_ClothCollision') or p==NEW

def payload_equal(a_root, a_pkg, b_pkg=None):
    for ext in EXTS[1:]:
        a=a_root/(relative_package(a_pkg)+ext);b=OUT/'final-legacy'/(relative_package(b_pkg or a_pkg)+ext)
        assert a.exists()==b.exists(),(a_pkg,ext)
        if a.exists(): assert sha(a)==sha(b),(a_pkg,ext)

def substitute(value):
    if isinstance(value,dict):return {k:substitute(v) for k,v in value.items()}
    if isinstance(value,list):return [substitute(v) for v in value]
    return value.replace(OLD,NEW) if isinstance(value,str) else value

def build():
    OUT.mkdir(exist_ok=True)
    assert not (OUT/'build-report.json').exists(),'Use verify for an existing final candidate'
    a=read(BASE/'build-report.json'); fresh=read(V/'build-report.json')
    assert read(BASE/'verification.json')['status']=='independent-final-container-verified-runtime-pending'
    assert read(V/'verification.json')['status']=='independent-container-semantics-passed'
    assert read(V/'cloth-assets-verification.json')['status']=='final-container-cloth-config-and-collision-readback-passed'
    assert read(ROOT/'source-preservation.json')['source_fbx_sha256']==sha(ROOT/'Sui_Jirai_Hun_Body.fbx')
    assert read(ROOT/'source-preservation.json')['all_original_positions_uv_weights_preserved']
    assert read(V/'eye-geometry-verification.json')['passed']
    assert read(V/'eye-geometry-verification.json')['source_fbx_sha256']==sha(ROOT/'Sui_Jirai_Hun_Body.fbx')
    for f in read(BASE/'verification.json')['container_files']:
        assert sha(Path(f['path']))==f['sha256']
        assert (MODS/f['name']).is_file() and sha(MODS/f['name'])==f['sha256'], 'Installed model changed; rebase before staging this full replacement'
    for f in fresh['container_files']:assert sha(Path(f['path']))==f['sha256']
    snapshot=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]
    write(OUT/'installed-before.json',snapshot)
    # Include the current verified R6 baseline as a full replacement container.
    keep=set(a['packages'])-{p for p in a['packages'] if jirai(p)}
    new={p for p in fresh['packages'] if jirai(p)};new.add(NEW)
    for p in sorted(keep):B.copyasset(BASE/'legacy',p)
    for p in sorted(new-{NEW}):B.copyasset(V/'legacy',p)
    src=V/'legacy'/(relative_package(OLD)+'.uasset')
    original_json=OUT/'body-original.json'
    run('dual-body-original',[diag.TOOLS/'UAssetGUI.exe','tojson',src,original_json,'VER_UE5_6','PBZ'])
    original=read(original_json);edited=B.replace(original,{OLD:NEW})
    path=OUT/'body-edited.json';write(path,edited)
    target=OUT/'legacy'/(relative_package(NEW)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
    run('dual-body-relocate',[diag.TOOLS/'UAssetGUI.exe','fromjson',path,target,'PBZ'])
    generated=OUT/'body-generated.json'
    run('dual-body-generated',[diag.TOOLS/'UAssetGUI.exe','tojson',target,generated,'VER_UE5_6','PBZ'])
    relocation=B.restore(src,target,original,read(generated))
    for ext in ['.ubulk','.uptnl']:
        if src.with_suffix(ext).exists():shutil.copy2(src.with_suffix(ext),target.with_suffix(ext))
    assert src.with_suffix('.uexp').read_bytes()==target.with_suffix('.uexp').read_bytes()
    jk=read(PBZ/'variants/jk-motion-v5/material-spec.json')['materials']
    jk=[configure(copy.deepcopy(m)) for m in jk]
    for m in jk:
        # JK's residual atlas slot includes several kinds of surfaces. Use a
        # smooth native lit shader there; do not claim a dedicated JK skin split.
        if m['slot']=='MI_JK_Base':
            m['textures']['Mix']='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_ARM_Skin'
    write(OUT/'jk-material-spec.json',dict(materials=jk))
    build_rows(jk,OUT,OUT/'legacy')
    changed={'/HuaShira/Mods/SuiPBZ/Materials/'+m['slot'] for m in jk}
    assert changed<=keep
    packages=sorted(keep|new)
    assert {p.relative_to(OUT/'legacy').as_posix() for p in (OUT/'legacy').rglob('*.uasset')}=={relative_package(p)+'.uasset' for p in packages}
    container=OUT/'container';container.mkdir(exist_ok=True)
    run('dual-pack',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',OUT/'legacy',container/(NAME+'.utoc')])
    listing=run('dual-list',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
    assert {l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')}=={relative_package(p)+'.uasset' for p in packages}
    inputs=OUT/'extract-input';inputs.mkdir(exist_ok=True)
    for folder,stem in [(container,NAME),(diag.PAKS,'global')]:
        for ext in ['.utoc','.ucas']:shutil.copy2(folder/(stem+ext),inputs/(stem+ext))
    run('dual-extract',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inputs,OUT/'final-legacy'])
    for p in keep-changed:payload_equal(BASE/'legacy',p)
    for p in changed:payload_equal(OUT/'legacy',p)
    for p in new:payload_equal(V/'legacy',OLD if p==NEW else p,p)
    write(OUT/'build-report.json',dict(status='packaged-awaiting-independent-verification',
        game_build='26367565',packages=packages,package_count=len(packages),
        preserved_packages=sorted(keep-changed),modified_jk_materials=sorted(changed),jirai_packages=sorted(new),
        outfits=a['outfits'],body_relocation=relocation,source_fbx_sha256=sha(ROOT/'Sui_Jirai_Hun_Body.fbx'),
        container_files=[dict(name=p.name,path=str(p.resolve()),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())],
        installed=False,game_runtime_tested=False))

def verify_material(m,doc):
    e,=doc;p=e['Properties']
    assert e['Type']=='MaterialInstanceConstant'
    assert p['Parent']['ObjectPath']==m['parent']+'.0'
    assert not p.get('bHasStaticPermutationResource',False) and e['LoadedMaterialResources']==[]
    assert e['CachedData']['ParentLayerIndexRemap']==m['layer_remap']
    texture={}
    for row in p['TextureParameterValues']:
        info=row['ParameterInfo'];assert info['Association'].split('::')[-1]=='LayerParameter' and info['Index']==0
        texture[info['Name']]=row['ParameterValue']['ObjectPath'].rsplit('.',1)[0]
    assert texture==m['textures'],m['slot']
    scalars={(x['ParameterInfo']['Name'],x['ParameterInfo']['Index']):x['ParameterValue'] for x in p['ScalarParameterValues']}
    for name,value,layer in m['scalars']:assert abs(scalars[(name,layer)]-value)<1e-5
    if m['parent']==SKIN:
        vec=next(x for x in p['VectorParameterValues'] if x['ParameterInfo']['Name']=='Albedo Controls')['ParameterValue']
        assert [vec[k] for k in ['R','G','B','A']]==[1,1,1,0]

def verify():
    report=read(OUT/'build-report.json')
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',
        PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=str(OUT/'container'))
    for mode,packages in [('json',report['packages']),('skel',[OLD,NEW])]:
        log=run('dual-independent-'+mode,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',OUT/'independent'/mode,mode,*[relative_package(p) for p in packages]],env)
        assert not any(x in log for x in ['Failed to','Exception','[WRN]','[ERR]'])
    jk={m['slot']:m for m in read(OUT/'jk-material-spec.json')['materials']}
    materials={m['slot']:m for m in read(V/'material-spec.json')['materials']}
    for p in report['packages']:
        actual=read(OUT/'independent/json'/(relative_package(p)+'.json'))
        assert not any(e['Type']=='Material' for e in actual)
        slot=p.rsplit('/',1)[-1]
        if p in report['modified_jk_materials']:verify_material(jk[slot],actual)
        else:
            root=BASE if p in report['preserved_packages'] else V
            source=OLD if p==NEW else p
            expected=read(root/'independent/json'/(relative_package(source)+'.json'))
            if p==NEW:expected=substitute(expected)
            assert expected==actual,('semantic mismatch',p)
            if slot in materials:verify_material(materials[slot],actual)
    for p,root,sp in [(OLD,BASE,OLD),(NEW,V,OLD)]:
        got=read(OUT/'independent/skel'/(relative_package(p)+'.Hun_Body_Simple.skel.json'))
        want=read(root/'independent/skel'/(relative_package(sp)+'.Hun_Body_Simple.skel.json'))
        assert got['bones']==want['bones'] and got['lods']==want['lods']
    for f in report['container_files']:assert sha(f['path'])==f['sha256']
    write(OUT/'verification.json',dict(status='independent-final-container-verified-runtime-pending',
        package_count=report['package_count'],preserved_packages=len(report['preserved_packages']),
        jk_geometry_and_cloth_payloads_unchanged=True,all_appearance_rows_unchanged=True,
        jirai_original_positions_uv_weights_preserved=True,closed_sclera_added=2,
        native_skin_slots=['MI_Jirai_Skin','MI_Jirai_Hands'],
        jk_base_uses_smooth_native_lit_shader=True,jk_has_dedicated_skin_split=False,
        custom_shaders=0,container_files=report['container_files'],installed=False,game_runtime_tested=False))
    print('DUAL_SKIN_EYES_VERIFIED',report['package_count'])

if __name__=='__main__':
    if sys.argv[1:]==['verify']:verify()
    else:build();verify()
