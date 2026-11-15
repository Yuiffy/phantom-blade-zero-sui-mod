from pathlib import Path
import sys,os,json,math,base64,struct,hashlib
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent;PBZ=ROOT.parents[2];sys.path.insert(0,str(PBZ/'tools'))
import run_native_diagnostic as diag
from package_model import relative_package
from ue_pipeline import sha,game_pids
from read_cooked_model import import_path
WORK=PBZ/'variants/new-jk-v11';BASE=PBZ/'variants/native-shaders-v1';OUT=WORK/'independent'
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
    assert len(skel['lods'][0]['sections'])==len(spec['materials'])
    props=docs[body][0]['Properties']
    for name,path in [('Skeleton','/HuaShira/Characters/Hero/Hero_Hun/Hun_Skin_Skeleton'),('PhysicsAsset','/HuaShira/Characters/Hero/Hero_Hun/PA_Hun'),('PostProcessAnimBlueprint','/HuaShira/Characters/Hero/Hero_Hun/Rig/ABP_Hun_PostProcess')]:
        assert props[name]['ObjectPath'].rsplit('.',1)[0]==path,(name,props[name])
    for package in build['reused_baseline_packages']:
        a=BASE/'legacy'/(relative_package(package)+'.uexp');b=WORK/'final-legacy'/(relative_package(package)+'.uexp');assert a.read_bytes()==b.read_bytes()
    for row in build['container_files']:assert sha(PBZ/row['path'])==row['sha256']
    report={'status':'independent-container-semantics-passed','package_count':build['package_count'],'triangles':build['triangles'],'body_bones':264,'material_slots':len(spec['materials']),'max_translation_error_cm':maxdist,'max_rotation_error_degrees':maxangle,'custom_shaders':0,'reused_outfit_table_and_hidden_parts_verified':True,'runtime_tested':False,'installed':False}
    write(WORK/'verification.json',report);print(json.dumps(report))
def skin():
    oldrun=native_run
    import build_native_shader_assets as native
    native.WORK=WORK
    body=read(WORK/'build-report.json')['body'];source=WORK/'final-legacy'/(relative_package(body)+'.uasset');dest=OUT/'body-uassetapi.json'
    oldrun('read-body-weights',[diag.TOOLS/'UAssetGUI.exe','tojson',source,dest,'VER_UE5_6','PBZ']);doc=read(dest)
    # Reuse the previously source-audited decoder, changing only section budget.
    import read_cooked_skin_weights as decoder
    import inspect
    code=inspect.getsource(decoder.parse).replace('assert count==14','assert count==len(spec["materials"])')
    def slots(d,raw,target,spec):
        count=struct.unpack_from('<i',raw,58)[0];assert count==len(spec['materials']);rows=[]
        for i in range(count):
            material,idx,number=struct.unpack_from('<3i',raw,62+44*i);name=d['NameMap'][idx]+('_'+str(number-1) if number else '')
            package='/HuaShira/Mods/SuiPBZ/Materials/'+name
            assert import_path(d,material)==package+'.'+name
            assert name in [m['slot'] for m in spec['materials']];rows.append(name)
        return rows,62+44*count
    scope=dict(vars(decoder));scope['skeletal_materials']=slots;exec(code,scope)
    pos,weights,indices,detail=scope['parse'](doc,{'package':body},read(WORK/'material-spec.json'))
    original=read(ROOT/'source-render-contract.json');points=np.array(original['positions_blender_cm']);points[:,1]*=-1
    tree=cKDTree(points);distance,_=tree.query(pos,workers=1);assert distance.max()<.001,float(distance.max())
    candidates=tree.query_ball_point(pos,r=.001,workers=1)
    # UE5.7.4 uses rounded/normalized uint16 weights, then truncates >>8
    # and gives the remaining 8-bit normalization units to the largest weight.
    # Follow the installed BoneWeights.h and SkeletalMeshLODRenderData.cpp.
    def quantized(wanted,raw_order=None):
        items=raw_order if raw_order is not None else sorted([(k,int(np.float32(np.float32(v)*np.float32(65535))+np.float32(.5))) for k,v in wanted.items()],key=lambda x:-x[1])
        items=[(k,v) for k,v in items if v>0];total=sum(v for k,v in items);carry=0;norm=[]
        for k,v in items:
            scaled=v*65535+carry;value=scaled//total;carry=scaled-value*total;norm.append((k,value))
        norm.sort(key=lambda x:-x[1])
        if detail['weight_denominator']==65535:return {k:v/65535 for k,v in norm if v}
        q={k:v>>8 for k,v in norm if v>>8}
        q[next(iter(q))]+=255-sum(q.values())
        return {k:v/255 for k,v in q.items()}
    quantized_source=[quantized(w) for w in original['influences']]
    tolerance=1e-7
    # BoneWeights.h DescSortByWeightPredicate compares RawWeight only;
    # equal uint16 weights have no bone-name tie breaker. Enumerate only
    # these exact ties, preserving the exact same integer normalization and
    # byte comparison. Do not widen the numeric tolerance for this case.
    import itertools
    def tied_variants(wanted):
        raw=sorted([(k,int(np.float32(np.float32(v)*np.float32(65535))+np.float32(.5))) for k,v in wanted.items()],key=lambda x:-x[1])
        groups=[list(g) for _,g in itertools.groupby(raw,key=lambda r:r[1])]
        if all(len(g)==1 for g in groups):return
        for combination in itertools.product(*(itertools.permutations(g) for g in groups)):
            yield quantized(wanted,[item for group in combination for item in group])
    max_error=0;max_source_error=0;matched=set();failures=[];tie_order_vertices=0
    for i,(row,choices) in enumerate(zip(weights,candidates)):
        good=[]
        for j in choices:
            wanted=quantized_source[j];err=max(abs(row.get(k,0)-wanted.get(k,0)) for k in row.keys()|wanted.keys())
            if err<=tolerance:good.append((j,err))
        if not good:
            for j in choices:
                for wanted in tied_variants(original['influences'][j]):
                    err=max(abs(row.get(k,0)-wanted.get(k,0)) for k in row.keys()|wanted.keys())
                    if err<=tolerance:good.append((j,err));break
            if good:tie_order_vertices+=1
        if not good:
            failures.append({'vertex':i,'actual':row,'source_candidates':[original['influences'][j] for j in choices[:3]],'expected_quantized':[quantized_source[j] for j in choices[:3]]})
            continue
        matched.update(j for j,_ in good);max_error=max(max_error,min(err for _,err in good))
        max_source_error=max(max_source_error,min(max(abs(row.get(k,0)-original['influences'][j].get(k,0)) for k in row.keys()|original['influences'][j].keys()) for j,_ in good))
    if failures:
        write(WORK/'weight-comparison-diagnostic.json',{'failure_count':len(failures),'render_vertices':len(pos),'weight_denominator':detail['weight_denominator'],'max_influences':detail['max_influences'],'samples':failures[:50]})
        raise AssertionError(('Weight comparison',len(failures),'see weight-comparison-diagnostic.json'))
    assert len(matched)==len(points),(len(matched),len(points))
    report={'status':'final-cooked-render-vertices-and-weights-match-refined-source','render_vertices':len(pos),'source_vertices_matched':len(matched),'triangles':len(indices)//3,'max_position_error_cm':float(distance.max()),'max_weight_error_after_UE_quantization':max_error,'max_weight_difference_from_float_source':max_source_error,'weight_tolerance':tolerance,'weight_comparison':'reproduce installed UE16 normalization and UE8 truncation plus dominant-weight remainder','max_influences':detail['max_influences'],'source_contract_sha256':sha(ROOT/'source-render-contract.json'),'body_readback_sha256':sha(dest),'runtime_tested':False}
    report['equal_uint16_weight_tie_order_vertices']=tie_order_vertices
    report['tie_order_rule']='Only permutations of equal rounded uint16 source weights; same exact normalization, same 1e-7 tolerance'
    write(WORK/'skin-verification.json',report);print(json.dumps(report))
if __name__=='__main__':
    isolated()
    {'gather':gather,'validate':validate,'skin':skin}[sys.argv[1]]()
