"""Synthetic stress clips only; no extracted game animation is redistributed."""
import json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Q
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-recovery-v1';P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
bones=json.loads((P/'models/hun-body.skel.json').read_text())['bones'];globalq=[]
for b in bones:globalq.append((globalq[b['parent']]*Q.from_quat(b['q'])) if b['parent']>=0 else Q.from_quat(b['q']))
clips={}
for profile in ['crouch','wide-crouch','diagonal-crouch','lunge-left','lunge-right','run','head-arms']:
 keys=[]
 for f in range(121):
  t=f/30;fade=min(1,max(0,(t-.3)/.8));fade=fade*fade*(3-2*fade);angles={}
  if profile=='crouch':angles={'thigh_l':82*fade,'thigh_r':82*fade,'calf_l':-110*fade,'calf_r':-110*fade,'spine_03':-18*fade}
  extra={}
  if profile in ['wide-crouch','diagonal-crouch','lunge-left','lunge-right']:
   angles={'thigh_l':96*fade,'thigh_r':96*fade,'calf_l':-125*fade,'calf_r':-125*fade,'spine_03':-26*fade}
   extra={'thigh_l':(-24*fade,12*fade),'thigh_r':(24*fade,-12*fade)}
   if profile=='diagonal-crouch':
    angles.update(thigh_l=106*fade,thigh_r=74*fade,calf_l=-130*fade,calf_r=-110*fade);extra={'thigh_l':(-30*fade,20*fade),'thigh_r':(16*fade,-10*fade),'pelvis':(0,20*fade)}
   if profile.startswith('lunge-'):
    left=profile.endswith('left');forward='l' if left else 'r';back='r' if left else 'l'
    angles.update({f'thigh_{forward}':108*fade,f'thigh_{back}':-24*fade,f'calf_{forward}':-118*fade,f'calf_{back}':-65*fade});extra={'thigh_l':(-16*fade,8*fade),'thigh_r':(16*fade,-8*fade)}
  if profile=='run':
   a=math.sin(max(0,t-.3)*math.pi*2*1.1)*fade
   angles={'thigh_l':58*max(a,0)+30*min(a,0),'thigh_r':58*max(-a,0)+30*min(-a,0),'calf_l':-80*max(0,a),'calf_r':-80*max(0,-a),'spine_03':-12*fade,'upperarm_l':-30*a,'upperarm_r':30*a}
  if profile=='head-arms':angles={'head':24*math.sin(t*2)*fade,'neck_02':8*math.sin(t*2)*fade,'spine_05':12*math.sin(t*1.5)*fade}
  frame=[]
  for i,b in enumerate(bones):
   delta=Q.identity()
   if b['name'] in angles:delta=globalq[i].inv()*Q.from_euler('x',angles[b['name']],degrees=True)*globalq[i]
   if profile=='head-arms' and b['name'] in ['upperarm_l','upperarm_r']:
    ang=55*fade*(1 if b['name'].endswith('_r') else -1);delta=globalq[i].inv()*Q.from_euler('y',ang,degrees=True)*globalq[i]
   if b['name'] in extra:
    y,z=extra[b['name']];g=globalq[i];delta=(g.inv()*Q.from_euler('z',z,degrees=True)*Q.from_euler('y',y,degrees=True)*g)*delta
   p=b['t'].copy()
   if profile in ['crouch','wide-crouch','diagonal-crouch','lunge-left','lunge-right'] and b['name']=='pelvis':p[2]-=26*fade
   frame.append(dict(b,t=p,q=(Q.from_quat(b['q'])*delta).as_quat().tolist()))
  keys.append(frame)
 clips[profile]={'fps':30,'keys':keys}
(W/'pose-contract.json').write_text(json.dumps({'basis':'synthetic joint rotations using native local references','clips':clips}));print('POSE_CONTRACT_READY')
