import json,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
code=(ROOT/'bind_hun.py').read_text(encoding='utf8').split('# Create the exact game hierarchy')[0]
exec(compile(code,str(ROOT/'bind_hun.py'),'exec'))
rows=[]
for label in ['Right','Left']:
    for suffix in ['UpLeg','Leg','Arm','ForeArm']:
        name=label+suffix;point=(np.array(S[name])+np.array(S[child[name]]))*.5
        names=[label+n for n in (['UpLeg','Leg','Foot'] if suffix in ['UpLeg','Leg'] else ['Arm','ForeArm','Hand'])]
        eps=1e-5
        J=np.column_stack([(chain_fit(point+np.eye(3)[k]*eps,names,.018)-chain_fit(point-np.eye(3)[k]*eps,names,.018))/(2*eps) for k in range(3)])
        u=np.array((S[child[name]]-S[name]).normalized())
        transverse=frame(u,[0,1,0])[:,[0,2]]
        radial=np.linalg.svd(J@transverse,compute_uv=False)
        rows.append({'segment':name,'radial_scales':radial.tolist(),'radial_anisotropy':float(max(radial)/min(radial))})
assert max(r['radial_anisotropy'] for r in rows)<1.001
(ROOT/'proportion-validation.json').write_text(json.dumps({'segment_sections':rows,'max_control_joint_miss_cm':max(r['miss_cm'] for r in fit_checks),'face_similarity_scale':190.,'game_animations_executed':False},indent=2),encoding='utf8')
print(json.dumps(rows))
