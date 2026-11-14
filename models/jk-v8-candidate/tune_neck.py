"""Search continuous neck weight fields on fixed rest geometry; no rendering."""
import bpy,json,numpy as np,itertools
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
me=ob.data;co=np.array([v.co[:] for v in me.vertices]);src=np.array([d.vector[:] for d in me.attributes['source_rest_position'].data]);comp=np.array([d.value for d in me.attributes['source_component'].data])
x=np.abs(src[:,0]-.00195217);z=src[:,2];e=np.array([a.vertices[:] for a in me.edges]);l=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1)
regions={'neck':(comp==0)&(x<.025)&(z>.76)&(z<.785),'shoulder':(comp==0)&(x>.025)&(x<.145)&(z>.66)&(z<.77)}
masks={k:v[e[:,0]]&v[e[:,1]]&(l>.05) for k,v in regions.items()}
W=[{ob.vertex_groups[g.group].name:g.weight for g in v.groups} for v in me.vertices];base=np.array([row.get('head',0) for row in W])
pivot=np.array(arm.data.bones['head'].head_local)
deltas=[]
for axis,angle in [((0,0,1),85),((1,0,0),43)]:
 for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
 pb=arm.pose.bones['head'];b=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=b.inverted()@Quaternion(Vector(axis),np.deg2rad(angle))@b
 bpy.context.view_layer.update()
 transform=np.array(pb.matrix@pb.bone.matrix_local.inverted())
 delta=co@transform[:3,:3].T+transform[:3,3]-co
 deltas.append(delta)
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh();actual=np.array([v.co[:] for v in data.vertices]);ev.to_mesh_clear()
 error=np.max(np.abs(actual-(co+delta*base[:,None])))
 print('ANALYTIC CHECK',axis,angle,'max_cm',error,'modifier',[(m.type,getattr(m,'use_deform_preserve_volume',None)) for m in ob.modifiers])
 assert error<.001,error
change=(comp==0)&(z>.71)&(z<.785)
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)
rows=[]
for z0,z1,x0,x1 in itertools.product([.735,.745,.750,.755],[.760,.766,.772,.778],[.012,.016,.020,.025],[.034,.044,.054,.064,.074]):
 if x1<=x0 or z1<=z0:continue
 h=base.copy();h[change]=(smooth((z-z0)/(z1-z0))*(1-smooth((x-x0)/(x1-x0))))[change]
 metrics=[]
 for delta in deltas:
  posed=co+delta*h[:,None];rat=np.linalg.norm(posed[e[:,0]]-posed[e[:,1]],axis=1)/np.maximum(l,1e-10)
  metrics.append({k:{'p99':float(np.percentile(rat[m],99)),'max':float(rat[m].max()),'over_1_6':int((rat[m]>1.6).sum())} for k,m in masks.items()})
 score=max(m['neck']['p99'] for m in metrics)*1.3+max(m['shoulder']['p99'] for m in metrics)+.40*max(m['shoulder']['max'] for m in metrics)+.003*sum(m['neck']['over_1_6']+m['shoulder']['over_1_6'] for m in metrics)
 rows.append({'field':[z0,z1,x0,x1],'score':score,'poses':metrics})
rows.sort(key=lambda r:r['score'])
(ROOT/'neck-weight-search.json').write_text(json.dumps({'fixed_rest_mesh':True,'poses':'analytic LBS, head turn 85 / nod 43 degrees','best':rows[:12]},indent=2))
print(json.dumps(rows[:3]))
