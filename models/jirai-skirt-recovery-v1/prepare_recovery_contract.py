"""Three move/stop cycles with exactly stationary final poses; synthetic only."""
import json, math, runpy
from pathlib import Path
from scipy.spatial.transform import Rotation as Q

C = Path(__file__).resolve().parent
W = C.parents[1] / 'private/jirai-skirt-recovery-v1'
runpy.run_path(str(C/'prepare_pose_contract.py'), run_name='__main__')
doc = json.loads((W/'pose-contract.json').read_text())
bones = json.loads(Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui/models/hun-body.skel.json').read_text())['bones']
globalq=[]
for b in bones:
    globalq.append(globalq[b['parent']]*Q.from_quat(b['q']) if b['parent']>=0 else Q.from_quat(b['q']))

def smooth(x):
    x=max(0.,min(1.,x)); return x*x*(3-2*x)

def motion(t, profile):
    if t<1 or t>=16: return 0.,0.,0.
    u=(t-1)%5
    env=smooth(u/.3)*smooth((2-u)/.3)
    a=math.sin(u*math.tau*(1.1 if profile=='walk-recover' else 1.6))
    return u,env,a

for profile in ['walk-recover','jog-recover','crouch-recover']:
    keys=[]
    for f in range(481):
        t=f/30;u,env,a=motion(t,profile)
        if profile=='crouch-recover':
            fade=smooth(u/.6)*smooth((2-u)/.6) if t>=1 else 0
            angles={'thigh_l':82*fade,'thigh_r':82*fade,'calf_l':-110*fade,'calf_r':-110*fade,'spine_03':-18*fade}
        else:
            forward,back,knee=(26,16,38) if profile=='walk-recover' else (58,30,80)
            angles={'thigh_l':env*(forward*max(a,0)+back*min(a,0)), 'thigh_r':env*(forward*max(-a,0)+back*min(-a,0)), 'calf_l':-knee*env*max(a,0), 'calf_r':-knee*env*max(-a,0), 'spine_03':-6*env,'upperarm_l':-20*a*env,'upperarm_r':20*a*env}
        frame=[]
        for i,b in enumerate(bones):
            delta=globalq[i].inv()*Q.from_euler('x',angles.get(b['name'],0),degrees=True)*globalq[i]
            p=b['t'].copy()
            if profile=='crouch-recover' and b['name']=='pelvis': p[2]-=26*fade
            frame.append(dict(b,t=p,q=(Q.from_quat(b['q'])*delta).as_quat().tolist()))
        keys.append(frame)
    doc['clips'][profile]={'fps':30,'keys':keys,'steps':541,'recovery':True,'stop_times':[3,8,13],'quiet_windows':[[5.5,6],[10.5,11],[15.5,16]]}
(W/'pose-contract.json').write_text(json.dumps(doc))
print('RECOVERY_CONTRACT_READY',len(doc['clips']))

def component_samples(profile, dt, steps):
    points=[];distance=0.;last_v=0.
    speed=140 if profile=='walk-recover' else 260 if profile=='jog-recover' else 0
    for step in range(steps):
        t=max(0,(step-60)*dt);u,env,a=motion(t,profile)
        v=speed*env
        distance+=(last_v+v)*dt*.5;last_v=v
        points.append([0,distance,0,2*env,6*env*math.sin(u*math.pi),1.5*a*env])
    return {'frames':points}

if __name__=='__main__':
    for profile in ['walk-recover','jog-recover','crouch-recover']:
        for hz in [30,60]:
            steps=60+16*hz+1
            (W/f'component-{profile}-{hz}hz.json').write_text(json.dumps(component_samples(profile,1/hz,steps)))
