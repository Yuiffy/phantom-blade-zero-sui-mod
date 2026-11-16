"""Manual polearm guard proxies, not animation extracted from PBZ."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'tripo-refine-v9/sui-jk-hun-bound.blend'))
baseline=np.array([v.co[:] for v in next(o for o in bpy.context.scene.objects if o.type=='MESH').data.vertices])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.render.threads_mode='FIXED';s.render.threads=2;s.render.resolution_x=900;s.render.resolution_y=900
co=np.array([v.co[:] for v in m.vertices]);comp=np.array([d.value for d in m.attributes['source_component'].data]);src=np.array([d.vector[:] for d in m.attributes['source_rest_position'].data])
edges=np.array([e.vertices[:] for e in m.edges]);lens=np.linalg.norm(co[edges[:,0]]-co[edges[:,1]],axis=1)
def aim(side,target,pole):
 u=a.pose.bones['upperarm_'+side];l=a.pose.bones['lowerarm_'+side];h=a.pose.bones['hand_'+side]
 st=u.head.copy();el=l.head.copy();wr=h.head.copy();la=(el-st).length;lb=(wr-el).length
 v=Vector(target)-st;d=min(v.length,la+lb-.1);axis=v.normalized();along=(la*la-lb*lb+d*d)/(2*d)
 per=Vector(pole)-st;per-=axis*per.dot(axis);per.normalize();elbow=st+axis*along+per*math.sqrt(max(0,la*la-along*along));wrist=st+axis*d
 q=(el-st).rotation_difference(elbow-st);u.matrix=Matrix.Translation(st)@q.to_matrix().to_4x4()@Matrix.Translation(-st)@u.matrix
 bpy.context.view_layer.update();el=l.head.copy();wr=h.head.copy();q=(wr-el).rotation_difference(wrist-el)
 l.matrix=Matrix.Translation(el)@q.to_matrix().to_4x4()@Matrix.Translation(-el)@l.matrix;bpy.context.view_layer.update()
def render(label,pos=(-430,350,160),target=(-12,5,146),scale=78):
 s.camera.location=pos;s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=scale;s.render.filepath=str(ROOT/('guard-after-'+label+'.png'));bpy.ops.render.render(write_still=True)
rows=[]
for pose,target,pole in [('forward',(-9,-43,156),(-58,-10,140)),('high',(-23,-35,172),(-63,-12,149))]:
 for b in a.pose.bones:b.matrix_basis=Matrix.Identity(4)
 bpy.context.view_layer.update();aim('r',target,pole);aim('l',(8,-30,137),(65,-10,132))
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();deformed=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear()
 np.save(ROOT/('guard-'+pose+'-after.npy'),deformed)
 ratio=np.linalg.norm(deformed[edges[:,0]]-deformed[edges[:,1]],axis=1)/np.maximum(lens,1e-9)
 mask=(comp==0)&(baseline[:,0]<-5)&(baseline[:,0]>-30)&(baseline[:,2]>127)&(baseline[:,2]<158)&(baseline[:,1]>0)
 sel=mask[edges[:,0]]&mask[edges[:,1]]&(lens>.05)
 rows.append({'pose':pose,'edges':int(sel.sum()),'p99':float(np.percentile(ratio[sel],99)),'max':float(ratio[sel].max()),'over_1_6':int((ratio[sel]>1.6).sum())})
 render(pose)
 if pose=='high':render('high-side',(-600,90,160),(-12,3,146),72)
(ROOT/'guard-after.json').write_text(json.dumps({'manual_proxies_only':True,'runtime_tested':False,'poses':rows},indent=2))
W=np.zeros((len(co),len(o.vertex_groups)))
for v in m.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
np.savez_compressed(ROOT/'guard-inspect.npz',co=co,comp=comp,src=src,edges=edges,faces=np.array([p.vertices[:] for p in m.polygons]),uv=np.array([d.uv[:] for d in m.uv_layers.active.data]).reshape(-1,3,2),mi=np.array([p.material_index for p in m.polygons]),weights=W,groups=np.array([g.name for g in o.vertex_groups]))
print(json.dumps(rows))
