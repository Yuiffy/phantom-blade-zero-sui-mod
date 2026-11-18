"""Compose the three reduced physical LODs and their render maps onto the live JK body."""
import copy
import shutil
import struct
import sys

import numpy as np
from measure import base, common, prior, root, code
import compose
import package_verify
from native import decode, unpack, DT

compose.W = package_verify.W = root
read, write, sha = common.read, common.write, common.sha
body = common.BODY
relative = common.relative_package(body) + '.uasset'
name = 'zzzzzzzzzzzz_Sui_JKOutfitPerf2_13_P'
stage = root/'reduced-full'


def build():
    before = common.snapshot()
    source = compose.extract('before',[common.MODS])/relative
    original = compose.tojson('before',source)
    cooked = compose.tojson('cooked',base.project/'Saved/Cooked/Windows'/relative)
    positions, _, _, details = decode(original)
    document = copy.deepcopy(original)
    raw = bytearray(unpack(original))
    phys = read(stage/'cloth-details.json')['assets']
    changes, mapping_stats = {}, {}
    for section in details['sections']:
        index = section['cloth_index']
        if index not in (1,3,4):
            continue
        asset=phys[index]
        n=asset['name']
        target=read(root/'guides'/(n+'-map.json'))
        start,count=section['base_vertex'],section['vertices']
        rest=positions[start:start+count]
        assert np.allclose(rest,target['positions'],atol=.0001,rtol=0), n
        records=np.zeros(count,dtype=DT)
        for key in ('position','normal','tangent','source','weight'):
            records[key]=[row[key] for row in target['mapping']]
        ids=records['source'][:,:3]
        q=np.array(asset['positions'])
        tri=np.array(asset['indices']).reshape(-1,3)
        assert ids.max()<len(q)
        normals=np.zeros_like(q)
        cross=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]])
        cross/=np.maximum(np.linalg.norm(cross,axis=1,keepdims=True),1e-12)
        for j in range(3):
            np.add.at(normals,tri[:,j],cross)
        normals/=np.maximum(np.linalg.norm(normals,axis=1,keepdims=True),1e-12)
        bary=records['position'].astype(float)
        bary[:,2]=1-bary[:,:2].sum(1)
        projected=((q[ids]+normals[ids]*bary[:,3,None,None])*bary[:,:3,None]).sum(1)
        error=np.linalg.norm(projected-rest,axis=1)
        old_alpha=1-np.array(section['cloth_maps'][0]['source'])[:,3]/65535
        alpha=np.minimum(old_alpha,1-records['source'][:,3].astype(float)/65535)
        alpha=np.minimum(alpha,.24/np.maximum(error,1e-10))
        records['source'][:,3]=np.rint((1-alpha)*65535).astype('<u2')
        mapping_stats[n]=dict(vertices=count,static_error_cm=float(max(error*alpha)),old_mean_blend=float(old_alpha.mean()),new_mean_blend=float(alpha.mean()))
        for offset in (section['cloth_map_spans'][0]['offset'],details['gpu_cloth_mapping_span']['offset']+64*section['gpu_mapping_offset']):
            raw[offset:offset+64*count]=records.tobytes()
        idx=next(i for i,e in enumerate(document['Exports']) if e['ObjectName']==n)
        dst=document['Exports'][idx]
        src=next(e for e in cooked['Exports'] if e['ObjectName']==n)
        field=lambda e,k:next(p for p in e['Data'] if p['Name']==k)
        for k in ('UsedBoneNames','UsedBoneIndices','ReferenceBoneIndex','AssetGuid'):
            assert field(src,k)==field(dst,k),(n,k)
        field(dst,'LodData')['Value']=field(src,'LodData')['Value']
        changes[idx]=n
    assert len(changes)==3
    write(root/'encoded/body.json',document)
    temp=root/'encoded/body.uasset'
    common.run('encode',[common.diag.TOOLS/'UAssetGUI.exe','fromjson',root/'encoded/body.json',temp])
    encoded=compose.tojson('encoded',temp)
    assert encoded['NameMap']==original['NameMap'] and encoded['Imports']==original['Imports']
    old_head=source.read_bytes()
    header=bytearray(old_head)
    old_payload=source.with_suffix('.uexp').read_bytes()
    new_payload=temp.with_suffix('.uexp').read_bytes()
    blocks=[]
    total=len(header)
    previous=0
    for idx,exp in sorted(enumerate(original['Exports']),key=lambda row:row[1]['SerialOffset']):
        at=exp['SerialOffset']-len(header)
        assert at==previous
        previous=at+exp['SerialSize']
        block=old_payload[at:previous]
        if idx in changes:
            e=encoded['Exports'][idx]
            off=e['SerialOffset']-temp.stat().st_size
            block=new_payload[off:off+e['SerialSize']]
        elif exp['ObjectName']=='Hun_Body_Simple':
            existing=unpack(original)
            assert block.count(existing)==1
            block=block.replace(existing,raw,1)
        offset=compose.unique(old_head,struct.pack('<qq',exp['SerialSize'],exp['SerialOffset']))
        struct.pack_into('<qq',header,offset,len(block),total)
        blocks.append(block)
        total+=len(block)
    assert previous==len(old_payload)-4
    offset=compose.unique(old_head,struct.pack('<q',len(old_head)+previous))
    struct.pack_into('<q',header,offset,total)
    dest=root/'legacy'/relative
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(header)
    dest.with_suffix('.uexp').write_bytes(b''.join(blocks)+old_payload[-4:])
    container=root/'container'
    container.mkdir(exist_ok=True)
    utoc=container/(name+'.utoc')
    retoc=common.diag.TOOLS/'retoc.exe'
    common.run('pack',[retoc,'to-zen','--version','UE5_6','--no-parallel',root/'legacy',utoc])
    listing=common.run('list',[retoc,'list','--path',utoc])
    assert [l.split()[-1].replace(chr(92),'/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')]==[relative]
    files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())]
    assert {r['name'] for r in files}=={name+ext for ext in ('.pak','.utoc','.ucas')}
    assert common.snapshot()==before
    write(root/'build.json',dict(before=before,files=files,mapping=mapping_stats,payload=sha(dest.with_suffix('.uexp'))))
    verify('final',[common.MODS,container])


def verify(label,dirs):
    report=read(root/'build.json')
    resolved=compose.extract(label,dirs)/relative
    assert sha(resolved.with_suffix('.uexp'))==report['payload']
    doc=compose.tojson(label,resolved)
    assert not any('Unknown' in x['ObjectName'] for x in doc['Imports'])
    p,w,i,d=decode(doc)
    original=read(root/'native/before.json')
    op,ow,oi,od=decode(original)
    assert np.array_equal(p,op) and w==ow and np.array_equal(i,oi)
    for s,t in zip(d['sections'],od['sections']):
        if s['cloth_index'] not in (1,3,4):
            assert s==t
    old=package_verify.cue('before-cue',[common.MODS]) if label=='final' else read(root/'before-cue.json')
    if label=='final':
        write(root/'before-cue.json',old)
    actual=package_verify.cue(label,dirs)
    assert actual[common.PA]==old[common.PA]
    phys=read(stage/'cloth-details.json')['assets']
    for e,ref in zip(actual[body],old[body],strict=True):
        assert e['Name']==ref['Name']
        if e['Name'] not in report['mapping']:
            assert e==ref,e['Name']
            continue
        reference=copy.deepcopy(ref)
        lod=e['Properties']['LodData']
        reference['Properties']['LodData']=lod
        assert reference==e
        grid=next(a for a in phys if a['name']==e['Name'])
        data=lod[0]['PhysicalMeshData']
        assert data['Indices']==grid['indices']
        assert np.allclose([[v[k] for k in 'XYZ'] for v in data['Vertices']],grid['positions'],rtol=0,atol=.0001)
    print(label,'verified', report['mapping'],flush=True)


if __name__=='__main__':
    build()
