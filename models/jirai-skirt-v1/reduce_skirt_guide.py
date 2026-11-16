"""Resample only the hidden regular skirt cage; preserve every visible corner."""
import bpy,bmesh,math
import numpy as np

def resample_guide(o,arm,rows=17,columns=36):
 m=o.data;c=np.array([v.value for v in m.attributes['source_component'].data]);ix=np.where(c==2002)[0];assert len(ix)==25*72
 old=np.array([m.vertices[int(i)].co[:] for i in ix]).reshape(25,72,3)
 normals=[d.vector.copy() for f in m.polygons if all(c[i]!=2002 for i in f.vertices) for d in (m.corner_normals[j] for j in f.loop_indices)]
 material=next(x for x in m.materials if x.name=='MI_Jirai_SkirtSim')
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]==2002],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 points=[];faces=[]
 for u in np.linspace(0,24,rows):
  lo=int(u);hi=min(lo+1,24);ring=old[lo]*(1-(u-lo))+old[hi]*(u-lo)
  points.extend(ring[::2].tolist())
 for j in range(rows-1):
  for i in range(columns):
   a=j*columns+i;b=j*columns+(i+1)%columns;c=b+columns;d=a+columns
   faces.extend([(a,b,c),(a,c,d)])
 me=bpy.data.meshes.new('Skirt simulation cage');me.from_pydata(points,[],faces);me.materials.append(material);me.update();ob=bpy.data.objects.new(me.name,me);bpy.context.collection.objects.link(ob);ob.parent=arm
 me.attributes.new('source_component','INT','POINT').data.foreach_set('value',[2002]*len(points));me.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(points));uv=me.uv_layers.new(name='UVMap')
 for d in uv.data:d.uv=(.5,.5)
 for n in ['pelvis','thigh_l','thigh_r']:ob.vertex_groups.new(name=n)
 def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
 for v in me.vertices:
  p=v.co;front=smooth((5-p.y)/15);side=smooth(abs(p.x)/20);follow=.23*smooth((122-p.z)/24)+(.71*front+.50*side*(1-front))*smooth((122-p.z)/15);left=smooth((p.x+5)/10)
  for n,w in [('pelvis',1-follow),('thigh_l',follow*left),('thigh_r',follow*(1-left))]:
   if w>1e-7:ob.vertex_groups[n].add([v.index],w,'REPLACE')
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
 # Use smooth outward cage normals for cloth projection; visible normals stay exact.
 for f in me.polygons:f.use_smooth=True
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.join();o.data.update()
 out=[d.vector.copy() for d in o.data.corner_normals];out[:len(normals)]=normals;o.data.normals_split_custom_set(out);o.data.update()
 return dict(before_vertices=len(ix),vertices=len(points),triangles=len(faces),rows=rows,columns=columns,retained_corner_normals_restored=len(normals))
