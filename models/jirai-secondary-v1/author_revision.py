"""R6 isolated revision from the frozen R5 surface, without cumulative reshaping."""
import bpy,bmesh,json,math,hashlib,copy
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';BASE=R/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
comp=np.array([v.value for v in m.attributes['source_component'].data]);oldpos=np.array([v.co[:] for v in m.vertices]);m.calc_loop_triangles()
# Give front locks actual garment clearance before adding dynamics.
for i,v in enumerate(m.vertices):
 if comp[i] in [20,21,28,64,67]:v.co.y-=6*smooth((169-v.co.z)/24)
# Prefit hair and guides outside the exact cloth-only collision envelope.
# The old rectangular cages contained unused particles inside the shoulders.
spheres=[((0,7,177),7),((0,5,166.5),4),((0,5,158),7),((7,3,150),10.5),((-7,3,150),10.5),((7,6,141),10),((-7,6,141),10),((14,-3,154),6.5),((-14,-3,154),6.5),((14,8,154),6.5),((-14,8,154),6.5),((10,-7.5,152),3.5),((-10,-7.5,152),3.5),((13,14,154),3.8),((-13,14,154),3.8),((10,11,147),7.5),((-10,11,147),7.5)]
garment=BVHTree.FromPolygons([Vector(p) for p in oldpos],[tuple(t.vertices) for t in m.loop_triangles if m.materials[t.material_index].name in ['MI_Jirai_Blouse','MI_Jirai_Corset']],all_triangles=True)
def ylimit(x,z,front):
 limits=[]
 for (cx,cy,cz),radius in spheres:
  d=radius*radius-(x-cx)**2-(z-cz)**2
  if d>0:limits.append(cy+(-1 if front else 1)*(math.sqrt(d)+.6))
 hit,_,_,_=garment.ray_cast(Vector((x,-60 if front else 60,z)),Vector((0,1 if front else -1,0)),120)
 if hit is not None:limits.append(hit.y+(-.9 if front else .9))
 return (min(limits) if front else max(limits)) if limits else (1e6 if front else -1e6)
hair_refit=[];guide_refit=[]
for parts,front in [([4,16,31],False),([3,17,30],False),([21,67],True),([20,28,64],True)]:
 ids=np.where(np.isin(comp,parts))[0];plane=float(np.median([m.vertices[i].co.x for i in ids]))
 for i in ids:
  v=m.vertices[i];before=v.co.copy();limit=ylimit(v.co.x,v.co.z,front);plane_limit=ylimit(plane,v.co.z,front)
  v.co.y=min(v.co.y,limit,plane_limit) if front else max(v.co.y,limit,plane_limit)
  if (v.co-before).length>1e-5:hair_refit.append({'i':int(i),'distance_cm':(v.co-before).length})
for cid,parts in [(2000,[4,16,31]),(2001,[3,17,30])]:
 ids=np.where(comp==cid)[0];q=np.array([m.vertices[i].co[:] for i in np.where(np.isin(comp,parts))[0]]);x=float(np.median(q[:,0]));nr=26;cols=7;assert len(ids)==nr*cols
 for j,z in enumerate(np.linspace(q[:,2].max()+.4,q[:,2].min()-.4,nr)):
  near=q[abs(q[:,2]-z)<2]
  if len(near)<4:near=q[np.argsort(abs(q[:,2]-z))[:8]]
  lo=max(float(near[:,1].min())-.35,ylimit(x,float(z),False));hi=max(float(near[:,1].max())+.35,lo+.25)
  for k,y in enumerate(np.linspace(lo,hi,cols)):
   v=m.vertices[int(ids[j*cols+k])];v.co=(x,float(y),float(z))
def capsule_distance(p,a,b):
 axis=b-a;t=np.clip(np.dot(p-a,axis)/np.dot(axis,axis),0,1);return np.linalg.norm(p-(a+t*axis))
def skirt_clear(p):
 distances=[np.linalg.norm(p-np.array([0,5,115]))-11]
 for sign in [-1,1]:distances.append(capsule_distance(p,np.array([sign*9.3,5.3,111]),np.array([sign*12.7,5.3,82]))-9.2)
 return min(distances)
for i in np.where(comp==2002)[0]:
 v=m.vertices[int(i)];p=np.array(v.co[:]);rad=p[:2]-[0,5]
 if skirt_clear(p)<.45:
  lo=1.;hi=3.
  for _ in range(24):
   scale=(lo+hi)/2;test=p.copy();test[:2]=[0,5]+rad*scale
   if skirt_clear(test)<.45:lo=scale
   else:hi=scale
  new=p.copy();new[:2]=[0,5]+rad*hi;v.co=new;guide_refit.append({'i':int(i),'distance_cm':float(np.linalg.norm(new-p))})
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
# Front panel follows the lifting thigh much more than the hanging rear panel.
skirt_slots={i for i,x in enumerate(m.materials) if x.name in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim']};skirt_ids={i for f in m.polygons if f.material_index in skirt_slots for i in f.vertices}
for i in skirt_ids:
 p=m.vertices[i].co;front=smooth((5-p.y)/15);follow=.23*smooth((122-p.z)/24)+.71*front*smooth((122-p.z)/15);left=smooth((p.x+5)/10);weights[i]={'pelvis':1-follow,'thigh_l':follow*left,'thigh_r':follow*(1-left)}
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
verts=[];faces=[];rows=43
for z in np.linspace(77.6,111,rows):
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
# Side locks get separate coherent render sections, each with its own flat guide.
for label,parts in [('L',[21,67]),('R',[20,28,64])]:
 mat=m.materials[next(i for i,x in enumerate(m.materials) if x.name=='MI_Jirai_Hair')].copy();mat.name='MI_Jirai_Side'+label;m.materials.append(mat);slot=len(m.materials)-1
 spec.append({'slot':mat.name,'source_texture':True,'base_color_linear':[1,1,1,1],'roughness':.5,'metallic':0})
 for f in m.polygons:
  if all(comp[i] in parts for i in f.vertices):f.material_index=slot
 q=p[np.isin(comp,parts)];x=float(np.median(q[:,0]));vs=[];fs=[];cols=10;nr=30
 for z in np.linspace(q[:,2].max()+.4,q[:,2].min()-.4,nr):
  near=q[np.abs(q[:,2]-z)<2]
  if len(near)<4:near=q[np.argsort(abs(q[:,2]-z))[:8]]
  # Keep a usable particle spacing after projection; a .25 cm strip divided
  # into nine cells creates near-degenerate edges under shoulder contact.
  hi=min(float(near[:,1].max())+.35,ylimit(x,float(z),True));lo=min(float(near[:,1].min())-.35,hi-.9)
  for y in np.linspace(lo,hi,cols):vs.append((x,float(y),float(z)))
 for j in range(nr-1):
  for i in range(cols-1):a=j*cols+i;b=a+cols;fs.extend([(a,a+1,b+1),(a,b+1,b)])
 simmat=bpy.data.materials.new('MI_Jirai_Side'+label+'Sim');simmat.use_nodes=True;make(simmat.name,vs,fs,simmat,2010+len(cages),[{'head':1.} for v in vs]);cages.append({'slot':simmat.name,'vertices':len(vs),'triangles':len(fs)})
 row=copy.deepcopy(cloth[0]);row.update(slot=mat.name,name='CA_Jirai_Side'+label,max_distance=5.0);row['mask'].update(anchors=[[0,0,176]],d1=32,sim_slot=simmat.name);row['config'].update(GravityScale=.35,AnimDriveStiffness={'Low':.12,'High':.12});cloth.append(row)
for row in cloth:
 if row['slot']=='MI_Jirai_Skirt':
  row['max_distance']=10;row['mask'].update(anchors=[[0,0,122]],d1=28);row['config'].update(GravityScale=.3,AnimDriveStiffness={'Low':.12,'High':.12},FrictionCoefficient=.25)
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
