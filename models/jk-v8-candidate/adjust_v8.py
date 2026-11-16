"""Recover the petite source torso after the male-rig cage distorted it.

Keep the exact game skeleton and v7 lower body. Use per-vertex source provenance,
not a second broad x/z squeeze that also moves the legs and hands.
"""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from v7_helpers import fix_custom_normals,write_weights,sstep
REPO=Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod')
SRC=REPO/'models/jk-v7-candidate/sui-jk-hun-bound-v7.blend'
P=dict(torso_x=230.,torso_y=205.,torso_z=225.,torso_z_offset=-9.8,
       head_x=215.,head_y=205.,head_z=200.,head_top_z=199.0059357,
       head_top_source=.94140625,bow_scale_x=240.,bow_z_offset=-11.,
       shoulder_clavicle_support=0.,neck_head_ramp=(.745,.778),neck_lateral_fade=(.012,.054))
def state():
 ob=next(o for o in bpy.context.scene.objects if o.type=='MESH')
 arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
 return ob,arm,np.array([v.co[:] for v in ob.data.vertices])
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-refined-source.blend'))
source_arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
source_controls={b.name.removeprefix('mixamorig:'):source_arm.matrix_world@b.head_local for b in source_arm.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'v6-with-source-map.blend'))
ob,_,mapco=state()
source=np.array([v.vector[:] for v in ob.data.attributes['source_rest_position'].data])
sleeve_field=np.array([v.value for v in ob.data.attributes['source_sleeve_weight'].data])
mapcomp=np.array([v.value for v in ob.data.attributes['source_component'].data])
bpy.ops.wm.open_mainfile(filepath=str(REPO/'models/jk-v6-candidate/sui-jk-hun-bound.blend'))
_,_,old6=state()
assert old6.shape==mapco.shape and np.max(np.abs(old6-mapco))<1e-5
bpy.ops.wm.open_mainfile(filepath=str(SRC))
ob,arm,old=state();me=ob.data
comp=np.array([d.value for d in me.attributes['source_component'].data])
assert np.array_equal(comp,mapcomp)
assert len(old)==len(source)==35056
band_ids=np.flatnonzero(comp==23);band_tree=KDTree(len(band_ids))
for i in band_ids:band_tree.insert(Vector(source[i]),int(i))
band_tree.balance()
for i,p in enumerate(source):
 if comp[i] in [0,23] and p[0]<.00195217 and .60<p[2]<.76:
  blend=1. if comp[i]==23 else float(sstep((.025-band_tree.find(Vector(p))[2])/.015))
  sleeve_field[i]=max(sleeve_field[i],blend)
W=[{ob.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in me.vertices]
bag=np.array([v.value for v in me.attributes['backpack_vertex'].data]).astype(bool)
names={b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}
srcx,srcy,srcz=source.T
cx=.0019521676
torso=np.column_stack([(srcx-cx)*P['torso_x'],(srcy+.02928255)*P['torso_y']+6.5,srcz*P['torso_z']+P['torso_z_offset']])
head=np.column_stack([(srcx-cx)*P['head_x'],(srcy+.033186875)*P['head_y']+6.0023919,P['head_top_z']+(srcz-P['head_top_source'])*P['head_z']])
headblend=sstep((srcz-.755)/.025)
target=torso*(1-headblend[:,None])+head*headblend[:,None]
alpha=sstep((srcz-.50)/.10)
armweight=np.array([sum(v for k,v in d.items() if k.startswith(('upperarm_','lowerarm_','hand_')) or any(k.startswith(f+'_') for f in ['thumb','index','middle','ring','pinky'])) for d in W])
sleeve=sstep((armweight-.15)/.55)
# Recover narrow upper sleeves without changing wrist/finger/socket positions.
alpha*=1-sleeve*(1-sstep((srcz-.595)/.145))
keep=np.isin(comp,[1,4,5,9,10,16,17,1001])|(old[:,2]<100.)|bag
alpha[keep]=0.
headpiece=(srcz>.78)&~bag&~keep
alpha[headpiece]=1.
new=old+(target-old)*alpha[:,None]
for c in [11,25]:
 ids=(comp==c)
 new[ids,0]=(source[ids,0]-cx)*P['bow_scale_x']
 new[ids,1]=(source[ids,1]+.02928255)*P['torso_y']+6.5
 new[ids,2]=source[ids,2]*P['torso_z']+P['bow_z_offset']

stats={'neck_collar_weights_regraded':0,'proximal_sleeve_clavicle_support':0}
for i,d in enumerate(W):
 if keep[i]:continue
 p=source[i];ax=abs(p[0]-cx);z=p[2]
 if comp[i]==0 and .71<z<.785:
  # The real white shirt collar is part of component 0, not 25 (bow tails).
  # Blend the narrow neck column; the surrounding garment stays torso-driven.
  a,b=P['neck_lateral_fade'];lo,top=P['neck_head_ramp']
  lat=1-float(sstep((ax-a)/(b-a)))
  hi=float(sstep((z-lo)/(top-lo)))*lat
  n2=float(sstep((z-.740)/.016))*(1-hi)*lat
  n1=float(sstep((z-.730)/.018))*(1-hi-n2)*lat
  remove=sum(d.pop(k,0.) for k in ['head','neck_01','neck_02'])
  if remove>0:d['spine_05']=d.get('spine_05',0)+remove
  totalneck=hi+n2+n1
  d={k:v*(1-totalneck) for k,v in d.items()}
  for k,v in [('head',hi),('neck_02',n2),('neck_01',n1)]:
   if v>1e-6:d[k]=d.get(k,0)+v
  stats['neck_collar_weights_regraded']+=1
 if comp[i] in [11,25]:
  d={'spine_05':.85,'neck_01':.15}
 # Use the same harmonic sleeve/body field for geometry and skin support.
 # Reusing the old spatial cage's sleeve weights after changing the cap
 # creates different moving surfaces on the armband and inner sleeve.
 if comp[i]==0 and .64<z<.765 and ax>.035:
  side='l' if p[0]>cx else 'r';aw=float(sleeve_field[i])
  trunk={k:v for k,v in d.items() if not k.startswith(('upperarm_','lowerarm_','hand_')) and not any(k.startswith(f+'_') for f in ['thumb','index','middle','ring','pinky'])}
  total=sum(trunk.values())
  trunk={k:v/total for k,v in trunk.items()} if total>1e-6 else {'spine_05':1.}
  d={k:v*(1-aw) for k,v in trunk.items()};d['upperarm_'+side]=aw
 # Transfer proximal upper-arm support toward the clavicle to suit the
 # narrower cap; distal sleeves and hands keep v7 weights exactly.
 if comp[i]==0 and .66<z<.765 and ax>.035:
  side='l' if p[0]>cx else 'r';key='upperarm_'+side
  support=P['shoulder_clavicle_support']*float(sstep((z-.66)/.09))
  moved=d.get(key,0)*support
  if moved>1e-6:
   d[key]-=moved;d['clavicle_'+side]=d.get('clavicle_'+side,0)+moved
   stats['proximal_sleeve_clavicle_support']+=1
 # Seat the armband and its adjacent sleeve on the same upper-arm transform.
 if comp[i] in [0,23] and p[0]<cx and .60<z<.76:
  distance=band_tree.find(Vector(p))[2]
  blend=1. if comp[i]==23 else float(sstep((.025-distance)/.015))
  if blend>0:
   d={k:v*(1-blend) for k,v in d.items()};d['upperarm_r']=d.get('upperarm_r',0)+blend
 d={k:v for k,v in d.items() if v>1e-5}
 if len(d)>8:d=dict(sorted(d.items(),key=lambda x:-x[1])[:8])
 total=sum(d.values());W[i]={k:v/total for k,v in d.items()}
provenance=me.attributes.get('source_rest_position') or me.attributes.new('source_rest_position','FLOAT_VECTOR','POINT')
for i,p in enumerate(source):provenance.data[i].vector=p
authored_corner=[n.vector.copy() for n in me.corner_normals]
me.vertices.foreach_set('co',new.ravel());me.update()
normals=fix_custom_normals(me,old,new)
# v7 rotated each authored corner normal face by face. Recomputing continuous
# garment vertex normals avoids inheriting visible flat bands on the new torso.
corner=[n.vector.copy() for n in me.corner_normals]
smooth_garment=(comp==0)&(srcz<.78)&~bag
for li,loop in enumerate(me.loops):
 if smooth_garment[loop.vertex_index]:corner[li]=me.vertices[loop.vertex_index].normal.copy()
 elif headpiece[loop.vertex_index]:
  # Here v7 -> v8 is one affine scale, so use its exact inverse transpose.
  # Per-face rotations would create different normals at every smooth seam.
  n=np.array(authored_corner[li])/np.array([P['head_x']/190.,P['head_y']/190.,P['head_z']/190.])
  corner[li]=n/max(np.linalg.norm(n),1e-12)
me.normals_split_custom_set(corner)
write_weights(ob,W);me.update()
assert np.array_equal(new[keep],old[keep])
assert {b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}==names
assert all(row and abs(sum(row.values())-1)<1e-6 for row in W)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.threads_mode='FIXED';sc.render.threads=2;sc.cycles.device='CPU';sc.cycles.samples=8
sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.01
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report={'source':str(SRC),'parameters':P,'bones':len(names),'vertices':len(new),'triangles':len(me.polygons),'material_slots':len(me.materials),'skeleton_exactly_unchanged':True,'unchanged_vertices':int((np.linalg.norm(new-old,axis=1)<1e-6).sum()),'lower_body_hands_backpack_exactly_unchanged':True,'max_displacement_cm':float(np.linalg.norm(new-old,axis=1).max()),'custom_normals_fixed':normals,'unweighted_vertices':sum(not row for row in W),'max_weight_sum_error':max(abs(sum(g.weight for g in v.groups)-1) for v in me.vertices),'max_influences':max(map(len,W)),'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'weight_repairs':stats,'no_new_physics':True}
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report))
