import bpy,json,numpy as np,math
from pathlib import Path
from mathutils import Quaternion
ROOT=Path(__file__).resolve().parent
rows={}
for tag,path in [('v8',ROOT.parent/'tripo-refine-v8/sui-jk-hun-bound.blend'),('v9',ROOT/'sui-jk-hun-bound.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 comp=np.array([d.value for d in o.data.attributes['source_component'].data]);rest=np.array([v.co[:] for v in o.data.vertices]);e=np.array([edge.vertices[:] for edge in o.data.edges]);e=e[np.isin(comp[e[:,0]],[4,5])&np.isin(comp[e[:,1]],[4,5])]
 length=np.linalg.norm(rest[e[:,0]]-rest[e[:,1]],axis=1)
 for side in ['l','r']:
  for finger in ['index','middle','ring','pinky']:
   for i in [1,2,3]:
    pb=a.pose.bones[f'{finger}_{i:02d}_{side}'];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((0,0,1),math.radians(-35 if side=='r' else 35))
 bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();co=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear()
 ratio=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1)/length
 rows[tag]={'hand_edge_count':len(e),'edge_ratio_p99':float(np.quantile(ratio,.99)),'edge_ratio_max':float(ratio.max()),'edges_stretched_over_1_6':int((ratio>1.6).sum()),'edges_compressed_below_0_4':int((ratio<.4).sum())}
report={'pose':'manual 35-degree per-joint finger curl, local Z diagnostic; not extracted game animation','versions':rows,'runtime_tested':False}
(ROOT/'motion-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
