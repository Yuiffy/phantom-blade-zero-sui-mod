"""Check that the neck/shoulder edit preserved the established lower-body fit."""
from pathlib import Path
import json,math
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
a=read(ROOT.parent/'tripo-refine-v2/source-render-contract.json')
b=read(ROOT/'source-render-contract.json')
assert a['bones']==b['bones']
pa,pb=a['positions_blender_cm'],b['positions_blender_cm']
assert len(pa)==len(pb)
ids=[i for i,p in enumerate(pa) if p[2]<130]
assert all(pa[i]==pb[i] for i in ids)
assert all(a['influences'][i]==b['influences'][i] for i in ids)
report={'unchanged_vertices_below_z_130_cm':len(ids),
        'lower_body_positions_exactly_equal':True,'lower_body_weights_exactly_equal':True,
        'max_displacement_cm':max(math.dist(x,y) for x,y in zip(pa,pb)),
        'max_influences':max(len(w) for w in b['influences'])}
(ROOT/'scope-check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps(report))
