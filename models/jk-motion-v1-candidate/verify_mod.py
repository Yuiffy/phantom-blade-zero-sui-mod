from pathlib import Path
import sys,os,json,math,base64,struct,hashlib
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];sys.path.insert(0,str(PBZ/'tools'))
import run_native_diagnostic as diag
from package_model import relative_package
from ue_pipeline import sha,game_pids
from read_cooked_model import import_path
WORK=PBZ/'variants/jk-motion-v1';BASE=PBZ/'variants/native-shaders-v1';OUT=WORK/'independent'
from offline_tools import diagnostic_run,native_run,isolated
diag.run=diagnostic_run
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2),encoding='utf8')
def gather():
    OUT.mkdir(exist_ok=True);diag.OUT=OUT
    env=dict(os.environ,DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1',DOTNET_PROCESSOR_COUNT='2',PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=str(WORK/'container'))
    build=read(WORK/'build-report.json');packages=[relative_package(p) for p in build['packages']]
    diag.run('all-assets',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',OUT/'json','json',*packages],env)
    meshes=[p for p in packages if '/EscapeOnly/' in p]
    diag.run('skeletons',[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',OUT/'skel','skel',*meshes],env)
def validate():
    build=read(WORK/'build-report.json');spec=read(WORK/'material-spec.json');docs={}
    for label in ['all-assets','skeletons']:
        result=read(OUT/(label+'.result.json'));assert result['exit_code']==0 and not result['parser_warnings_or_errors'],result
    for package in build['packages']:
        exports=read(OUT/'json'/(relative_package(package)+'.json'));assert exports and not any(e['Type']=='Material' for e in exports)
        docs[package]=exports
    hidden=next(m for m in read(BASE/'material-spec.json')['materials'] if m['slot']=='M_Sui_Hidden')
    for m in spec['materials']+[hidden]:
        package='/HuaShira/Mods/SuiPBZ/Materials/'+m['slot'];e,=docs[package];p=e['Properties']
        assert e['Type']=='MaterialInstanceConstant' and p['Parent']['ObjectPath']==m['parent']+'.0'
        assert not p.get('bHasStaticPermutationResource',False) and e['LoadedMaterialResources']==[] and e['CachedData']['ParentLayerIndexRemap']==[0,1]
        actual={}
        for v in p['TextureParameterValues']:
            info=v['ParameterInfo'];assert info['Association'].split('::')[-1]=='LayerParameter' and info['Index']==0
            actual[info['Name']]=v['ParameterValue']['ObjectPath'].rsplit('.',1)[0]
        assert actual==m['textures']
    for package,ex in docs.items():
        e=ex[0]
        if e['Type']=='Texture2D':
            assert e['Properties']['VirtualTextureStreaming'];vt=e['VTData'];assert vt['NumMips']>0 and vt['Chunks']
            bulk=WORK/'final-legacy'/(relative_package(package)+'.ubulk');assert bulk.is_file()
            for ch in vt['Chunks']:
                d=ch['BulkData'];off=int(d['OffsetInFile'],16);assert 0<=off and off+d['SizeOnDisk']<=bulk.stat().st_size
    body=build['body'];skel=read(OUT/'skel'/(relative_package(body)+'.Hun_Body_Simple.skel.json'))
    expected=read(PBZ/'models/hun-body.skel.json')['bones'];actual=skel['bones'];assert len(actual)==len(expected)==264
    byname={b['name'].lower():b for b in actual};maxdist=maxangle=maxscale=0.
    for b in expected:
        a=byname[b['name'].lower()]
        assert (actual[a['parent']]['name'].lower() if a['parent']>=0 else None)==(expected[b['parent']]['name'].lower() if b['parent']>=0 else None)
        maxdist=max(maxdist,math.dist(a['t'],b['t']));maxscale=max(maxscale,max(abs(x-y) for x,y in zip(a['s'],b['s'])))
        dot=abs(sum(x*y for x,y in zip(a['q'],b['q'])))/math.sqrt(sum(x*x for x in a['q'])*sum(x*x for x in b['q']))
        maxangle=max(maxangle,math.degrees(2*math.acos(min(1,dot))))
    assert maxdist<.02 and maxangle<.1 and maxscale<.001,(maxdist,maxangle,maxscale)
    assert sum(s['NumTriangles'] for s in skel['lods'][0]['sections'])==build['triangles']
    assert len(skel['lods'][0]['sections'])==24
    props=next(e for e in docs[body] if e['Type']=='SkeletalMesh' and e['Name']=='Hun_Body_Simple')['Properties']
    for name,path in [('Skeleton','/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton'),('PhysicsAsset','/HuaShira/Characters/Hero/Hero_Hun/PA_Hun'),('PostProcessAnimBlueprint','/HuaShira/Characters/Hero/Hero_Hun/Rig/ABP_Hun_PostProcess')]:
        assert props[name]['ObjectPath'].rsplit('.',1)[0]==path,(name,props[name])
    for package in build['reused_baseline_packages']:
        a=BASE/'legacy'/(relative_package(package)+'.uexp');b=WORK/'final-legacy'/(relative_package(package)+'.uexp');assert a.read_bytes()==b.read_bytes()
    for row in build['container_files']:assert sha(PBZ/row['path'])==row['sha256']
    report={'status':'independent-container-semantics-passed','package_count':build['package_count'],'triangles':build['triangles'],'body_bones':264,'material_slots':len(spec['materials']),'max_translation_error_cm':maxdist,'max_rotation_error_degrees':maxangle,'custom_shaders':0,'reused_outfit_table_and_hidden_parts_verified':True,'runtime_tested':False,'installed':False}
    write(WORK/'verification.json',report);print(json.dumps(report))
def body_json():
    import run_native_diagnostic as diag
    source=WORK/'final-legacy'/(relative_package(read(WORK/'build-report.json')['body'])+'.uasset')
    native_run('read-body-cloth',[diag.TOOLS/'UAssetGUI.exe','tojson',source,OUT/'body-uassetapi.json','VER_UE5_6','PBZ'])
    assert (OUT/'body-uassetapi.json').is_file()
if __name__=='__main__':
    isolated()
    {'gather':gather,'validate':validate,'body':body_json}[sys.argv[1]]()
