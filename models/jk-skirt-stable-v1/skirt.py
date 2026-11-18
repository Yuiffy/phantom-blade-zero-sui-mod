"""Keep a continuous pleated shell; retarget lower front pleats to the corresponding thigh."""
from pathlib import Path
import shutil
import sys

import numpy as np

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent/'jk-skirt-perf-v1'))
import common
import compose
import package_verify
import evaluate
from native import decode, unpack, DT

WORK = common.REPO/'private/jk-skirt-stable-v1/delivery'
PERF = common.REPO/'private/jk-outfit-perf-v2'
BODY = common.relative_package(common.BODY)+'.uasset'
NAME = 'zzzzzzzzzzzzz_Sui_JKStableSkirt1_14_P'
common.W = compose.W = package_verify.W = evaluate.W = WORK
read, write, sha = common.read, common.write, common.sha


def smooth(x):
    t=np.clip(x,0,1)
    return t*t*(3-2*t)


def patch(doc):
    positions, weights, _, detail = decode(doc)
    section=detail['sections'][14]
    assert section['material']==14 and section['cloth_index']==2
    lo=section['base_vertex']
    count=section['vertices']
    raw=bytearray(unpack(doc))
    rest=positions[lo:lo+count].copy()
    x,y,z=rest.T.copy()
    bottom=smooth((113-z)/15)
    front=smooth((y+10)/14)
    hip_band=smooth((z-98)/4)*(1-smooth((z-106)/6))
    radial=np.column_stack((x,y+5))
    radial/=np.maximum(np.linalg.norm(radial,axis=1,keepdims=True),1)
    # Increase clearance only below the waistband; keep the original folds.
    rest[:,1] += 2.2*front*bottom
    rest[:,:2] += radial*(1.45*hip_band)[:,None]
    rest[:,2] -= 1.7*bottom
    start=detail['position_span']['offset']+12*lo
    raw[start:start+12*count]=rest.astype('<f4').tobytes()
    # Reproject the altered reference pleats; keep motion local to the low front edge.
    new_map=read(WORK.parent/'soft-edge/remap.json')
    assert np.allclose(rest,new_map['positions'],rtol=0,atol=1e-4)
    mapped=np.zeros(count,dtype=DT)
    for key in ('position','normal','tangent','source','weight'):
        mapped[key]=[r[key] for r in new_map['mapping']]
    alpha=.18*front*(1-smooth((z-97)/5))*smooth((16-abs(x))/5)
    alpha=np.minimum(alpha,1-np.array(section['cloth_maps'][0]['source'])[:,3]/65535)
    mapped['source'][:,3]=np.rint((1-alpha)*65535).astype('<u2')
    for start in [section['cloth_map_spans'][0]['offset'],detail['gpu_cloth_mapping_span']['offset']+64*section['gpu_mapping_offset']]:
        raw[start:start+64*count]=mapped.tobytes()
    slots=detail['max_influences']
    assert not detail['bone_weights_16_bit'] and not detail['bone_indices_16_bit']
    packed=np.frombuffer(raw,'u1',count=2*slots*count,offset=detail['weight_span']['offset']+lo*2*slots).reshape(count,2*slots)
    bone_by_local={}
    for j,values in enumerate(weights[lo:lo+count]):
        for b,w in values.items():
            for k in np.flatnonzero(packed[j,slots:]):
                local=int(packed[j,k])
                if int(round(w*255))==packed[j,slots+k] and sum(abs(t-w)<1e-8 for t in values.values())==1:
                    if local in bone_by_local:
                        assert bone_by_local[local]==b
                    bone_by_local[local]=b
    assert set(bone_by_local.values())=={'pelvis','thigh_l','thigh_r'}
    for j,old in enumerate(weights[lo:lo+count]):
        old_leg=1-old.get('pelvis',0)
        leg=max(old_leg,float(bottom[j]*(.55+.07*front[j])))
        left=smooth((x[j]+7)/14)
        target={'pelvis':1-leg,'thigh_l':leg*left,'thigh_r':leg*(1-left)}
        # Keep the old seam weights where the front correction has no effect.
        mix=bottom[j]*front[j]
        values=np.array([(1-mix)*old.get(b,0)+mix*target[b] for b in bone_by_local.values()])
        # Contacts clustered on the middle pleats over the thighs. Give these
        # pleats clearance without making the free edge rise more on a stride.
        hip_target={'pelvis':.12,'thigh_l':.88*left,'thigh_r':.88*(1-left)}
        mix_hip=hip_band[j]*(.65+.35*front[j])
        values=(1-mix_hip)*values+mix_hip*np.array([hip_target[b] for b in bone_by_local.values()])
        # Both thighs advance together when crouching, but swing in opposite
        # directions on a stride. Share the extra hem support across both legs.
        paired=front[j]*(1-smooth((z[j]-99)/6))
        bones=list(bone_by_local.values())
        extra=values[bones.index('pelvis')]*paired*.98
        values[bones.index('pelvis')]-=extra
        for leg_name in ('thigh_l','thigh_r'):
            values[bones.index(leg_name)]+=extra*.5
        L,R=bones.index('thigh_l'),bones.index('thigh_r')
        spread=(values[L]-values[R])*.16*paired
        values[L]-=spread
        values[R]+=spread
        order=np.argsort(-values)
        quant=np.rint(values*255).astype(int)
        quant[order[0]]+=255-quant.sum()
        packed[j]=0
        packed[j,:3]=np.array(list(bone_by_local))[order]
        packed[j,slots:slots+3]=quant[order]
    return raw


def build():
    before=common.snapshot()
    source=compose.extract('before',[common.MODS])/BODY
    payload=source.with_suffix('.uexp').read_bytes()
    assert sha(source.with_suffix('.uexp'))==read(PERF/'build.json')['payload']
    doc=compose.tojson('before',source)
    old=unpack(doc)
    assert payload.count(old)==1
    dest=WORK/'legacy'/BODY
    dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,dest)
    dest.with_suffix('.uexp').write_bytes(payload.replace(old,patch(doc),1))
    folder=WORK/'container'
    folder.mkdir(exist_ok=True)
    utoc=folder/(NAME+'.utoc')
    retoc=common.diag.TOOLS/'retoc.exe'
    common.run('pack',[retoc,'to-zen','--version','UE5_6','--no-parallel',WORK/'legacy',utoc])
    listing=common.run('list',[retoc,'list','--path',utoc])
    assert [l.split()[-1].replace(chr(92),'/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')]==[BODY]
    files=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(folder.iterdir())]
    assert len(files)==3
    write(WORK/'build.json',dict(files=files,before=before,payload=sha(dest.with_suffix('.uexp'))))
    verify('final',[common.MODS,folder])


def verify(label,dirs):
    source=compose.extract(label,dirs)/BODY
    assert sha(source.with_suffix('.uexp'))==read(WORK/'build.json')['payload']
    doc=compose.tojson(label,source)
    assert unpack(doc)==patch(read(WORK/'native/before.json'))
    _,_,_,detail=decode(doc)
    assert max(1-row[3]/65535 for row in detail['sections'][14]['cloth_maps'][0]['source'])<.181
    result=package_verify.cue(label,dirs)
    for package,rows in result.items():
        assert rows==read(PERF/'independent/installed'/(common.relative_package(package)+'.json'))
    print(label,'verified',flush=True)


def replay():
    source=PERF/'reduced-full'
    stage=WORK/'replay'
    stage.mkdir(exist_ok=True)
    shutil.copy2(PERF/'reference-bones.json',WORK/'reference-bones.json')
    for p in source.glob('*.json'):
        if p.name in {'selection.json','cloth-details.json'} or p.stem.split('-')[0] in {'walk','jog','crouch'}:
            shutil.copy2(p,stage/p.name)
    evaluate.evaluate('replay',WORK/'native/final.json')
    assert read(stage/'evaluation.json')['passed']
    common.run('contacts',['D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe','-b','-t','2','--python-exit-code','1','-P',CODE.parent/'jk-skirt-perf-v1/contacts_blender.py','--',stage])
    print([(r['file'],r['visible_thigh_sum'],r['visible_lining_sum']) for r in read(stage/'contacts.json')['records']],flush=True)


if __name__=='__main__':
    WORK.mkdir(parents=True,exist_ok=True)
    build()
    replay()
