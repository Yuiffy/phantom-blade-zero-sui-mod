"""Skirt/shorts revision from SkinEyes1 geometry; Fishnet1 atlas is preserved at composition."""
import bpy,bmesh,json,hashlib,math
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-skirt-v1';BASE=R/'private/skin-eyes-v1'
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');arm=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data;m.calc_loop_triangles()
comp=np.array([v.value for v in m.attributes['source_component'].data]);slots={i for i,x in enumerate(m.materials) if x.name in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim']};ids={i for f in m.polygons if f.material_index in slots for i in f.vertices}
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
def capsule_distance(p,a,b):
 axis=b-a;t=np.clip(np.dot(p-a,axis)/np.dot(axis,axis),0,1);return np.linalg.norm(p-(a+t*axis))
def skirt_clear(p):
 distances=[np.linalg.norm(p-np.array([0,5,115]))-11]
 for sign in [-1,1]:distances.append(capsule_distance(p,np.array([sign*9.3,5.3,111]),np.array([sign*12.7,5.3,82]))-9.2)
 for sign in [-1,1]:distances.append(capsule_distance(p,np.array([sign*10.824,5.3,98]),np.array([sign*12.7,5.3,82]))-13)
 return min(distances)
prefit=[];hem_flare=[]
# The old z-slice fit mistook the short front lace hem for a complete ring,
# narrowing the hidden lower opening from 32 cm to 21 cm. Preserve an open
# flared guide below the widest lower skirt ring; the visible hem stays exact.
guide_ids=np.where(comp==2002)[0];guide_points=np.array([m.vertices[int(i)].co[:] for i in guide_ids]);rings=guide_ids.reshape(25,72)
target_rx=max(abs(guide_points[:,0]));target_ry=max(abs(guide_points[:,1]-5))
for ring in rings:
 q=np.array([m.vertices[int(i)].co[:] for i in ring])
 if q[:,2].mean()>=102:continue
 sx=max(1,target_rx/max(abs(q[:,0])));sy=max(1,target_ry/max(abs(q[:,1]-5)))
 for i,p in zip(ring,q):
  new=p.copy();new[0]*=sx;new[1]=5+(new[1]-5)*sy;m.vertices[int(i)].co=new
  if np.linalg.norm(new-p)>1e-5:hem_flare.append({'i':int(i),'distance_cm':float(np.linalg.norm(new-p))})
for i in np.where(comp==2002)[0]:
 v=m.vertices[int(i)];p=np.array(v.co[:]);rad=p[:2]-[0,5]
 if skirt_clear(p)<.45:
  lo=1.;hi=3.
  for _ in range(24):
   scale=(lo+hi)/2;test=p.copy();test[:2]=[0,5]+rad*scale
   if skirt_clear(test)<.45:lo=scale
   else:hi=scale
  new=p.copy();new[:2]=[0,5]+rad*hi;v.co=new;prefit.append({'i':int(i),'distance_cm':float(np.linalg.norm(new-p))})
for i in ids:
 p=m.vertices[i].co;front=smooth((5-p.y)/15);side=smooth(abs(p.x)/20)
 follow=.23*smooth((122-p.z)/24)+(.71*front+.50*side*(1-front))*smooth((122-p.z)/15)
 # The generated inward hip backing sits inside the safety shorts. Give it
 # the same continuous pelvis/thigh blend as the shorts rather than leaving
 # a rigid pelvic flap that can emerge when the legs cross.
 if comp[i]<2000 and 110<p.z<125:
  radius=math.hypot(p.x,p.y-5);core=smooth((15-radius)/4)
  follow=follow*(1-core)+.94*smooth((124-p.z)/18)*core
 left=smooth((p.x+5)/10);weights={'pelvis':1-follow,'thigh_l':follow*left,'thigh_r':follow*(1-left)}
 for g in list(m.vertices[i].groups):o.vertex_groups[g.group].remove([i])
 for n,v in weights.items():
  if v>1e-7:o.vertex_groups[n].add([i],v,'REPLACE')
# Give the visible lower panels room for folded thighs while preserving the
# waist and every pleat/trim connection. This is a real rest-shape revision.
flare=[]
pre_flare_normals=np.array([n.vector[:] for n in m.corner_normals]);pre_flare_positions=np.array([v.co[:] for v in m.vertices])
visible_skirt={i for f in m.polygons if m.materials[f.material_index].name=='MI_Jirai_Skirt' for i in f.vertices}
for i in visible_skirt:
 v=m.vertices[i];p=np.array(v.co[:]);rad=p[:2]-[0,5];length=np.linalg.norm(rad);amount=4*smooth((122-p[2])/14)
 if amount>0 and length>1:
  v.co[:2]=p[:2]+rad/length*amount;flare.append({'i':int(i),'distance_cm':float(amount)})
# Custom normals are encoded relative to face geometry in Blender. Transform
# their original directions with the actual flare Jacobian before re-encoding.
for f in m.polygons:
 if m.materials[f.material_index].name!='MI_Jirai_Skirt':continue
 for loop in f.loop_indices:
  p=pre_flare_positions[m.loops[loop].vertex_index];rad=p[:2]-[0,5];radius=np.linalg.norm(rad);t=float(np.clip((122-p[2])/14,0,1));amount=4*t*t*(3-2*t);da=-24*t*(1-t)/14 if 0<t<1 else 0
  j=np.eye(3);j[:2,:2]=(1+amount/radius)*np.eye(2)-amount*np.outer(rad,rad)/radius**3;j[:2,2]=rad/radius*da
  n=np.linalg.solve(j.T,pre_flare_normals[loop]);pre_flare_normals[loop]=n/np.linalg.norm(n)
m.normals_split_custom_set(pre_flare_normals.tolist());m.update()
from reduce_skirt_guide import resample_guide
guide_revision=resample_guide(o,arm)
cloth=json.loads((BASE/'cloth-spec.json').read_text())
for row in cloth:
 if row['slot']=='MI_Jirai_Skirt':
  row['max_distance']=48;row['mask'].update(anchors=[[0,0,130]],d1=38);row['config'].update(GravityScale=.3,AnimDriveStiffness={'Low':.01,'High':.01},BendingStiffnessWeighted={'Low':.15,'High':.15},bUseCCD=True,FrictionCoefficient=.1)
  row['render_pin_plane']={'z':128,'falloff':6,'rest_error_cap_cm':.25}
# Replace two independent open tubes with a continuous safety short mesh.
from safety_shorts import replace_safety_shorts
coverage=replace_safety_shorts(o,arm)
from prune_interior import prune
pruned=prune(o)
m=o.data;m.calc_loop_triangles()
(W/'coverage-authoring.json').write_text(json.dumps(coverage,indent=2))
(W/'cloth-spec.json').write_text(json.dumps(cloth,indent=2))
used_vertices={i for f in m.polygons for i in f.vertices}
(W/'source-render-contract.json').write_text(json.dumps({'used_vertices':[i in used_vertices for i in range(len(m.vertices))],'positions_blender_cm':[list(v.co) for v in m.vertices],'components':[d.value for d in m.attributes['source_component'].data],'influences':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices],'bones':[b.name for b in arm.data.bones]}))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=W/'Sui_Jirai_Hun_Body.fbx';bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report=json.loads((BASE/'binding-report.json').read_text());report.update(fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),vertices=len(m.vertices),triangles=len(m.loop_triangles),visible_triangles=sum(m.attributes['source_component'].data[t.vertices[0]].value<2000 for t in m.loop_triangles));(W/'binding-report.json').write_text(json.dumps(report,indent=2))
(W/'revision-report.json').write_text(json.dumps({'basis':'installed R6 SkinEyes1','basis_fbx_sha256':hashlib.sha256((BASE/'Sui_Jirai_Hun_Body.fbx').read_bytes()).hexdigest(),'interior_cleanup':pruned,'visible_skirt_flare':flare,'hidden_guide_revision':guide_revision,'skirt_weight_vertices':len(ids),'skirt_guide_prefit':prefit,'skirt_guide_hem_flare':hem_flare,'game_runtime_tested':False},indent=2));print('SKIRT_AUTHORED',len(ids),len(prefit))
