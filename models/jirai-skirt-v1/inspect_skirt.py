import bpy,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-detail-v1/sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;m.calc_loop_triangles();p=np.array([v.co[:] for v in m.vertices]);c=np.array([x.value for x in m.attributes['source_component'].data]);a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
report=[]
for name in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim']:
 ids=sorted({i for f in m.polygons if m.materials[f.material_index].name==name for i in f.vertices})
 report.append({'slot':name,'components':list(map(int,np.unique(c[ids]))),'vertices':len(ids),'min':p[ids].min(0).tolist(),'max':p[ids].max(0).tolist(),'samples':[{'p':p[i].tolist(),'w':{o.vertex_groups[g.group].name:g.weight for g in m.vertices[i].groups}} for i in ids[::max(1,len(ids)//24)]]})
(W/'skirt-inspection.json').write_text(json.dumps(report,indent=2))
np.savez_compressed(W/'r6-surface.npz',positions=p,components=c,triangles=np.array([t.vertices[:] for t in m.loop_triangles]),slots=np.array([m.materials[t.material_index].name for t in m.loop_triangles]))
print(json.dumps(report))
