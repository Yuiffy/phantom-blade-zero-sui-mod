"""R6 detail revision preserving approved R5 hair, skirt and collisions from the frozen R5 surface, without cumulative reshaping."""
import bpy,bmesh,json,math,hashlib,copy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-detail-v1';BASE=R/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
comp=np.array([v.value for v in m.attributes['source_component'].data]);oldpos=np.array([v.co[:] for v in m.vertices]);m.calc_loop_triangles()
hair_refit=[];guide_refit=[]
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
oldG={b.name:b.matrix_local.copy() for b in arm.data.bones};G={n:a.copy() for n,a in oldG.items()};parents={b.name:b.parent.name if b.parent else None for b in arm.data.bones}
# Restore undeforming IK marker references. Surface proportions and FK pivots stay R5.
raw=json.loads((R/'private/jirai-v1/intended-reference-skeleton.json').read_text())['bones'];C=Matrix.Diagonal((1.,-1.,1.,1.));ref=[]
for b in raw:
 from mathutils import Quaternion
 q=Quaternion((b['q'][3],*b['q'][:3]));a=Matrix.LocRotScale(Vector(b['t']),q,Vector(b['s']));a=C@a@C;ref.append(ref[b['parent']]@a if b['parent']>=0 else a)
for b,a in zip(raw,ref):
 if b['name'].startswith('ik_'):
  assert not any(w.get(b['name'],0)>1e-7 for w in weights),b['name'];G[b['name']]=a
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b in arm.data.edit_bones:b.matrix=G[b.name]
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
# Remove the generated raised buckle/strap relief from the underlying skin.
# Ray projection changes only depth, preserving the local silhouette and leg length.
right_faces=[tuple(t.vertices) for t in m.loop_triangles if all(comp[v]==5 and oldpos[v,0]<-.1 for v in t.vertices)]
right=BVHTree.FromPolygons([Vector(p) for p in oldpos],right_faces,all_triangles=True);flatten=[]
for i,v in enumerate(m.vertices):
 p=v.co
 if comp[i]!=5 or not (6<p.x<17 and p.y<1 and 78<p.z<113):continue
 hit,_,_,_=right.ray_cast(Vector((-p.x,-25,p.z)),Vector((0,1,0)),35)
 if hit is None:continue
 a=smooth((p.x-6)/2)*smooth((17-p.x)/2)*smooth((p.z-78)/2)*smooth((113-p.z)/2)
 old=p.copy();p.y=p.y*(1-a)+hit.y*a
 if (p-old).length>1e-5:flatten.append({'i':i,'distance_cm':(p-old).length})
for i,w in enumerate(weights):
 for g in list(m.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 for name,x in w.items():
  if x>1e-7:o.vertex_groups[name].add([i],x,'REPLACE')
# Collapse the almost coincident front/back remnants of the old raised stripe.
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
local=[v for v in bm.verts if v[layer]==5 and 8<v.co.x<14 and v.co.y<.5 and 80<v.co.z<112]
before=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=local,dist=.34);merged=before-len(bm.verts)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]==77],context='VERTS')
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if all(v[layer]==5 for v in f.verts)]);bm.to_mesh(m);bm.free();m.update();m.calc_loop_triangles()
for f in m.polygons:
 if all(m.attributes['source_component'].data[i].value==5 for i in f.vertices):f.use_smooth=True
# Repaired atlas is explicitly exported for UE as well as packed into the Blend.
oldim=next(x for x in bpy.data.images if x.size[0]==4096 and x.type=='IMAGE');newim=bpy.data.images.load(str(W/'textures/jirai-albedo.png'));newim.pack()
for mat in m.materials:
 if mat.use_nodes:
  for n in mat.node_tree.nodes:
   if n.type=='TEX_IMAGE' and n.image==oldim:n.image=newim
spec=json.loads((BASE/'game-materials.json').read_text());cloth=json.loads((BASE/'cloth-spec.json').read_text());objects=[o];cages=[]
def material(name,color,rough,metal=0):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 spec.append({'slot':name,'source_texture':False,'base_color_linear':[*color,1],'roughness':rough,'metallic':metal});return mat
black=material('MI_Jirai_Suspender',(.009,.010,.013),.48);silver=material('MI_Jirai_Buckle',(.48,.51,.56),.28,.85)
m.materials.append(black);blackslot=len(m.materials)-1;m.materials.append(silver);silverslot=len(m.materials)-1
for f in m.polygons:
 if all(m.attributes['source_component'].data[i].value==29 for i in f.vertices):f.material_index=blackslot
 if all(m.attributes['source_component'].data[i].value in [106,123] for i in f.vertices):f.material_index=silverslot
comp=np.array([v.value for v in m.attributes['source_component'].data]);p=np.array([v.co[:] for v in m.vertices]);skin_faces=[tuple(t.vertices) for t in m.loop_triangles if all(comp[i]==5 and p[i,0]>0 for i in t.vertices)];skin=BVHTree.FromPolygons([Vector(a) for a in p],skin_faces,all_triangles=True)
def front(x,z):
 hit,_,_,_=skin.ray_cast(Vector((x,-30,z)),Vector((0,1,0)),40);assert hit is not None,(x,z);return hit.y
def make(name,verts,faces,mat,cid,ww):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.parent=arm;ob.modifiers.new('Hun','ARMATURE').object=arm;me.materials.append(mat);uv=me.uv_layers.new(name='UVMap')
 for v in uv.data:v.uv=(.5,.5)
 me.attributes.new('source_component','INT','POINT').data.foreach_set('value',[cid]*len(verts));me.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(verts))
 for n in sorted({n for w in ww for n in w}):
  g=ob.vertex_groups.new(name=n)
  for i,w in enumerate(ww):
   if w.get(n,0)>1e-7:g.add([i],w[n],'REPLACE')
 objects.append(ob);return ob
def legweights(p):
 hit,_,face,_=skin.ray_cast(Vector((p[0],-30,p[2])),Vector((0,1,0)),40);assert hit is not None
 ids=skin_faces[face];a,b,c=[np.array(m.vertices[i].co[:]) for i in ids];uv=np.linalg.lstsq(np.column_stack([b-a,c-a]),np.array(hit)-a,rcond=None)[0];bary=np.maximum([1-uv.sum(),uv[0],uv[1]],0);bary/=bary.sum();out={}
 for i,f in zip(ids,bary):
  for g in m.vertices[i].groups:
   name=o.vertex_groups[g.group].name;out[name]=out.get(name,0)+g.weight*float(f)
 total=sum(out.values());return {n:w/total for n,w in out.items() if w>1e-7}
verts=[];faces=[];rows=37
# Terminate beneath the skirt instead of extending through the hip crease.
# Preserve the tested row spacing and every exposed strap vertex exactly.
for z in np.linspace(77.6,111,43)[:rows]:
 cx=11.1-.052*(z-95)
 for x in [cx-.84,cx+.84]:verts.append((x,front(x,z)-.11,float(z)))
for j in range(rows-1):a=j*2;faces.extend([(a,a+1,a+3),(a,a+3,a+2)])
make('Fitted black suspender',verts,faces,black,940,[legweights(p) for p in verts])
# A small rectangular frame, pin and crossbar, seated on the same curved leg.
verts=[];faces=[]
def rail(x0,x1,z0,z1):
 start=len(verts)
 for dep in [.24,.43]:
  for x,z in [(x0,z0),(x1,z0),(x1,z1),(x0,z1)]:verts.append((x,front(x,z)-dep,z))
 faces.extend([tuple(start+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
cx=11.1-.052*(89.4-95);cz=89.4;half=1.22;hh=1.13;t=.17
rail(cx-half,cx-half+t,cz-hh,cz+hh);rail(cx+half-t,cx+half,cz-hh,cz+hh);rail(cx-half+t,cx+half-t,cz-hh,cz-hh+t);rail(cx-half+t,cx+half-t,cz+hh-t,cz+hh);rail(cx-half+t,cx+half-t,cz-.07,cz+.07);rail(cx-.07,cx+.07,cz,cz+.83)
make('Rectangular metal suspender buckle',verts,faces,silver,941,[legweights(p) for p in verts])
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();m=o.data;m.calc_loop_triangles()
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices];comp=np.array([v.value for v in m.attributes['source_component'].data])
contract=[]
for b in json.loads((BASE/'intended-reference-skeleton.json').read_text())['bones']:
 n=b['name'];local=G[parents[n]].inverted()@G[n] if parents[n] else G[n];t,q,s=(C@local@C).decompose();contract.append(dict(b,t=list(t),q=[q.x,q.y,q.z,q.w],s=list(s)))
(W/'intended-reference-skeleton.json').write_text(json.dumps({'bones':contract,'runtime_retarget_verification_required':True},indent=2))
(W/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':[list(v.co) for v in m.vertices],'influences':weights,'bones':[b.name for b in arm.data.bones]}))
(W/'game-materials.json').write_text(json.dumps(spec,indent=2));(W/'cloth-spec.json').write_text(json.dumps(cloth,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=W/'Sui_Jirai_Hun_Body.fbx';bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report=json.loads((BASE/'binding-report.json').read_text());report.update(vertices=len(m.vertices),triangles=len(m.loop_triangles),visible_triangles=int(sum(comp[t.vertices[0]]<2000 for t in m.loop_triangles)),render_material_slots=len(m.materials),material_slots=len(spec),simulation_cages=report['simulation_cages']+cages,fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),runtime_retarget_verification_required=True)
(W/'binding-report.json').write_text(json.dumps(report,indent=2));(W/'revision-report.json').write_text(json.dumps({'basis':'immutable R5','old_front_relief_vertices_flattened':flatten,'old_relief_vertices_merged':merged,'new_suspender_component':940,'new_rectangular_metal_buckle_component':941,'cloth_assets':len(cloth),'ik_markers_restored':True,'hair_prefit':hair_refit,'skirt_guide_prefit':guide_refit,'game_runtime_tested':False},indent=2));print('R6_AUTHORED',len(m.vertices),len(m.loop_triangles))
