"""Fit Jirai with anatomical humerus pivots and an explicit reference contract."""
import bpy,bmesh,json,math,hashlib,sys,os
import numpy as np
from pathlib import Path
from mathutils import Matrix,Quaternion,Vector
ROOT=Path(__file__).resolve().parent
DATA=ROOT.parents[1]/'private/jirai-proportion-v1'
PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui')
bpy.ops.wm.open_mainfile(filepath=str(DATA/'source.blend'))
source=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
body=next(o for o in bpy.context.scene.objects if o.type=='MESH')
S={b.name.removeprefix('mixamorig:'):source.matrix_world@b.head_local for b in source.data.bones}
bones=json.loads((PBZ/'models/hun-body.skel.json').read_text())['bones']
C=Matrix.Diagonal((1.,-1.,1.,1.));G={};parents={}
for b in bones:
 q=b['q'];local=C@Matrix.LocRotScale(Vector(b['t']),Quaternion((q[3],q[0],q[1],q[2])),Vector(b['s']))@C
 parent=bones[b['parent']]['name'] if b['parent']>=0 else None
 G[b['name']]=G[parent]@local if parent else local;parents[b['name']]=parent
original_G={n:m.copy() for n,m in G.items()}
# Move the actual humerus head, rather than bending a displaced skin around
# the old male shoulder pivot. Keep elbow, wrist, fingers and weapon bones
# fixed in world rest space. The helper bones follow their anatomical segment.
shoulder_changes=[]
for side,sign in [('l',1),('r',-1)]:
 n='upperarm_'+side;old=G[n].translation.copy();new=Vector((sign*14.5,6.5,157.0));delta=new-old
 G[n].translation=new
 for name in list(G):
  if name.startswith('upperarm_twist_01_'+side):
   shift=delta*(2/3)
  elif name.startswith('upperarm_twist_02_'+side):
   shift=delta*(1/3)
  else:
   parent=parents[name];root=None
   while parent and parent!=n:
    if parent in ['upperarm_twist_01_'+side,'upperarm_twist_02_'+side,'upperarm_correctiveRoot_'+side]:root=parent
    parent=parents[parent]
   if parent!=n:continue
   if name=='lowerarm_'+side or name.startswith(('lowerarm_','hand_')):continue
   if root=='upperarm_twist_01_'+side:shift=delta*(2/3)
   elif root=='upperarm_twist_02_'+side:shift=delta*(1/3)
   else:shift=delta
  # Finger/weapon descendants also have upperarm as ancestor: only helpers
  # whose branch enters one of these direct upperarm children may move.
  branch=name
  while parents[branch] and parents[branch]!=n:branch=parents[branch]
  if branch=='lowerarm_'+side:continue
  G[name].translation=original_G[name].translation+shift
 shoulder_changes.append({'bone':n,'old_blender_cm':list(old),'new_blender_cm':list(new),'moved_cm':delta.length})
P={n:m.translation.copy() for n,m in G.items()}
expected=[]
for b in bones:
 name=b['name'];parent=parents[name];local=G[parent].inverted()@G[name] if parent else G[name]
 t,q,s=(C@local@C).decompose();expected.append(dict(b,t=list(t),q=[q.x,q.y,q.z,q.w],s=list(s)))
(DATA/'intended-reference-skeleton.json').write_text(json.dumps({'bones':expected,'shoulder_changes':shoulder_changes,'runtime_retarget_verification_required':True},indent=2))
mapping={'Hips':'pelvis','Spine':'spine_01','Spine1':'spine_03','Spine2':'spine_05','Neck':'neck_01','Head':'head'}
child={'Hips':'Spine','Spine':'Spine1','Spine1':'Spine2','Spine2':'Neck','Neck':'Head'}
for label,side in [('Left','l'),('Right','r')]:
 for a,b in [('UpLeg','thigh'),('Leg','calf'),('Foot','foot'),('ToeBase','ball'),('Shoulder','clavicle'),('Arm','upperarm'),('ForeArm','lowerarm'),('Hand','hand')]:mapping[label+a]=b+'_'+side
 for a,b in [('UpLeg','Leg'),('Leg','Foot'),('Foot','ToeBase'),('Shoulder','Arm'),('Arm','ForeArm'),('ForeArm','Hand'),('Hand','HandMiddle1')]:child[label+a]=label+b
 for f in ['Thumb','Index','Middle','Ring','Pinky']:
  for i in range(1,4):
   n=label+'Hand'+f+str(i);mapping[n]=f.lower()+'_%02d_'%i+side
   if i<3:child[n]=label+'Hand'+f+str(i+1)
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)
def affine(A,s,d):
 m=np.eye(4);m[:3,:3]=A;m[:3,3]=np.array(d)-A@np.array(s);return m
def apply(t,p):return t[:3,:3]@np.asarray(p)+t[:3,3]
def segment(s,e,d,f,width=190):
 a=e-s;b=f-d;u=np.array(a.normalized());R=np.array(a.normalized().rotation_difference(b.normalized()).to_matrix())
 return affine(R@(np.eye(3)*width+(b.length/a.length-width)*np.outer(u,u)),s,d)
def frame(axis,normal):
 y=np.asarray(axis,dtype=float);y/=np.linalg.norm(y)
 z=np.asarray(normal,dtype=float);z-=y*np.dot(y,z);z/=np.linalg.norm(z)
 return np.column_stack((np.cross(y,z),y,z))
T={}
for s,d in mapping.items():
 if s in child:T[s]=segment(S[s],S[child[s]],P[d],P[mapping[child[s]]],190 if any(w in s for w in ['Hand','Arm','Shoulder']) else 195)
 elif s=='Head':T[s]=affine(np.eye(3)*180,S[s],P[d])
 elif 'ToeBase' in s:T[s]=T[s.replace('ToeBase','Foot')]
 else:T[s]=affine(T[s[:-1]+'2'][:3,:3],S[s],P[d])
for label,side in [('Left','l'),('Right','r')]:
 T[label+'Arm']=segment(S[label+'Arm'],S[label+'ForeArm'],P['upperarm_'+side],P['lowerarm_'+side],168)
 sa=np.array(S[label+'HandMiddle1']-S[label+'Hand']);sx=np.array(S[label+'HandIndex1']-S[label+'HandPinky1'])
 da=np.array(P['middle_01_'+side]-P['hand_'+side]);dx=np.array(P['index_01_'+side]-P['pinky_01_'+side])
 sn=np.cross(sx,sa);dn=np.cross(dx,da)
 T[label+'Hand']=affine(frame(da,dn)@np.diag([np.linalg.norm(dx)/np.linalg.norm(sx),np.linalg.norm(da)/np.linalg.norm(sa),190.])@frame(sa,sn).T,S[label+'Hand'],P['hand_'+side])
 for finger in ['Thumb','Index','Middle','Ring','Pinky']:
  for i in [1,2,3]:
   name=label+'Hand'+finger+str(i);dest=mapping[name]
   if i<3:
    a=np.array(S[child[name]]-S[name]);b=np.array(P[mapping[child[name]]]-P[dest])
    A=frame(b,dn)@np.diag([190.,np.linalg.norm(b)/np.linalg.norm(a),190.])@frame(a,sn).T
   else:A=T[name[:-1]+'2'][:3,:3]
   T[name]=affine(A,S[name],P[dest])
 # Keep platform soles above the floor without changing either foot or ball bones.
 T[label+'Shoe']=affine(np.diag([205.,205.,(P['foot_'+side].z-.6)/S[label+'Foot'].z]),S[label+'Foot'],P['foot_'+side])

def torso(p):
 v=np.asarray(p);r=np.array([v[0]*210,(v[1]-.01)*195+7.5,(v[2]-.814055)*215+P['neck_01'].z])
 r[2]-=5.4*(1-smooth((v[2]-.58)/.10))
 # Raise the waist while keeping the neck/upper chest seated. This shortens
 # the trunk, instead of stretching the complete character and its grip points.
 r[2]+=7.0*(1-smooth((v[2]-.63)/.115))
 h=smooth((v[2]-.802)/.040)
 return r*(1-h)+apply(T['Head'],v)*h
def torso_weights(z):
 chain=['pelvis','spine_01','spine_02','spine_03','spine_04','spine_05','neck_01','neck_02','head']
 if z<P[chain[0]].z:return {chain[0]:1.}
 for a,b in zip(chain,chain[1:]):
  if P[a].z<=z<P[b].z:
   t=(z-P[a].z)/(P[b].z-P[a].z);return {a:1-t,b:t}
 return {'head':1.}
def leg(p,label):
 names=[label+n for n in ['UpLeg','Leg','Foot']];z=p[2]
 idx=0 if z>S[names[1]].z else 1
 r=apply(T[names[idx]],p)
 if abs(z-S[names[1]].z)<.018:
  t=smooth((S[names[1]].z+.018-z)/.036);r=apply(T[names[0]],p)*(1-t)+apply(T[names[1]],p)*t
 foot=smooth((.16-z)/.045)
 return r*(1-foot)+apply(T[label+'Shoe'],p)*foot
def leg_weights(p,label):
 side='l' if label=='Left' else 'r';z=p[2];knee=S[label+'Leg'].z
 t=smooth((knee+.035-z)/.07);foot=smooth((.17-z)/.06)
 return {k:w for k,w in {'thigh_'+side:(1-t)*(1-foot),'calf_'+side:t*(1-foot),'foot_'+side:foot}.items() if w>1e-7}

# These IDs refer only to this audited input hash; provenance is retained in .blend.
HAIR={3,4,6,11,16,17,19,20,21,22,28,30,31,34,40,41,54,57,64,65,67,68,69,76,80,81,94,95,111,112,113,114,132}
SKIRT={2,14,38,39,43,46,47,55,59,72,74,85,90,91,92,93,107,108,144,145,147,148}
SLEEVE={23,24,25,49,50}
METAL={32,33,36,53,61,120,121,122}
mesh=body.data;world=body.matrix_world.copy();points=np.array([world@v.co for v in mesh.vertices]);comp=np.array([d.value for d in mesh.attributes['source_component'].data])
weights0=[{body.vertex_groups[g.group].name.removeprefix('mixamorig:'):g.weight for g in v.groups if g.weight>1e-7} for v in mesh.vertices]
# Harmonic sleeve attachment over the blouse surface; arm seeds and torso seeds
# are fixed by topology, so detached ribbons use the same local field.
edges=np.array([e.vertices[:] for e in mesh.edges]);values=np.zeros(len(points))
for component in [0,1]:
 mask=comp==component;e=edges[mask[edges[:,0]]&mask[edges[:,1]]];a,b=e.T
 x=np.abs(points[:,0]);z=points[:,2]
 fixed=~mask|(x<.045)|(z>.81)
 outer=mask&(x>.09)&(z<.79);values[outer]=1.;fixed|=outer
 ew=1/np.maximum(np.linalg.norm(points[a]-points[b],axis=1),.0005);degree=np.bincount(a,weights=ew,minlength=len(points))+np.bincount(b,weights=ew,minlength=len(points));unknown=mask&~fixed&(degree>0)
 for it in range(1800):
  sums=np.bincount(a,weights=ew*values[b],minlength=len(points))+np.bincount(b,weights=ew*values[a],minlength=len(points));v=(values[unknown]+sums[unknown]/degree[unknown])*.5
  err=np.max(abs(v-values[unknown])) if unknown.any() else 0;values[unknown]=v
  if err<1e-7:break
 print('ARM_FIELD',component,int(unknown.sum()),it,err,flush=True)

out=[];weights=[];sections=[]
for i,(p,c,w) in enumerate(zip(points,comp,weights0)):
 label='Left' if p[0]>=0 else 'Right';side='l' if label=='Left' else 'r'
 if c in HAIR or (c!=0 and p[2]>.845) or (c==0 and p[2]>.842):
  r=apply(T['Head'],p);dw={'head':1.};section='Hair' if c in HAIR else 'Skin'
 elif c in SKIRT:
  r=torso(p);follow=.58*smooth((.64-p[2])/.14);left=smooth((p[0]+.035)/.07)
  r[2]+=4.0*(1-smooth((p[2]-.49)/.15))
  dw={'pelvis':1-follow,'thigh_l':follow*left,'thigh_r':follow*(1-left)};section='Skirt'
 elif p[2]<.62 and c not in [0,1]:
  r=leg(p,label);dw=leg_weights(p,label);section='Legwear' if c!=5 else 'Skin'
  r[2]+=8.0*smooth((p[2]-.42)/.195)
  if p[2]<.117:r=apply(T[label+'Shoe'],p);dw={'foot_'+side:1.};section='Shoes'
 else:
  r=torso(p);dw=torso_weights(r[2]);section='Skin' if c==0 else 'Blouse'
  if c==10 or c in METAL:section='Metal' if c in METAL else 'Corset'
  strength=values[i] if c in [0,1] else (1. if c in SLEEVE else 0.)
  if strength:
   aw={}
   for n,val in w.items():
    if n.startswith(label+'Hand'):aw[n]=aw.get(n,0)+val
    elif n in [label+'Arm',label+'Shoulder']:aw[label+'Arm']=aw.get(label+'Arm',0)+val
    elif n==label+'ForeArm':aw[n]=aw.get(n,0)+val
   if not aw:aw={label+'Arm':1.}
   total=sum(aw.values());aw={n:val/total for n,val in aw.items()}
   ar=sum((apply(T[n],p)*val for n,val in aw.items()),np.zeros(3));r=r*(1-strength)+ar*strength
   dw={n:val*(1-strength) for n,val in dw.items()}
   for n,val in aw.items():dw[mapping[n]]=dw.get(mapping[n],0)+val*strength
  if c==0 and p[2]>.802:
   h=smooth((p[2]-.802)/.040);dw={n:val*(1-h) for n,val in dw.items()};dw['head']=dw.get('head',0)+h
 dw={n:val for n,val in dw.items() if val>1e-6};total=sum(dw.values());dw={n:val/total for n,val in dw.items()}
 out.append(r);weights.append(dw);sections.append(section)

body.parent=None;body.matrix_world=Matrix.Identity(4);mesh.vertices.foreach_set('co',np.asarray(out).ravel());mesh.update();body.vertex_groups.clear()
for n in sorted({n for w in weights for n in w}):
 vg=body.vertex_groups.new(name=n)
 for i,w in enumerate(weights):
  if n in w:vg.add([i],w[n],'REPLACE')
for m in list(body.modifiers):
 if m.type=='ARMATURE':body.modifiers.remove(m)
bpy.data.objects.remove(source,do_unlink=True)
arm=bpy.data.objects.new('Armature',bpy.data.armatures.new('Hun_Original_264'));bpy.context.collection.objects.link(arm)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b in bones:
 eb=arm.data.edit_bones.new(b['name']);eb.length=4;eb.matrix=G[b['name']]
 if parents[b['name']]:eb.parent=arm.data.edit_bones[parents[b['name']]]
 eb.use_connect=False;eb.use_deform=True
bpy.ops.object.mode_set(mode='OBJECT')
body.parent=arm;body.modifiers.new('Hun Original Skeleton','ARMATURE').object=arm;body.name='Sui_Jirai_Hun_Body'
base=mesh.materials[0];spec=[];slots={}
for name,rough,metal in [('Skin',.78,0),('Hair',.50,0),('Blouse',.88,0),('Corset',.57,0),('Skirt',.82,0),('Legwear',.77,0),('Shoes',.43,0),('Metal',.29,.7)]:
 mat=base.copy();mat.name='MI_Jirai_'+name;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 slots[name]=len(spec);spec.append({'slot':mat.name,'source_texture':True,'base_color_linear':[1,1,1,1],'roughness':rough,'metallic':metal});mesh.materials.append(mat)
for f in mesh.polygons:f.material_index=slots[sections[f.vertices[0]]]+1
mesh.materials.pop(index=0)
# Delete only the two audited duplicate rear suspender islands. Source indices
# survive deletion, allowing later re-edits and texture/projection checks.
bm=bmesh.new();bm.from_mesh(mesh);layer=bm.verts.layers.int['source_component'];dead=[v for v in bm.verts if v[layer] in [83,124]];bmesh.ops.delete(bm,geom=dead,context='VERTS');bm.to_mesh(mesh);bm.free()
mesh.update()
if mesh.has_custom_normals:mesh.normals_split_custom_set([(0,0,0)]*len(mesh.loops))

checks=[]
for label in ['Left','Right']:
 for finger in ['Thumb','Index','Middle','Ring','Pinky']:
  for i in [1,2,3]:
   n=label+'Hand'+finger+str(i);checks.append({'joint':n,'miss_cm':float(np.linalg.norm(apply(T[n],S[n])-P[mapping[n]]))})
assert max(x['miss_cm'] for x in checks)<1e-5
(DATA/'fit-control-checks.json').write_text(json.dumps(checks,indent=2))
(DATA/'game-materials.json').write_text(json.dumps(spec,indent=2))
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=.01
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2
scene.render.resolution_x=720;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Jirai Studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.12,.12,1)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
for o in list(scene.objects):
 if o.type in ['LIGHT','CAMERA']:bpy.data.objects.remove(o,do_unlink=True)
for name,pos,power,size in [('Key',(200,-300,350),650000,250),('Fill',(-200,-200,180),350000,250),('Rim',(100,250,280),800000,180)]:
 l=bpy.data.lights.new(name,'AREA');l.energy=power;l.shape='DISK';l.size=size;o=bpy.data.objects.new(name,l);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,110))-o.location).to_track_quat('-Z','Y').to_euler()
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));scene.collection.objects.link(cam);scene.camera=cam;cam.data.type='ORTHO';cam.data.clip_end=3000
def render(name,pos,target=(0,0,105),scale=230):
 if os.environ.get('PBZ_SKIP_AUDIT_RENDER')=='1':return
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(DATA/(name+'.png'));bpy.ops.render.render(write_still=True)
mesh.calc_loop_triangles();unweighted=sum(not v.groups for v in mesh.vertices);assert unweighted==0
report={'bones':len(bones),'vertices':len(mesh.vertices),'triangles':len(mesh.loop_triangles),'unweighted_vertices':unweighted,'removed_source_components':[83,124],'hair_rigid_head_baseline':True,'new_physics':False,'source_glb_preserved':True,'bone_matrices_unchanged':False,'shoulder_changes':shoulder_changes,'intended_reference_contract':'intended-reference-skeleton.json','runtime_retarget_verification_required':True}
(DATA/'binding-report.json').write_text(json.dumps(report,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(DATA/'sui-jirai-hun-bound.blend'),compress=True)
render('bound-front',(0,-600,108));render('bound-back',(0,600,108));render('bound-side',(600,-80,108))
print('JIRAI_BIND_OK',json.dumps(report),flush=True)
