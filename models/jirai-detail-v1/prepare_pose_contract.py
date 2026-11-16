"""Synthetic stress clips only; no extracted game animation is redistributed."""
import json,math
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation as Q
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
bones=json.loads((P/'models/hun-body.skel.json').read_text())['bones'];globalq=[]
for b in bones:globalq.append((globalq[b['parent']]*Q.from_quat(b['q'])) if b['parent']>=0 else Q.from_quat(b['q']))
clips={}
for profile in ['crouch','run','head-arms']:
 keys=[]
 for f in range(121):
  t=f/30;fade=min(1,max(0,(t-.3)/.8));fade=fade*fade*(3-2*fade);angles={}
  if profile=='crouch':angles={'thigh_l':82*fade,'thigh_r':82*fade,'calf_l':-110*fade,'calf_r':-110*fade,'spine_03':-18*fade}
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
   p=b['t'].copy()
   if profile=='crouch' and b['name']=='pelvis':p[2]-=26*fade
   frame.append(dict(b,t=p,q=(Q.from_quat(b['q'])*delta).as_quat().tolist()))
  keys.append(frame)
 clips[profile]={'fps':30,'keys':keys}
(W/'pose-contract.json').write_text(json.dumps({'basis':'synthetic joint rotations using native local references','clips':clips}));print('POSE_CONTRACT_READY')
