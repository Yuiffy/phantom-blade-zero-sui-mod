"""Opaque continuous shorts: one waist, two leg openings, a shared crotch seam."""
import bpy,bmesh,math
import numpy as np
from collections import Counter,defaultdict
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
def replace_safety_shorts(o,arm):
 m=o.data;slot=next(i for i,x in enumerate(m.materials) if x.name=='MI_Jirai_ShortLining')
 retained_normals=[d.vector.copy() for f in m.polygons if all(m.attributes['source_component'].data[i].value!=920 for i in f.vertices) for d in (m.corner_normals[j] for j in f.loop_indices)]
 bm=bmesh.new();bm.from_mesh(m);c=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[c]==920],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 backup=0
 for f in m.polygons:
  if all(m.attributes['source_component'].data[i].value==5 and m.vertices[i].co.z>104.5 for i in f.vertices):f.material_index=slot;backup+=1
 verts=[];faces=[];N=64
 for z,rx,ry in [(125,14.5,9.5),(120,17.2,9.7),(113,20.2,12.2)]:
  for i in range(N):
   t=i*math.tau/N;verts.append((rx*math.sin(t),4.5-ry*math.cos(t),z))
 for j in range(2):
  for i in range(N):k=(i+1)%N;faces.append((j*N+i,j*N+k,(j+1)*N+k,(j+1)*N+i))
 seam=[]
 for k in range(1,16):
  t=k/16;seam.append(len(verts));verts.append((0,4.5+12.2*(1-2*t),113-7*math.sin(math.pi*t)))
 for side in [1,-1]:
  top=[2*N+(side*i)%N for i in range(33)]+seam
  angles=np.concatenate([np.linspace(-math.pi/2,math.pi/2,33),np.linspace(math.pi/2,3*math.pi/2,17)[1:-1]])
  assert len(top)==len(angles)==48
  starts=np.array([verts[i] for i in top]);last=top
  for j in range(1,7):
   t=j/6;ring=[]
   for start,angle in zip(starts,angles):
    end=np.array((side*(11.4+9.4*math.cos(angle)),5.3+10.3*math.sin(angle),103));p=start*(1-t)+end*t;ring.append(len(verts));verts.append(p.tolist())
   for i in range(48):k=(i+1)%48;faces.append((last[i],last[k],ring[k],ring[i]))
   last=ring
 me=bpy.data.meshes.new('Continuous opaque safety shorts');me.from_pydata(verts,[],faces);me.materials.append(m.materials[slot]);me.update();ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);ob.parent=arm;ob.modifiers.new('Hun','ARMATURE').object=arm
 me.attributes.new('source_component','INT','POINT').data.foreach_set('value',[920]*len(verts));me.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(verts));uv=me.uv_layers.new(name='UVMap')
 for d in uv.data:d.uv=(.5,.5)
 for n in ['pelvis','thigh_l','thigh_r']:ob.vertex_groups.new(name=n)
 for v in me.vertices:
  f=.94*smooth((124-v.co.z)/18);left=smooth((v.co.x+5)/10)
  for n,w in [('pelvis',1-f),('thigh_l',f*left),('thigh_r',f*(1-left))]:
   if w>1e-7:ob.vertex_groups[n].add([v.index],w,'REPLACE')
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update();me.calc_loop_triangles()
 for f in me.polygons:f.use_smooth=True
 counts=Counter(tuple(sorted((f.vertices[i],f.vertices[(i+1)%3]))) for f in me.polygons for i in range(3));assert max(counts.values())==2
 adj=defaultdict(set)
 for (a,b),count in counts.items():
  if count==1:adj[a].add(b);adj[b].add(a)
 assert all(len(x)==2 for x in adj.values());seen=set();loops=[]
 for i in adj:
  if i in seen:continue
  todo=[i];seen.add(i);part=[]
  while todo:
   j=todo.pop();part.append(j)
   for k in adj[j]-seen:seen.add(k);todo.append(k)
  q=np.array([me.vertices[j].co[:] for j in part]);loops.append(dict(vertices=len(part),min=q.min(0).tolist(),max=q.max(0).tolist()))
 assert len(loops)==3 and sum(x['min'][2]>124 for x in loops)==1 and sum(x['max'][2]<104 for x in loops)==2,loops
 report=dict(continuous_crotch_seam=True,one_waist_two_leg_openings=True,boundary_loops=loops,opaque_material='MI_Jirai_ShortLining',skin_backup_faces=backup,hem_z_cm=103,vertices=len(me.vertices),triangles=len(me.loop_triangles))
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.data.update()
 # BMesh deletion discards imported corner normals. Restore every retained
 # corner, including the skirt guide, before FBX projection is authored.
 normals=[d.vector.copy() for d in o.data.corner_normals];normals[:len(retained_normals)]=retained_normals;o.data.normals_split_custom_set(normals);o.data.update()
 report['retained_corner_normals_restored']=len(retained_normals)
 return report
