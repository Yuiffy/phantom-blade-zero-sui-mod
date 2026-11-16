import bpy,json,numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
out=[]
for uv in m.uv_layers:
 loops=[li for p in m.polygons if m.materials[p.material_index].name in ['MI_Jirai_WingL','MI_Jirai_WingR'] for li in p.loop_indices]
 q=np.array([uv.data[i].uv[:] for i in loops]);out.append({'name':uv.name,'active_render':uv.active_render,'wing_uv_min':q.min(0).tolist(),'wing_uv_max':q.max(0).tolist(),'u_values':np.unique(q[:,0]).tolist()[:20]})
print('SOURCE_UV_AUDIT',json.dumps(out),flush=True)
