"""R5: shorter limbs/neck, aligned JK donor hands, contained hips, no cotton wings."""
import bpy,bmesh,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

REPO=Path(__file__).resolve().parents[2];ROOT=REPO/'private/jirai-proportion-v1';BASE=REPO/'private/jirai-v1'
donor=json.loads((ROOT/'diagnostic/jk-hands.json').read_text())
hand_repair=json.loads((ROOT/'hand-weight-repair.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
oldG={b.name:b.matrix_local.copy() for b in arm.data.bones};parent={b.name:b.parent.name if b.parent else None for b in arm.data.bones}
def ancestor(name,root):
 while name:
  if name==root:return True
  name=parent[name]
 return False
def smooth(x):
 x=float(np.clip(x,0,1));return x*x*(3-2*x)

# Preserve material provenance and sample the existing wrist color before cutting.
im=bpy.data.images.get('jirai-albedo')
im=next(x for x in bpy.data.images if x.size[0]==4096 and x.type=='IMAGE')
pix=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(pix);pix=pix.reshape(im.size[1],im.size[0],4)
samples=[];uv=m.uv_layers[0]
for f in m.polygons:
 if f.material_index!=0:continue
 for li in f.loop_indices:
  p=m.vertices[m.loops[li].vertex_index].co
  if 42<abs(p.x)<53 and 111<p.z<122:
   u,v=uv.data[li].uv;samples.append(pix[int(v*(im.size[1]-1))%im.size[1],int(u*(im.size[0]-1))%im.size[0],:3])
assert samples
srgb=np.median(samples,axis=0)
color=[float(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for v in srgb]
handmat=bpy.data.materials.new('MI_Jirai_Hands');handmat.use_nodes=True
bs=handmat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.78
m.materials.append(handmat);hand_slot=len(m.materials)-1

bm=bmesh.new();bm.from_mesh(m);comp=bm.verts.layers.int['source_component'];origin=bm.verts.layers.int.get('original_vertex_index');dv=bm.verts.layers.deform.active
donorattr=bm.verts.layers.int.new('jk_hand_vertex')
for v in bm.verts:v[donorattr]=-1
removed_wings=sum(v[comp] in [910,911,2003,2004] for v in bm.verts)
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[comp] in [910,911,2003,2004]],context='VERTS')
groups={g.name:g.index for g in o.vertex_groups}
for w in donor['weights']:
 for n in w:
  if n not in groups:groups[n]=o.vertex_groups.new(name=n).index
def angles(loop,center,axis):
 ref=Vector((0,0,1))
 if abs(ref.dot(axis))>.9:ref=Vector((0,1,0))
 x=axis.cross(ref).normalized();y=axis.cross(x).normalized()
 return sorted([((math.atan2((v.co-center).dot(y),(v.co-center).dot(x))+2*math.pi)%(2*math.pi),v) for v in loop],key=lambda x:x[0])
bridge_count=0;cuts=[]
for side in ['l','r']:
 wrist=oldG['hand_'+side].translation;axis=(oldG['middle_01_'+side].translation-wrist).normalized();plane=wrist-axis*.8
 geom=[v for v in bm.verts if v[comp]==0 and (v.co-wrist).length<28]
 faces={f for v in geom for f in v.link_faces if all(q[comp]==0 for q in f.verts)}
 edges={e for f in faces for e in f.edges};geom=list(set(geom)|edges|faces)
 result=bmesh.ops.bisect_plane(bm,geom=geom,dist=.0001,plane_co=plane,plane_no=axis,clear_outer=True,clear_inner=False)
 ring={v for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_valid and e.is_boundary for v in e.verts}
 assert len(ring)>=8,(side,'wrist cut failed',len(ring))
 added={}
 for i,p in enumerate(donor['positions']):
  if (p[0]>0)!=(side=='l'):continue
  v=bm.verts.new(p);v[comp]=930;v[donorattr]=i
  if origin:v[origin]=-1
  for n,w in hand_repair['weights'][str(i)].items():v[dv][groups[n]]=w
  added[i]=v
 for face in donor['faces']:
  if not all(i in added for i in face):continue
  f=bm.faces.new([added[i] for i in face]);f.material_index=hand_slot;f.smooth=True
  for layer in bm.loops.layers.uv.values():
   for loop in f.loops:loop[layer].uv=(.5,.5)
 boundary={v for v in added.values() if any(e.is_boundary for e in v.link_edges)}
 assert len(boundary)==16,(side,len(boundary))
 # Both sides of the seam are carried by the wrist, so finger motion cannot
 # separate their nearly coincident positions or pinch the forearm ring.
 for v in boundary|ring:
  v[dv].clear();v[dv][groups['hand_'+side]]=1
 aa=angles(ring,wrist,axis);bb=angles(boundary,wrist,axis)
 # A zipper triangulates different wrist loop sizes without overlapping caps.
 ia=ib=0;na=len(aa);nb=len(bb)
 while ia<na or ib<nb:
  va=aa[ia%na][1];vb=bb[ib%nb][1]
  nexta=aa[(ia+1)%na][0]+(2*math.pi if ia+1>=na else 0) if ia<na else math.inf
  nextb=bb[(ib+1)%nb][0]+(2*math.pi if ib+1>=nb else 0) if ib<nb else math.inf
  if nexta<nextb:tri=[va,aa[(ia+1)%na][1],vb];ia+=1
  else:tri=[va,bb[(ib+1)%nb][1],vb];ib+=1
  f=bm.faces.new(tri);f.material_index=hand_slot;f.smooth=True;bridge_count+=1
  for layer in bm.loops.layers.uv.values():
   for loop in f.loops:loop[layer].uv=(.5,.5)
 cuts.append({'side':side,'forearm_boundary':na,'donor_boundary':nb})
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if f.material_index==hand_slot])
bm.to_mesh(m);bm.free();m.update()

# Segment transforms shorten the arm while transporting every joint and weapon
# child coherently. Finger shape/size and all hand-local socket transforms stay intact.
G={n:g.copy() for n,g in oldG.items()};affines={n:Matrix.Identity(4) for n in G};segment_report=[]
for side in ['l','r']:
 shoulder=oldG['upperarm_'+side].translation;elbow=oldG['lowerarm_'+side].translation;wrist=oldG['hand_'+side].translation
 new_elbow=shoulder+(elbow-shoulder)*.94;new_wrist=new_elbow+(wrist-elbow)*.94
 def segment(a,b,newa,factor):
  u=(b-a).normalized();A=np.eye(3)+(factor-1)*np.outer(u,u);T=Matrix.Identity(4)
  for i in range(3):
   for j in range(3):T[i][j]=float(A[i,j])
  T.translation=newa-T.to_3x3()@a;return T
 upper=segment(shoulder,elbow,shoulder,.94);lower=segment(elbow,wrist,new_elbow,.94);hand=Matrix.Translation(new_wrist-wrist)
 for n in G:
  t=hand if ancestor(n,'hand_'+side) else lower if ancestor(n,'lowerarm_'+side) else upper if ancestor(n,'upperarm_'+side) else None
  if t is not None:G[n].translation=t@oldG[n].translation;affines[n]=t
 for n in G:
  if n in ['ik_hand_'+side,'ik_weapon_'+side,'ik_weapon_'+side+'_child']:
   G[n].translation=hand@oldG[n].translation;affines[n]=hand
 if side=='r':G['ik_hand_gun'].translation=hand@oldG['ik_hand_gun'].translation
 segment_report.append({'side':side,'upperarm_old_cm':(elbow-shoulder).length,'upperarm_new_cm':(new_elbow-shoulder).length,'forearm_old_cm':(wrist-elbow).length,'forearm_new_cm':(new_wrist-new_elbow).length,'wrist_shift_cm':(new_wrist-wrist).length})
for n in G:
 shift=-3 if ancestor(n,'head') else -1.5 if n=='neck_02' else 0
 if shift:G[n].translation.z+=shift;affines[n]=Matrix.Translation((0,0,shift))

components=np.array([d.value for d in m.attributes['source_component'].data]);before=np.array([v.co[:] for v in m.vertices]);weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in m.vertices]
hip_fixed=skin_fuller=sleeve_clearance=0
for i,v in enumerate(m.vertices):
 w=weights[i];p=v.co.copy();c=int(components[i])
 # A source hip patch extended above the actual hip pivot but was fully thigh
 # weighted. Its upper rings belong to the pelvis, unlike the visible thigh.
 if c in [5,920] and p.z>108:
  f=smooth((p.z-108)/9)
  w={n:x*(1-f) for n,x in w.items()};w['pelvis']=w.get('pelvis',0)+f;hip_fixed+=1
  shrink=.10*smooth((p.z-111)/12);p.x*=1-shrink;p.y=5.5+(p.y-5.5)*(1-shrink)
 if c==2002 or any(n.startswith('thigh_') for n in w) and c not in [5,920] and c<900 and 90<p.z<135:
  # Preserve skirt ownership; do not alter visible legs, hands or body skin.
  if c==2002 or c in [2,14,38,39,43,46,47,55,59,72,74,85,90,91,92,93,107,108,144,145,147,148]:
   left=smooth((p.x+7)/14);follow=.30*smooth((121-p.z)/26);w={'pelvis':1-follow,'thigh_l':follow*left,'thigh_r':follow*(1-left)}
 v.co=sum(((affines.get(n,Matrix.Identity(4))@p)*x for n,x in w.items()),Vector((0,0,0)))
 # Build deltoid volume around the actual repaired upper-arm centerline.
 if c in [0,1,23,24,25,49,50]:
  side='l' if p.x>0 else 'r';root=G['upperarm_'+side].translation;end=G['lowerarm_'+side].translation;u=(end-root).normalized();t=(v.co-root).dot(u)/(end-root).length
  q=root+u*(v.co-root).dot(u);rad=v.co-q;strength=sum(x for n,x in w.items() if ancestor(n,'upperarm_'+side))
  own=strength>.25 and -.12<t<.78 and rad.length<10
  fade=smooth((t+.12)/.15)*(1-smooth((t-.55)/.23))
  if own and c==0:
   v.co=q+rad*(1+(.15+.16*math.exp(-((t-.18)/.22)**2))*fade);skin_fuller+=1
  elif own and c!=0 and rad.length>1e-5:
   v.co=q+rad*(1+.10*fade)+rad.normalized()*.45*fade;sleeve_clearance+=1
 total=sum(w.values());weights[i]={n:x/total for n,x in w.items() if x>1e-7}
shortslot=next(i for i,x in enumerate(m.materials) if x.name=='MI_Jirai_ShortLining')
for f in m.polygons:
 if all(components[v]==5 and m.vertices[v].co.z>109 for v in f.vertices):f.material_index=shortslot
o.vertex_groups.clear()
for n in sorted({n for w in weights for n in w}):
 g=o.vertex_groups.new(name=n)
 for i,w in enumerate(weights):
  if n in w:g.add([i],w[n],'REPLACE')
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for b in arm.data.edit_bones:b.matrix=G[b.name]
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm.pose.bones:b.matrix_basis=Matrix.Identity(4)
# Explicit native reference contract for the imported 264-bone mesh.
oldcontract=json.loads((BASE/'intended-reference-skeleton.json').read_text());C=Matrix.Diagonal((1.,-1.,1.,1.));contract=[]
for b in oldcontract['bones']:
 n=b['name'];local=G[parent[n]].inverted()@G[n] if parent[n] else G[n];t,q,s=(C@local@C).decompose();contract.append(dict(b,t=list(t),q=[q.x,q.y,q.z,q.w],s=list(s)))
(ROOT/'intended-reference-skeleton.json').write_text(json.dumps({'bones':contract,'runtime_retarget_verification_required':True,'based_on_r4_shoulder_repair':True},indent=2))
for side in ['l','r']:
 for n in ['weapon_'+side,'weapon_'+side+'_child','weapon_'+side+'_Inst']:
  assert max(abs(a-b) for rowa,rowb in zip(oldG[parent[n]].inverted()@oldG[n],G[parent[n]].inverted()@G[n]) for a,b in zip(rowa,rowb))<.0001
for i in reversed(range(len(m.materials))):
 if m.materials[i].name in ['MI_Jirai_WingL','MI_Jirai_WingR','MI_Jirai_WingLSim','MI_Jirai_WingRSim']:m.materials.pop(index=i)
if m.has_custom_normals:m.normals_split_custom_set([(0,0,0)]*len(m.loops))
m.update();m.calc_loop_triangles()
# Remove only skin concealed by the actual sleeve shell, using arm-relative
# rays. Retaining that hidden surface caused the raised-arm triangular patches.
components=np.array([d.value for d in m.attributes['source_component'].data])
points=[v.co.copy() for v in m.vertices]
shell=BVHTree.FromPolygons(points,[tuple(t.vertices) for t in m.loop_triangles if all(components[i] in [1,23,24,25,49,50] for i in t.vertices)],all_triangles=True)
covered=[]
for f in m.polygons:
 if not all(components[i]==0 for i in f.vertices):continue
 p=sum((points[i] for i in f.vertices),Vector())/len(f.vertices);side='l' if p.x>0 else 'r'
 root=G['upperarm_'+side].translation;end=G['lowerarm_'+side].translation;axis=(end-root).normalized();t=(p-root).dot(axis)/(end-root).length;center=root+axis*(p-root).dot(axis);rad=p-center
 own=sum(sum(w for n,w in weights[i].items() if ancestor(n,'upperarm_'+side)) for i in f.vertices)/len(f.vertices)
 if own>.55 and .065<t<.72 and .1<rad.length<10:
  hit,_,_,_=shell.ray_cast(center,rad.normalized(),12)
  if hit is not None:covered.append(f.index)
bm=bmesh.new();bm.from_mesh(m);bm.faces.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.faces[i] for i in covered],context='FACES')
# The generated sleeve also has two small open quads on its back surface.
# Close those actual holes with the neighboring sleeve UVs, preserving cuffs.
layer=bm.verts.layers.int['source_component'];pending={e for e in bm.edges if e.is_boundary and all(v[layer]==1 for v in e.verts)};filled_sleeve=0
while pending:
 e=pending.pop();group={e};todo=[e]
 while todo:
  for v in todo.pop().verts:
   for q in v.link_edges:
    if q in pending:pending.remove(q);group.add(q);todo.append(q)
 vs={v for e in group for v in e.verts};center=sum((v.co for v in vs),Vector())/len(vs)
 if len(group)==4 and abs(center.x)>15 and all(sum(v in e.verts for e in group)==2 for v in vs):
  samples={v:{uv:v.link_loops[0][uv].uv.copy() for uv in bm.loops.layers.uv.values()} for v in vs}
  faces=bmesh.ops.holes_fill(bm,edges=list(group),sides=4)['faces']
  for f in faces:
   f.material_index=next(i for i,x in enumerate(m.materials) if x.name=='MI_Jirai_Blouse');f.smooth=True
   for loop in f.loops:
    for uv,co in samples[loop.vert].items():loop[uv].uv=co
  filled_sleeve+=len(faces)
bmesh.ops.recalc_face_normals(bm,faces=[f for f in bm.faces if all(v[layer]==1 for v in f.verts)])
bm.to_mesh(m);bm.free();m.update();m.calc_loop_triangles()
components=np.array([d.value for d in m.attributes['source_component'].data]);weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
spec=json.loads((BASE/'game-materials.json').read_text());spec=[s for s in spec if s['slot'] not in ['MI_Jirai_WingL','MI_Jirai_WingR']]
spec.append({'slot':'MI_Jirai_Hands','source_texture':False,'base_color_linear':[*color,1],'roughness':.78,'metallic':0})
(ROOT/'game-materials.json').write_text(json.dumps(spec,indent=2))
cloth=json.loads((BASE/'cloth-spec.json').read_text());cloth=[x for x in cloth if 'Wing' not in x['slot']]
for x in cloth:
 if 'Tail' in x['slot']:x['mask']['anchors'][0][2]-=3
(ROOT/'cloth-spec.json').write_text(json.dumps(cloth,indent=2))
(ROOT/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':[list(v.co) for v in m.vertices],'influences':weights,'bones':[b.name for b in arm.data.bones]}))
visible=sum(1 for t in m.loop_triangles if components[t.vertices[0]]<2000)
report=json.loads((BASE/'binding-report.json').read_text());report.update(vertices=len(m.vertices),triangles=len(m.loop_triangles),visible_triangles=visible,render_material_slots=len(m.materials),material_slots=len(spec),optional_wings_removed=True,authored_accessories=['gold split halo','opaque short lining'],simulation_cages=[x for x in report['simulation_cages'] if 'Wing' not in x['slot']])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_Jirai_Hun_Body.fbx';bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report['fbx_sha256']=hashlib.sha256(fbx.read_bytes()).hexdigest();(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2))
audit={'arm_segments':segment_report,'head_lowered_cm':3,'neck_midpoint_lowered_cm':1.5,'hand_source':'installed JK motion v4, source components 4/5','donor_hand_vertices':len(donor['positions']),'wrist_bridge_triangles':bridge_count,'wrist_connections':cuts,'hands_keep_size_and_finger_pivots':True,'weapon_child_local_transforms_preserved':True,'upper_hip_vertices_reweighted':hip_fixed,'upperarm_skin_vertices_fuller':skin_fuller,'sleeve_vertices_given_clearance':sleeve_clearance,'removed_wing_and_guide_vertices':removed_wings,'physics_assets':len(cloth),'fbx_sha256':report['fbx_sha256'],'game_runtime_tested':False}
audit['concealed_arm_skin_faces_removed']=len(covered);audit['sleeve_holes_closed']=filled_sleeve;audit['hand_weight_repair']={k:v for k,v in hand_repair.items() if k!='weights'}
(ROOT/'revision-report.json').write_text(json.dumps(audit,indent=2));print('R5_SOURCE',json.dumps(audit))
