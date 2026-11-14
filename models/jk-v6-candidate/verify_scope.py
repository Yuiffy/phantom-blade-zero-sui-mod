import bpy,json,numpy as np,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
a=read(ROOT.parent/'tripo-refine-v5/source-render-contract.json');b=read(ROOT/'source-render-contract.json')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
m=next(o for o in bpy.context.scene.objects if o.type=='MESH');mask=m.data.attributes['backpack_vertex']
assert a['bones']==b['bones']
assert len(a['positions_blender_cm'])==len(b['positions_blender_cm'])==len(m.data.vertices)
assert a['influences']==b['influences']
ids=[i for i in range(len(m.data.vertices)) if mask.data[i].value]
other=[i for i in range(len(m.data.vertices)) if not mask.data[i].value]
assert all(a['positions_blender_cm'][i]==b['positions_blender_cm'][i] for i in other)
old=np.array(a['positions_blender_cm'])[ids];new=np.array(b['positions_blender_cm'])[ids]
ratio=float(np.ptp(new[:,0])/np.ptp(old[:,0]));assert abs(ratio-.75)<1e-6
assert np.array_equal(old[:,1:],new[:,1:])
r={'baseline':'final v5 close-skirt/lining candidate','backpack_vertices':len(ids),'all_other_vertices_exactly_unchanged':len(other),
   'all_weights_exactly_unchanged':True,'backpack_width_ratio':ratio,'backpack_width_before_cm':float(np.ptp(old[:,0])),
   'backpack_width_after_cm':float(np.ptp(new[:,0])),'backpack_height_and_depth_unchanged':True,
   'neck_shoulders_and_legs_and_skirt_unchanged':True,'source_contract_sha256':hashlib.sha256((ROOT/'source-render-contract.json').read_bytes()).hexdigest()}
(ROOT/'scope-check.json').write_text(json.dumps(r,indent=2),encoding='utf8');print(json.dumps(r))
