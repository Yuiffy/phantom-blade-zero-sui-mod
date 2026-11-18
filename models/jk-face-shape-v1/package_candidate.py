"""One-mesh overlay; preserve every original export byte outside face buffers."""
from common import *
import base64, importlib.util, inspect, shutil
import numpy as np

def unpack(doc):
    return base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])

def parse(doc):
    path=PBZ/'models/new-outfit-20261114/tripo-motion-v5/decode_cloth_body.py'
    spec=importlib.util.spec_from_file_location('jk_cloth_decoder',path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    code=inspect.getsource(mod.decoder.parse).replace('assert count==14','assert count==24')
    scope=dict(vars(mod.decoder));scope.update(section=mod.section,skeletal_materials=mod.materials);exec(code,scope)
    return scope['parse'](doc,dict(package=BODY),read(JK/'material-spec.json'))

def cue(label, dirs, packages, mode='json'):
    dest=ROOT/'independent'/label
    env=dict(PBZX_GAME='GAME_UE5_7',PBZX_SCRIPT='1',PBZX_AES=diag.private_key(),PBZX_EXTRA=';'.join(str(p) for p in dirs),DOTNET_CLI_TELEMETRY_OPTOUT='1',DOTNET_NOLOGO='1')
    output=run('cue-'+label,[diag.DOTNET,diag.DLL,diag.PAKS,diag.MAPPING,diag.TOOLS/'oo2core_9_win64.dll',dest,mode,*[relative_package(p) for p in packages]],env)
    assert not any(s in output for s in ['Failed to','Exception','[WRN]','[ERR]']),label
    return {p:read(dest/(relative_package(p)+'.json')) for p in packages} if mode=='json' else dest

def patch():
    assert_baseline();assert read(ROOT/'author-report.json')['authored_sha256']==sha(ROOT/'authored.npz')
    dest=ROOT/'legacy'/(relative_package(BODY)+'.uasset');dest.parent.mkdir(parents=True,exist_ok=True)
    for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
        p=SOURCE.with_suffix(ext)
        if p.exists():shutil.copy2(p,dest.with_suffix(ext))
    docpath=ROOT/'native/source.json';docpath.parent.mkdir(parents=True,exist_ok=True)
    run('source-json',[diag.TOOLS/'UAssetGUI.exe','tojson',SOURCE,docpath,'VER_UE5_6','PBZ'])
    doc=read(docpath);pos,weights,idx,detail=parse(doc);raw=unpack(doc)
    before=np.load(ROOT/'before.npz');after=np.load(ROOT/'authored.npz')
    assert np.array_equal(pos,before['positions']) and np.array_equal(idx,before['indices'])
    selected=np.where(after['changed'])[0];assert len(selected)>300
    assert all(weights[i]=={'head':1.0} for i in selected), 'Only rigid head surface may change'
    edited=bytearray(raw);allowed=np.zeros(len(raw),bool)
    for key,span,stride in [('positions',detail['position_span'],12),('packed_tangents',detail['tangent_span'],8)]:
        value=after[key].tobytes();assert len(value)==span['bytes']
        for i in selected:
            at=span['offset']+int(i)*stride;edited[at:at+stride]=value[int(i)*stride:(int(i)+1)*stride];allowed[at:at+stride]=True
    changed=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1')
    assert changed.any() and np.all(allowed[changed])
    payload=SOURCE.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1
    at=payload.index(raw);result=payload[:at]+edited+payload[at+len(raw):]
    assert len(result)==len(payload)
    dest.with_suffix('.uexp').write_bytes(result)
    assert sha(dest)==sha(SOURCE)
    np.savez_compressed(ROOT/'allowed-bytes.npz',mask=allowed)
    write(ROOT/'patch-report.json',dict(passed=True,source_header_sha256=sha(SOURCE),output_header_sha256=sha(dest),source_payload_sha256=sha(SOURCE.with_suffix('.uexp')),output_payload_sha256=sha(dest.with_suffix('.uexp')),changed_native_bytes=int(changed.sum()),changed_position_vertices=len(selected),only_head_position_tangent_bytes_changed=True,other_export_bytes_exact=True))
    print('JK_FACE_NATIVE_PATCHED',len(selected),flush=True)

def build():
    assert_baseline();patch()
    container=ROOT/'container';container.mkdir(exist_ok=True)
    run('pack',[diag.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',ROOT/'legacy',container/(NAME+'.utoc')])
    listing=run('list',[diag.TOOLS/'retoc.exe','list','--path',container/(NAME+'.utoc')])
    assert {s.split()[-1].replace('\\','/').removeprefix('../../../') for s in listing.splitlines() if s.strip().endswith('.uasset')}=={relative_package(BODY)+'.uasset'}
    write(ROOT/'build-report.json',dict(passed=True,package_count=1,package=BODY,authored_sha256=sha(ROOT/'authored.npz'),container_files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())]))
    print('JK_FACE_PACKAGED',flush=True)

def verify(installed=False):
    report=read(ROOT/'build-report.json');assert report['authored_sha256']==sha(ROOT/'authored.npz')
    for row in report['container_files']:assert sha(ROOT/'container'/row['name'])==row['sha256']
    assert_baseline() if not installed else None
    context=ROOT/('installed-input' if installed else 'resolved-input');context.mkdir(exist_ok=True)
    dirs=[MODS] if installed else [MODS,ROOT/'container']
    for directory in dirs:
        for p in directory.iterdir():
            if p.suffix in ['.ucas','.utoc']:shutil.copy2(p,context/p.name)
    for ext in ['.ucas','.utoc']:shutil.copy2(diag.PAKS/('global'+ext),context/('global'+ext))
    legacy=ROOT/('installed-readback' if installed else 'final-legacy')
    run('extract-installed' if installed else 'extract',[diag.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',context,legacy])
    output=legacy/(relative_package(BODY)+'.uasset');expect=ROOT/'legacy'/(relative_package(BODY)+'.uasset')
    assert sha(output.with_suffix('.uexp'))==sha(expect.with_suffix('.uexp')),'Overlay body was shadowed'
    docpath=ROOT/'native'/('installed.json' if installed else 'final.json')
    run('installed-json' if installed else 'final-json',[diag.TOOLS/'UAssetGUI.exe','tojson',output,docpath,'VER_UE5_6','PBZ'])
    doc=read(docpath);base=read(ROOT/'native/source.json')
    pos,weights,idx,detail=parse(doc);op,ow,oi,od=parse(base)
    raw=unpack(doc);old=unpack(base);allowed=np.load(ROOT/'allowed-bytes.npz')['mask']
    assert len(raw)==len(old)
    actual=np.frombuffer(raw,'u1')!=np.frombuffer(old,'u1');assert np.all(allowed[actual]) and actual.any()
    assert weights==ow and np.array_equal(idx,oi)
    assert {k:v for k,v in detail.items() if k!='raw_native_export_sha256'}=={k:v for k,v in od.items() if k!='raw_native_export_sha256'}
    authored=np.load(ROOT/'authored.npz');assert np.array_equal(pos,authored['positions'])
    n=len(pos);span=detail['tangent_span'];frames=np.frombuffer(raw,'u1',count=span['bytes'],offset=span['offset']).reshape(n,8)
    assert np.array_equal(frames,authored['packed_tangents'])
    fields={k:authored[k] for k in authored.files};fields.update(positions=pos,packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127)
    np.savez_compressed(ROOT/'final.npz',**fields)
    # All retained package payloads, including Jirai, both 8K pattern atlases,
    # material definitions and the appearance table, must resolve identically.
    preserved=[];source=REPO/'private/outfit-patterns-v1/installed-readback'
    for p in source.rglob('*.uasset'):
        rel=p.relative_to(source)
        if rel.as_posix()==relative_package(BODY)+'.uasset':continue
        for ext in ['.uexp','.ubulk','.uptnl']:
            a=p.with_suffix(ext);b=(legacy/rel).with_suffix(ext)
            assert a.exists()==b.exists(),str(rel)
            if a.exists():assert sha(a)==sha(b),str(rel)
        preserved.append(rel.as_posix())
    assert len(preserved)>=100
    label='installed' if installed else 'candidate'
    got=cue(label,dirs,[BODY])
    if not installed:
        a=cue('order-a',[MODS,ROOT/'container'],[BODY])
        b=cue('order-b',[ROOT/'container',MODS],[BODY])
        assert a==b==got
    write(ROOT/('installed-verification.json' if installed else 'verification.json'),dict(passed=True,package_count=1,package=BODY,container_files=report['container_files'],native_render_sha256=sha(ROOT/'final.npz'),changed_vertices=int(authored['changed'].sum()),all_other_native_export_bytes_exact=True,uv_indices_weights_skeleton_cloth_physics_exact=True,preserved_package_count=len(preserved),directory_order_independent=True,eyes_mouth_and_all_other_components_exact=True,authored_sha256=report['authored_sha256'],game_runtime_tested=False))
    print('JK_FACE_INDEPENDENTLY_VERIFIED',label,len(preserved),flush=True)

if __name__=='__main__':
    if sys.argv[1:]==['installed']:verify(True)
    elif sys.argv[1:]==['verify']:verify()
    else:build();verify()
