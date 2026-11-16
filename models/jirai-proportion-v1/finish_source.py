"""Authored halo, scalloped ornaments and opaque hidden short lining."""
import bpy,bmesh,json,math,hashlib,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
CODE=Path(__file__).resolve().parent;ROOT=CODE.parents[1]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-hun-bound.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');spec=json.loads((ROOT/'game-materials.json').read_text());objects=[body]
def material(name,color,rough=.65,metal=0):
 m=bpy.data.materials.new('MI_Jirai_'+name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 spec.append({'slot':m.name,'source_texture':False,'base_color_linear':[*color,1],'roughness':rough,'metallic':metal});return m
gold=material('HaloGold',(.58,.37,.13),.28,.72);white=material('WingWhite',(.83,.81,.86),.7);pink=material('WingPink',(.56,.15,.30),.54);black=material('ShortLining',(.009,.007,.012),.89)
def mesh(name,verts,faces,mat,bone='head',weights=None,component=900):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(mat)
 uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  p.use_smooth=True
  for li,co in zip(p.loop_indices,[(0,0),(1,0),(1,1),(0,1)]*10):uv.data[li].uv=co
 me.attributes.new('source_component','INT','POINT').data.foreach_set('value',[component]*len(verts));me.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(verts))
 if weights is None:weights=[{bone:1.} for v in verts]
 for n in sorted({n for row in weights for n in row}):
  g=o.vertex_groups.new(name=n)
  for i,row in enumerate(weights):
   if n in row:g.add([i],row[n],'REPLACE')
 o.parent=arm;o.modifiers.new('Hun Skeleton','ARMATURE').object=arm;objects.append(o);return o
def tube(name,pts,r,mat,bone='head',sides=8,component=900):
 vs=[];fs=[]
 for i,p in enumerate(pts):
  p=Vector(p);t=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);t.normalize();ref=Vector((0,1,0));u=t.cross(ref).normalized();v=t.cross(u).normalized()
  for j in range(sides):vs.append(tuple(p+r*(u*math.cos(j*2*math.pi/sides)+v*math.sin(j*2*math.pi/sides))))
 for i in range(len(pts)-1):
  for j in range(sides):k=(j+1)%sides;fs.append((i*sides+j,i*sides+k,(i+1)*sides+k,(i+1)*sides+j))
 fs.extend([tuple(reversed(range(sides))),tuple((len(pts)-1)*sides+j for j in range(sides))]);return mesh(name,vs,fs,mat,bone,component=component)
# Thin split ellipse in a slanted plane, clear of the head silhouette.
center=Vector((-9,6,209));u=Vector((.62,0,.785));v=Vector((-.55,.72,.43)).normalized()
angles=np.linspace(-.35,math.pi*2-.53,100);ring=[center+u*(16*math.cos(t))+v*(6.0*math.sin(t)) for t in angles]
tube('Halo_split_gold',ring,.23,gold,component=901)
for k in [0,-1]:
 p=ring[k];t=(ring[1]-ring[0]).normalized() if k==0 else (ring[-1]-ring[-2]).normalized();direction=t*(-1 if k==0 else 1);n=Vector((0,1,0)).cross(t).normalized()
 mesh('Halo_arrow', [p+direction*2.6,p-direction*1.8+n*.8,p-direction*.8,p-direction*1.8-n*.8],[(0,1,2),(0,2,3)],gold,component=902)
for i,t in enumerate(np.linspace(.25,2.15,9)):
 p=center+u*(16*math.cos(t))+v*(6*math.sin(t));tangent=(-u*16*math.sin(t)+v*6*math.cos(t)).normalized();normal=tangent.cross(Vector((0,1,0))).normalized()*(1 if i%2 else -1)
 tip=p+normal*1.6+tangent*1.1;cross=p+normal*.6
 mesh('Halo_leaf_%02d'%i,[p,cross+tangent*.6,tip,cross-tangent*.35],[(0,1,2),(0,2,3)],gold,component=903)

# Three rounded scallops, with shallow domed front/back faces. These are padded
# wing-shaped ornaments, not feathers; paired pink crossed straps sit on both sides.
outline=[(0,-9),(10,-10),(16,-9),(18,-5),(23,-5),(27,-2),(28,3),(26,7),(22,8),(20,11),(15,12),(9,11),(0,8)]
def catmull(poly,steps=5):
 out=[]
 for i in range(len(poly)):
  a,b,c,d=[np.array(poly[j%len(poly)],float) for j in [i-1,i,i+1,i+2]]
  for t in np.linspace(0,1,steps,endpoint=False):out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 return np.array(out)
outline=catmull(outline);mid=np.array([12.,0.]);N=len(outline)
for side in [-1,1]:
 def point(x,z,depth=0):return (side*(9+x),22+x*.10+depth,145+z)
 vs=[];fs=[]
 # Boundary and four progressively domed rings per face.
 for sign in [-1,1]:
  off=len(vs)
  for r in [1,.75,.5,.25]:
   for p in outline:vs.append(point(*(mid+(p-mid)*r),sign*1.8*(1-r*r)))
  vs.append(point(*mid,sign*1.8));c=len(vs)-1
  for j in range(3):
   for i in range(N):n=(i+1)%N;a=off+j*N+i;b=off+j*N+n;d=a+N;e=b+N;fs.extend([(a,b,e),(a,e,d)] if sign<0 else [(e,b,a),(d,e,a)])
  for i in range(N):a=off+3*N+i;b=off+3*N+(i+1)%N;fs.append((a,b,c) if sign<0 else (c,b,a))
 mesh('Scalloped_wing_'+str(side),vs,fs,white,'spine_05',component=910)
 for sign in [-1,1]:
  for n,(a,b) in enumerate([((5,8),(17,-5)),((10,-3),(22,7)),((15,10),(25,-.5))]):
   pts=[]
   for t in np.linspace(0,1,12):
    x,z=np.array(a)*(1-t)+np.array(b)*t;rad=np.linalg.norm((np.array([x,z])-mid)/np.array([20,14]));depth=sign*(1.85*max(.25,1-rad*rad)+.14);pts.append(point(x,z,depth))
   # Flat ribbon, beveled rectangular strip, rather than rope.
   direction=(Vector(pts[-1])-Vector(pts[0])).normalized();across=Vector((direction.z,0,-direction.x)).normalized()*.48
   verts=[]
   for p in pts:verts.extend([Vector(p)-across,Vector(p)+across])
   faces=[(2*i,2*i+1,2*i+3,2*i+2) for i in range(len(pts)-1)]
   mesh('Wing_crossed_ribbon',verts,faces,pink,'spine_05',component=911)

# Short opaque lining ends well above the skirt hem, with a shared pelvis band
# and two short leg tubes. It remains independently editable in the mother file.
vs=[];fs=[];ww=[];N=32
for side in [-1,1]:
 off=len(vs)
 for j,(z,rx,ry) in enumerate([(132,9,9),(125,9,9),(115,8.8,8.6),(106,8.5,8.2)]):
  for i in range(N):
   t=i*2*math.pi/N;vs.append((side*9+rx*math.cos(t),5.5+ry*math.sin(t),z));follow=.9*(132-z)/26;ww.append({'pelvis':1-follow,'thigh_'+('l' if side>0 else 'r'):follow})
 for j in range(3):
  for i in range(N):k=(i+1)%N;fs.append((off+j*N+i,off+j*N+k,off+(j+1)*N+k,off+(j+1)*N+i))
mesh('Opaque_short_lining',vs,fs,black,weights=ww,component=920)

bpy.ops.object.select_all(action='DESELECT')
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body=bpy.context.object
# Triangulate explicitly so the import/cook contract has no diagonal ambiguity.
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.triangulate(bm,faces=list(bm.faces));bad=[f for f in bm.faces if f.calc_area()<1e-9]
if bad:bmesh.ops.delete(bm,geom=bad,context='FACES')
bm.to_mesh(body.data);bm.free();body.data.update();body.data.calc_loop_triangles()
weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in body.data.vertices]
assert all(w and abs(sum(w.values())-1)<1e-5 for w in weights)
assert max(map(len,weights))<=8
(ROOT/'game-materials.json').write_text(json.dumps(spec,indent=2))
(ROOT/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':[list(v.co) for v in body.data.vertices],'influences':weights,'bones':[b.name for b in arm.data.bones]}))
report=json.loads((ROOT/'binding-report.json').read_text());report.update(vertices=len(body.data.vertices),triangles=len(body.data.loop_triangles),material_slots=len(body.data.materials),authored_accessories=['gold split halo with arrows and leaves','paired white scalloped ornaments with pink crossing ribbons','opaque short lining'])
fbx=ROOT/'Sui_Jirai_Hun_Body.fbx'
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jirai-final.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report['fbx_sha256']=hashlib.sha256(fbx.read_bytes()).hexdigest();(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2))
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=12
def reset():
 for p in arm.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0);p.scale=(1,1,1)
 bpy.context.view_layer.update()
def rotate(n,axis,angle):
 p=arm.pose.bones[n];b=p.bone.matrix_local.to_quaternion();p.rotation_quaternion=b.inverted()@Quaternion(Vector(axis),math.radians(angle))@b
def render(name,pos,target=(0,0,110),scale=247):
 if os.environ.get('PBZ_SKIP_AUDIT_RENDER')=='1':return
 bpy.context.view_layer.update();cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
render('final-front',(0,-650,115));render('final-back',(0,650,115));render('final-three-quarter',(-320,-650,130))
audit=[]
def audit_pose(name):
 bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();o=body.evaluated_get(dg);m=o.to_mesh();assert all(math.isfinite(x) for v in m.vertices for x in v.co)
 audit.append({'pose':name,'finite_vertices':True,'max_edge_cm':max((m.vertices[e.vertices[0]].co-m.vertices[e.vertices[1]].co).length for e in m.edges)});o.to_mesh_clear()
rotate('upperarm_r',(0,1,0),65);rotate('upperarm_l',(0,1,0),-55);rotate('lowerarm_r',(1,0,0),-65);audit_pose('arms');render('audit-arms-raised',(0,-650,115))
reset();rotate('thigh_l',(1,0,0),-55);rotate('calf_l',(1,0,0),80);rotate('thigh_r',(1,0,0),-35);rotate('calf_r',(1,0,0),65);rotate('head',(0,0,1),45);audit_pose('crouch');render('audit-crouch-head-turn',(-350,-650,115))
reset()
for side in ['l','r']:
 for finger in ['index','middle','ring','pinky']:
  for i in [1,2,3]:arm.pose.bones[f'{finger}_{i:02d}_{side}'].rotation_quaternion=Quaternion((0,0,1),math.radians(-45 if side=='r' else 45))
audit_pose('fingers');render('audit-finger-curl',(-180,-650,115));reset()
(ROOT/'model-audit.json').write_text(json.dumps({'bones':264,'poses':audit,'game_animations_executed':False,'manual_pose_only':True},indent=2));print('JIRAI_FINISH_OK',json.dumps(report),flush=True)
