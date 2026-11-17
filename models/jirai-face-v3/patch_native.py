"""Edit only face position/tangent bytes in the frozen installed native mesh."""
from common import *
import base64, importlib.util, inspect, shutil, struct
import numpy as np
from scipy.spatial import cKDTree

BODY='/HuaShira/Mods/SuiPBZ/JiraiOnly/Hun_Body_Simple'

def decoder():
    spec=importlib.util.spec_from_file_location('recovery_reader',REPO/'models/jirai-skirt-recovery-v1/decode_cloth_body.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    code=inspect.getsource(mod.decoder.parse).replace('assert count==14','assert count==20')
    scope=dict(vars(mod.decoder));scope.update(section=mod.section,skeletal_materials=mod.materials);exec(code,scope)
    return mod,scope['parse']

def parse_doc(doc):
    mod,parse=decoder()
    return parse(doc,{'package':BODY},read(REPO/'private/jirai-skirt-recovery-v1/variant/material-spec.json'))

def unpack(doc):
    return base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])

def unit(v):return v/np.maximum(1e-12,np.linalg.norm(v,axis=-1,keepdims=True))

def build():
    baseline=read(ROOT/'baseline.json')
    for row in baseline['installed']:assert sha(MODS/row['name'])==row['sha256'],'Installed base changed'
    original=MODEL/'legacy'/(relative_package(BODY)+'.uasset')
    assert sha(original.with_suffix('.uexp'))==sha(MODEL/'final-legacy'/(relative_package(BODY)+'.uexp'))
    # Source is the independently read back container installed in this task.
    for row in read(MODEL/'verification.json')['container_files']:
        assert sha(MODS/row['name'])==sha(row['path'])==row['sha256']
    out=ROOT/'legacy'/(relative_package(BODY)+'.uasset');out.parent.mkdir(parents=True,exist_ok=True)
    for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
        p=original.with_suffix(ext)
        if p.exists():shutil.copy2(p,out.with_suffix(ext))
    docpath=ROOT/'native/source.json'
    docpath.parent.mkdir(parents=True,exist_ok=True)
    run('native-source-json',[diag.TOOLS/'UAssetGUI.exe','tojson',original,docpath,'VER_UE5_6','PBZ'])
    doc=read(docpath);pos,weights,indices,details=parse_doc(doc)
    raw=unpack(doc);edited=bytearray(raw)
    d=np.load(ROOT/'surface.npz');old=d['old_positions'].copy();new=d['positions'].copy();comps=d['components'];changed=d['changed']
    loop_vertices=d['loop_vertices'];loop_triangles=d['loop_triangles'];source_materials=d['materials'];d.close()
    old[:,1]*=-1;new[:,1]*=-1
    tree=cKDTree(old)
    # Resolve duplicated source positions by material membership. This is a
    # geometry edit, so all source duplicates must agree on their displacement.
    src_material=[set() for _ in old]
    for loops,material in zip(loop_triangles,source_materials):
        for vertex in loop_vertices[loops]:src_material[int(vertex)].add(int(material))
    native_material=np.zeros(len(pos),int)
    for s in details['sections']:native_material[s['base_vertex']:s['base_vertex']+s['vertices']]=s['material']
    found=tree.query_ball_point(pos,.001,workers=1)
    patched=pos.copy();source_index=np.full(len(pos),-1,int);native_changed=np.zeros(len(pos),bool)
    for i,rows in enumerate(found):
        if native_material[i] not in [0,1,18,19] or pos[i,2]<170.6:continue
        rows=[j for j in rows if native_material[i] in src_material[j]]
        assert rows,('Missing face source vertex',i,pos[i])
        changes=np.array([new[j]-old[j] for j in rows])
        assert np.max(np.ptp(changes,axis=0))<1e-5,('Ambiguous source displacement',i,rows)
        source_index[i]=rows[0]
        if np.linalg.norm(changes[0])>1e-6:
            patched[i]=pos[i]+changes[0];native_changed[i]=True
    assert native_changed.sum()>2400
    assert set(comps[source_index[native_changed]])<=set(read(ROOT/'geometry-report.json')['components'])
    assert np.all(pos[native_changed,2]>170.6)
    # Cloth streams, weights, reference pose, sections and indices are outside
    # these two spans and remain byte-for-byte unchanged.
    packed=np.frombuffer(raw,dtype='u1',count=details['tangent_span']['bytes'],offset=details['tangent_span']['offset']).reshape(-1,8).copy()
    oldnorm=packed[:,4:7].view('i1').astype(float)/127
    oldtangent=packed[:,:3].view('i1').astype(float)/127
    tri=indices.reshape(-1,3)
    fn=np.cross(pos[tri[:,1]]-pos[tri[:,0]],pos[tri[:,2]]-pos[tri[:,0]])
    orient=np.sign(np.median(np.sum(unit(fn)*unit(oldnorm[tri].mean(1)),axis=1)))
    assert abs(orient)==1
    fn=np.cross(patched[tri[:,1]]-patched[tri[:,0]],patched[tri[:,2]]-patched[tri[:,0]])*orient
    accumulated=np.zeros_like(patched)
    for k in range(3):np.add.at(accumulated,tri[:,k],fn)
    newnorm=unit(accumulated)
    degenerate=np.linalg.norm(accumulated,axis=1)<1e-10
    newnorm[degenerate]=unit(oldnorm[degenerate])
    touched=np.any(native_changed[tri],axis=1)
    normal_changed=np.zeros(len(pos),bool);normal_changed[np.unique(tri[touched])]=True
    normal_changed &= np.isin(native_material,[0,1,18,19])
    normal_changed &= pos[:,2]>170.5
    for i in np.where((native_material==18)|(native_material==19))[0]:
        if source_index[i]<0:continue
        cid=comps[source_index[i]];x,y,z=patched[i];cx=-5.317217 if cid in [51,950] else 4.614422;sign=1 if cx<0 else -1
        dx=x-cx;dz=z-177.799362
        if cid in [51,52]:
            s=max(.01,float(np.sqrt(max(0,1-(dx/3.1)**2-(dz/2)**2))))
            n=np.array([1.4*dx/(3.1**2*s)-.3*sign,1,1.4*dz/(4*s)])
        elif cid in [950,951]:
            yy=-y+.9+.3*sign*dx
            n=np.array([dx/(3.1**2)+.3*sign*yy/(1.4**2),-yy/(1.4**2),dz/4])
        else:raise AssertionError(cid)
        newnorm[i]=unit(n);normal_changed[i]=True
    # A smooth mouth frame removes the source's tiny facet-shaped shadow
    # fragments. Its inset backing stays behind the connected lip surface.
    mouth=(native_material==0)&(np.abs(patched[:,0]+.35)<2.7)&(pos[:,2]>170.6)&(pos[:,2]<172.45)&(pos[:,1]>-.5)
    for i in np.where(mouth)[0]:
        newnorm[i]=unit(np.array([.30*(patched[i,0]+.35),1.,-.25]));normal_changed[i]=True
    newtan=unit(oldtangent-newnorm*np.sum(oldtangent*newnorm,axis=1,keepdims=True))
    normout=packed.copy()
    normout[normal_changed,:3]=np.rint(np.clip(newtan[normal_changed],-1,1)*127).astype('i1').view('u1')
    normout[normal_changed,4:7]=np.rint(np.clip(newnorm[normal_changed],-1,1)*127).astype('i1').view('u1')
    assert np.array_equal(normout[:,[3,7]],packed[:,[3,7]])
    assert np.min(np.linalg.norm(newnorm[normal_changed],axis=1))>.99
    allowed=np.zeros(len(raw),bool)
    for span,arr,which,stride in [(details['position_span'],patched.astype('<f4'),native_changed,12),(details['tangent_span'],normout,normal_changed,8)]:
        bs=arr.tobytes();assert len(bs)==span['bytes']
        for i in np.where(which)[0]:
            start=span['offset']+stride*i;edited[start:start+stride]=bs[stride*i:stride*(i+1)];allowed[start:start+stride]=True
    # Only the iris section gets new planar UV0. UV1 and all other UVs remain
    # exact, including every cloth map and the skin/hair atlas coordinates.
    uv_dt='<f2' if details['uv_span']['bytes']//details['uv_span']['count']==4 else '<f4'
    tex=np.frombuffer(raw,dtype=uv_dt,count=details['uv_span']['count']*2,offset=details['uv_span']['offset']).reshape(len(pos),2,2).copy()
    np.savez_compressed(ROOT/'native/baseline-render.npz',positions=pos,indices=indices,
        packed_tangents=packed,normals=oldnorm,uv=tex,materials=native_material,
        changed=np.zeros(len(pos),bool),normal_changed=np.zeros(len(pos),bool),source_index=source_index)
    iris_ids=np.where(native_material==18)[0]
    for i in iris_ids:
        j=source_index[i];assert j>=0 and comps[j] in [51,52]
        cx=-5.317217 if comps[j]==51 else 4.614422
        tex[i,0]=[(new[j,0]-cx)/(1.67*.97)*.5+.5,.5-(new[j,2]-177.799362)/1.89*.5]
        start=details['uv_span']['offset']+i*tex.dtype.itemsize*4
        bs=tex[i,0].tobytes();edited[start:start+len(bs)]=bs;allowed[start:start+len(bs)]=True
    actual=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1');assert actual.any() and np.all(allowed[actual])
    payload=out.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1
    start=payload.find(raw);result=payload[:start]+edited+payload[start+len(raw):]
    assert len(result)==len(payload);out.with_suffix('.uexp').write_bytes(result)
    assert sha(original)==sha(out)
    np.savez_compressed(ROOT/'native/patched-render.npz',positions=patched,indices=indices,
        packed_tangents=normout,normals=normout[:,4:7].view('i1').astype(float)/127,
        uv=tex,
        materials=native_material,changed=native_changed,normal_changed=normal_changed,source_index=source_index)
    write(ROOT/'native/details.json',details)
    write(ROOT/'native/patch-report.json',dict(passed=True,package=BODY,base_model='R8Shape1',
        source_header_sha256=sha(original),output_header_sha256=sha(out),source_payload_sha256=sha(original.with_suffix('.uexp')),
        output_payload_sha256=sha(out.with_suffix('.uexp')),payload_bytes=len(payload),changed_native_bytes=int(actual.sum()),
        changed_position_vertices=int(native_changed.sum()),changed_normal_vertices=int(normal_changed.sum()),
        source_surface_sha256=sha(ROOT/'surface.npz'),only_face_position_tangent_and_iris_uv0_bytes_changed=True,
        iris_uv_vertices=len(iris_ids),other_uvs_exact=True,
        all_other_export_bytes_exact=True,cloth_weights_indices_skeleton_and_physics_exact=True,game_runtime_tested=False))
    print('FACE3_NATIVE_PATCHED',int(native_changed.sum()),int(actual.sum()))

if __name__=='__main__':build()
