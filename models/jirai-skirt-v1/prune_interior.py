"""Remove only skirt triangles fully enclosed by the opaque safety shorts."""
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def prune(o):
 m=o.data;m.calc_loop_triangles();c=[d.value for d in m.attributes['source_component'].data];p=[v.co.copy() for v in m.vertices]
 shorts=[tuple(t.vertices) for t in m.loop_triangles if all(c[i]==920 for i in t.vertices)];tree=BVHTree.FromPolygons(p,shorts,all_triangles=True)
 removed=[];keep_normals=[]
 for f in m.polygons:
  inside=False
  if m.materials[f.material_index].name=='MI_Jirai_Skirt':
   assert len(f.vertices)==3
   q=[p[i] for i in f.vertices];samples=q+[(q[i]+q[(i+1)%3])*.5 for i in range(3)]+[sum(q,Vector())/3]
   inside=True;clearance=[]
   for a in samples:
    hit,n,_,dist=tree.find_nearest(a)
    signed=(a-hit).dot(n)
    if not 110<a.z<124 or signed>=-.3:inside=False;break
    clearance.append(-signed)
   if inside:removed.append(dict(face=f.index,vertices=list(f.vertices),inside_shorts_min_cm=min(clearance)))
  if not inside:keep_normals.extend(m.corner_normals[i].vector.copy() for i in f.loop_indices)
 assert removed,'No enclosed generated skirt caps found'
 bm=bmesh.new();bm.from_mesh(m);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[row['face']] for row in removed],context='FACES_ONLY');bm.to_mesh(m);bm.free();m.update();assert len(keep_normals)==len(m.loops);m.normals_split_custom_set(keep_normals);m.update()
 used={i for f in m.polygons for i in f.vertices}
 return dict(removed_triangles=len(removed),basis='All 7 vertex/edge/centroid samples are at least .3 cm inside opaque shorts and z between 110 and 124 cm',faces=removed,unused_vertices=sum(i not in used for i in range(len(m.vertices))))
