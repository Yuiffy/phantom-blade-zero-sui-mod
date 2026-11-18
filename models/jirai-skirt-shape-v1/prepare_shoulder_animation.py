"""Original animation reference translations plus a measured target pose contract."""
import json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-skirt-shape-v1'
PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
old=json.loads((PBZ/'models/hun-body.skel.json').read_text())['bones'];new=json.loads((ROOT/'intended-reference-skeleton.json').read_text())['bones']
def matrix(b):
 m=np.eye(4);m[:3,:3]=Rotation.from_quat(b['q']).as_matrix()@np.diag(b['s']);m[:3,3]=b['t'];return m
global_old=[]
for b in old:global_old.append(global_old[b['parent']]@matrix(b) if b['parent']>=0 else matrix(b))
keys=[];expected=[]
for angle in [0,30,60,90]:
 frame=[];world=[]
 for i,(a,b) in enumerate(zip(old,new)):
  delta=Rotation.identity()
  if a['name'] in ['upperarm_l','upperarm_r']:
   axis=Rotation.from_euler('y',-angle if a['name'].endswith('_l') else angle,degrees=True)
   g=Rotation.from_matrix(global_old[i][:3,:3]);delta=g.inv()*axis*g
  rot=(Rotation.from_quat(a['q'])*delta).as_quat().tolist()
  frame.append(dict(a,q=rot));local=matrix(dict(b,q=rot));world.append(world[b['parent']]@local if b['parent']>=0 else local)
 keys.append(frame);expected.append({'angle':angle,'bones':{b['name']:world[i][:3,3].tolist() for i,b in enumerate(new) if b['name'] in ['upperarm_l','lowerarm_l','hand_l','weapon_l','ik_hand_l','middle_01_l','middle_03_l','upperarm_r','lowerarm_r','hand_r','weapon_r','ik_hand_r','middle_01_r','middle_03_r','neck_01','neck_02','head']}})
changes=[a['name'] for a,b in zip(old,new) if math.dist(a['t'],b['t'])>.01 and not a['name'].startswith(('ik_','weapon_'))]
assert not any(n.startswith(('ik_','weapon_')) for n in changes)
(ROOT/'shoulder-animation-contract.json').write_text(json.dumps({'keys':keys,'expected':expected,'skeleton_translation_bones':changes,'fbx_sha256':hashlib.sha256((ROOT/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest()},indent=2))
print('Shoulder animation contract',changes)
