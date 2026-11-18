"""Compare posed, quantized render surfaces against the last installed JK version."""
import shutil
import numpy as np
from scipy.spatial.transform import Rotation
from deliver import root, prior, stage, read, write, sha, decode
import evaluate


def renderer(document):
    rest,weights,_,details=decode(document)
    bones=read(prior/'reference-bones.json')
    names=[b['name'] for b in bones]
    inverse=np.linalg.inv(evaluate.matrices(bones))
    parts=[]
    for s in details['sections']:
        if s['cloth_index']<0:
            continue
        lo=s['base_vertex']
        points=rest[lo:lo+s['vertices']]
        influences={}
        for i,w in enumerate(weights[lo:lo+len(points)]):
            for n,v in w.items():
                influences.setdefault(names.index(n),[]).append((i,v))
        mapping=s['cloth_maps'][0]
        ids=np.array(mapping['source'])
        b=np.array(mapping['position'])
        b[:,2]=1-b[:,0]-b[:,1]
        parts.append((s['cloth_index'],points,[(n,np.array([i for i,_ in rows]),np.array([v for _,v in rows])) for n,rows in influences.items()],ids,b))
    def frame(f):
        bones=np.array(f['component_bones'])
        pose=np.tile(np.eye(4),(len(bones),1,1))
        pose[:,:3,:3]=Rotation.from_quat(bones[:,3:]).as_matrix()
        pose[:,:3,3]=bones[:,:3]
        skin=pose@inverse
        result={}
        for index,points,weights,ids,b in parts:
            base=np.zeros_like(points)
            for n,ix,v in weights:
                base[ix]+=(points[ix]@skin[n,:3,:3].T+skin[n,:3,3])*v[:,None]
            cloth=next(a for a in f['assets'] if a['asset_index']==index)
            q=np.array(cloth['component_positions'])
            n=np.array(cloth['component_normals'])
            a=1-ids[:,3,None]/65535
            sim=((q[ids[:,:3]]+n[ids[:,:3]]*b[:,3,None,None])*b[:,:3,None]).sum(1)
            result[index]=base*(1-a)+sim*a
        return result
    return frame


def compare():
    previous=renderer(read(root/'native/before.json'))
    candidate=renderer(read(root/'native/final.json'))
    reference=prior/'coarse64-12x3-delivery'
    rows=[]
    for profile in ['walk','jog','crouch']:
        for hz in [30,60]:
            file=f'{profile}-{hz}.json'
            old=read(reference/file)
            new=read(stage/file)
            assert [f['step'] for f in old['frames']]==[f['step'] for f in new['frames']]
            parts={i:[] for i in range(5)}
            for f,g in zip(old['frames'],new['frames']):
                assert np.allclose(f['component_bones'],g['component_bones'],atol=1e-5,rtol=0)
                left,right=previous(f),candidate(g)
                for i in parts:
                    parts[i].append(np.linalg.norm(left[i]-right[i],axis=1))
            row={i:dict(peak_p95_cm=float(np.max(np.percentile(parts[i],95,axis=1))),max_cm=float(np.max(parts[i]))) for i in parts}
            print(file,{i:round(v['max_cm'],3) for i,v in row.items()},flush=True)
            rows.append(dict(file=file,deviations=row,simulation_sha=sha(stage/file)))
    write(root/'visible-motion.json',rows)


if __name__=='__main__':
    compare()
    evaluate.W=root
    shutil.copy2(prior/'reference-bones.json',root/'reference-bones.json')
    shutil.copy2(prior/'coarse64-12x3-delivery/selection.json',stage/'selection.json')
    evaluate.evaluate(stage.name,root/'native/final.json')
    assert read(stage/'evaluation.json')['passed']
