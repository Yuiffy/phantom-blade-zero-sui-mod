"""Same three-cycle recovery stress as Jirai, with the JK imported references."""
from common import *
import math
from scipy.spatial.transform import Rotation as Q
bones=read(W/'reference-bones.json');globalq=[]
for b in bones:globalq.append(globalq[b['parent']]*Q.from_quat(b['q']) if b['parent']>=0 else Q.from_quat(b['q']))
def smooth(x):
 x=max(0.,min(1.,x));return x*x*(3-2*x)
def motion(t,profile):
 if t<1 or t>=16:return 0.,0.,0.
 u=(t-1)%5;env=smooth(u/.3)*smooth((2-u)/.3)
 return u,env,math.sin(u*math.tau*(1.1 if profile=='walk' else 1.6))
doc={'basis':'synthetic JK joint stress, not extracted gameplay animation','clips':{}}
for profile in ['walk','jog','crouch']:
 keys=[]
 for f in range(481):
  t=f/30;u,env,a=motion(t,profile)
  if profile=='crouch':
   fade=smooth(u/.6)*smooth((2-u)/.6) if t>=1 else 0
   angles={'thigh_l':82*fade,'thigh_r':82*fade,'calf_l':-110*fade,'calf_r':-110*fade,'spine_03':-18*fade}
  else:
   forward,back,knee=(26,16,38) if profile=='walk' else (58,30,80)
   angles={'thigh_l':env*(forward*max(a,0)+back*min(a,0)),'thigh_r':env*(forward*max(-a,0)+back*min(-a,0)),'calf_l':-knee*env*max(a,0),'calf_r':-knee*env*max(-a,0),'spine_03':-6*env,'upperarm_l':-20*a*env,'upperarm_r':20*a*env}
  frame=[]
  for i,b in enumerate(bones):
   delta=globalq[i].inv()*Q.from_euler('x',angles.get(b['name'],0),degrees=True)*globalq[i];p=b['t'].copy()
   if profile=='crouch' and b['name']=='pelvis':p[2]-=26*fade
   frame.append(dict(b,t=p,q=(Q.from_quat(b['q'])*delta).as_quat().tolist()))
  keys.append(frame)
 doc['clips'][profile]={'fps':30,'keys':keys,'stop_times':[3,8,13]}
 for hz in [30,60]:
  points=[];distance=0.;last_v=0.
  for step in range(60+16*hz+1):
   t=max(0,(step-60)/hz);u,env,a=motion(t,profile);v=(140 if profile=='walk' else 260 if profile=='jog' else 0)*env
   distance+=(last_v+v)/hz*.5;last_v=v;points.append([0,distance,0,2*env,6*env*math.sin(u*math.pi),1.5*a*env])
  write(W/f'component-{profile}-{hz}.json',{'frames':points})
write(W/'pose-contract.json',doc)
print('JK_POSE_CONTRACT_READY',flush=True)
