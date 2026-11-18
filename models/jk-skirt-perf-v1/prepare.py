"""Initialize an isolated local experiment from the hash-checked previous author project."""
from common import *
import shutil
import numpy as np

def prepare():
    previous=REPO/'private/jk-skirt-v1'
    assert not PROJECT.exists(),'Already initialized; never overwrite frozen author inputs'
    for name in ['selection.json','pose-contract.json','reference-bones.json',
                 'skirt-reference-normals.json','baseline-body.json','baseline-cloth.json',
                 'skirt-collision-spec.json']:
        shutil.copy2(previous/name,W/name)
    for p in previous.glob('component-*.json'):shutil.copy2(p,W/p.name)
    for name in ['ProjectPBZ.uproject','Config','Content','Plugins/HuaShira','Plugins/PBZModTools']:
        source=previous/'variant/ue/ProjectPBZ'/name;target=PROJECT.parent/name
        if source.is_dir():shutil.copytree(source,target)
        elif source.exists():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    (W/'baseline').mkdir(exist_ok=True)
    shutil.copy2(previous/'baseline/contacts.json',W/'baseline/contacts.json')
    generate_guides(previous)

def generate_guides(previous):
    q=np.array(read(previous/'delivery/cloth-details.json')['assets'][2]['positions'])
    for name,zs,count in [('coarse128',[120,110,101,92.5],32),
                           ('coarse96',[120,107,92.5],32),
                           ('coarse64',[120,110,101,92.5],16),
                           ('coarse48',[120,107,92.5],16)]:
        rings=[]
        for z in zs:
            ids=np.where(abs(q[:,2]-z)<.01)[0]
            ids=ids[np.argsort(np.arctan2(q[ids,1]+5,q[ids,0]))]
            rings.append(q[ids][::32//count])
        p=np.concatenate(rings);tri=[]
        for ring in range(len(zs)-1):
            for a in range(count):
                b=(a+1)%count;v=ring*count
                tri.extend([[v+a,v+b,v+count+b],[v+a,v+count+b,v+count+a]])
        tri=np.array(tri);faces=p[tri];n=np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0])
        outward=faces.mean(1);outward[:,1]+=5;outward[:,2]=0
        if np.sum(n*outward)<0:tri=tri[:,::-1]
        write(W/(name+'.json'),dict(positions=p.tolist(),indices=tri.ravel().tolist()))
    mapping=read(previous/'low-guide/mapping.json')
    write(W/'render-target.json',{k:mapping[k] for k in ['original_positions','positions']})

if __name__=='__main__':
    W.mkdir(exist_ok=True);prepare()
