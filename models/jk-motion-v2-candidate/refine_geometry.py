"""Preserve the proven rig/topology while correcting halo and hanging rest shapes."""
import bpy,numpy as np,json,math,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
bpy.ops.wm.open_mainfile(filepath=str(R.with_name('tripo-motion-v1')/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
before=np.array([v.co[:] for v in m.vertices]);co=before.copy();comp=np.array([d.value for d in m.attributes['source_component'].data]);faces=np.array([p.vertices[:] for p in m.polygons]);mi=np.array([p.material_index for p in m.polygons]);norm=np.array([d.vector[:] for d in m.corner_normals]);normnew=norm.copy();reports={}
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
# Find all disconnected gold halo parts above the head. The main ring gives an
# unbiased ellipse frame; leaf decorations do not distort the fit.
halo=(mi==1)&(before[faces].mean(1)[:,2]>198);par=np.arange(len(co))
def find(i):
 while par[i]!=i:par[i]=par[par[i]];i=par[i]
 return i
for t in faces[halo]:
 root=find(t[0])
 for v in t[1:]:par[find(v)]=root
parts={}
for i in np.unique(faces[halo]):parts.setdefault(find(i),[]).append(int(i))
parts=sorted(parts.values(),key=len,reverse=True);ring=parts[0];center=before[ring].mean(0)
_,_,basis=np.linalg.svd(before[ring]-center,full_matrices=False);q=(before[ring]-center)@basis.T;extent=np.ptp(q,axis=0)
A=(extent[0]-.42)/2;B=(extent[1]-.42)/2;newA=A;newB=A*.95
for part in parts:
 p=(before[part]-center)@basis.T
 if part==ring:
  theta=np.arctan2(p[:,1]/B,p[:,0]/A)
  delta=np.column_stack(((newA-A)*np.cos(theta),(newB-B)*np.sin(theta),np.zeros(len(part))))
  co[part]+=delta@basis
 else:
  # Rotate/translate each leaf as a rigid piece at its nearest attachment to
  # the old ellipse, maintaining leaf size and gilded wire thickness.
  theta=np.arctan2(p[:,1]/B,p[:,0]/A);ellipse=np.column_stack((A*np.cos(theta),B*np.sin(theta),np.zeros(len(part))))
  j=int(np.argmin(np.linalg.norm(p-ellipse,axis=1)));t=float(theta[j]);anchor=ellipse[j];newanchor=np.array([newA*math.cos(t),newB*math.sin(t),0])
  tangent=np.array([-A*math.sin(t),B*math.cos(t)]);newtangent=np.array([-newA*math.sin(t),newB*math.cos(t)])
  angle=math.atan2(newtangent[1],newtangent[0])-math.atan2(tangent[1],tangent[0]);cs=math.cos(angle);sn=math.sin(angle);rot=np.array([[cs,-sn,0],[sn,cs,0],[0,0,1]])
  co[part]=((p-anchor)@rot.T+newanchor)@basis+center
  mask=np.isin(np.array([l.vertex_index for l in m.loops]),part);normnew[mask]=(norm[mask]@basis.T)@rot.T@basis
reports['halo']={'old_centerline_axes_cm':[2*A,2*B],'new_centerline_axes_cm':[2*newA,2*newB],'decorations_kept_rigid':True,'ring_wire_thickness_preserved_approximately':True,'parts':len(parts)}
# Relax the forward sweep of the lower ponytail, preserving its high root and
# its strand volume. The guide remains in one plane, avoiding v1 tube offsets.
mask=np.isin(comp,[2,22,2001]);t=smooth((184-before[:,2])/36)
co[mask,0]-=4*t[mask]*(comp[mask]!=2001);co[mask,1]+=5*t[mask];co[mask,2]-=2*t[mask]
# Normal transformation for this smooth shear (including strand highlights).
for li,l in enumerate(m.loops):
 i=l.vertex_index
 if not mask[i]:continue
 h=.001;zz=before[i,2];der=float((smooth((184-(zz+h))/36)-smooth((184-(zz-h))/36))/(2*h))
 J=np.array([[1,0,(-4 if comp[i]!=2001 else 0)*der],[0,1,5*der],[0,0,1-2*der]])
 n=np.linalg.inv(J).T@norm[li];normnew[li]=n/max(np.linalg.norm(n),1e-12)
reports['ponytail']={'root_z_fixed_above_cm':184,'lower_tip_rest_delta_cm':[-4,5,-2],'planar_guide_retained':True,'high_root_geometry_unchanged':bool(np.array_equal(co[mask&(before[:,2]>=184)],before[mask&(before[:,2]>=184)]))}
# Keep the real strap attachment fixed; lift the cat's lower body 1.2 cm away
# from the cardigan with a continuous neck transition, including its cage.
charm=np.isin(comp,[101,102,2002]);ct=smooth((143.5-before[:,2])/3.0);co[charm,1]-=1.2*ct[charm]
reports['charm']={'outward_body_offset_cm':1.2,'attachment_preserved_above_z_cm':143.5,'cage_moves_with_visible_body':True}
for v,p in zip(m.vertices,co):v.co=p
m.update();m.normals_split_custom_set([Vector(n).normalized() for n in normnew])
image=bpy.data.images.load(str(R/'textures/sui-jk-albedo-v2.png'),check_existing=False);image.pack()
for mat in m.materials:
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and 'albedo-v11' in node.image.name:node.image=image
image2=bpy.data.images.load(str(R/'textures/T_JK_CharmAtlas.png'),check_existing=False);image2.pack()
for node in m.materials[18].node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=image2
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in m.vertices]
old=json.loads((R.with_name('tripo-motion-v1')/'source-render-contract.json').read_text());assert weights==old['influences']
changed=np.linalg.norm(co-before,axis=1)>1e-6;allowed=np.zeros(len(co),bool);allowed[np.unique(faces[halo])]=True;allowed|=mask|charm;assert not np.any(changed&~allowed)
assert len(a.data.bones)==264 and len(m.polygons)==72305
(R/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':[v.co[:] for v in m.vertices],'influences':weights,'bones':[b.name for b in a.data.bones],'source_components':comp.tolist()}))
reports.update(changed_vertices=int(changed.sum()),weights_exactly_preserved=True,unrelated_positions_preserved=True,bones=264,triangles=72305)
(R/'geometry-repair.json').write_text(json.dumps(reports,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(R/'sui-jk-motion-source.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
bpy.ops.export_scene.fbx(filepath=str(R/'Sui_JK_Hun_Body_Motion.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
spec=json.loads((W/'source-spec.json').read_text());spec.update(source_root=str(R),fbx=str(R/'Sui_JK_Hun_Body_Motion.fbx'),fbx_sha256=hashlib.sha256((R/'Sui_JK_Hun_Body_Motion.fbx').read_bytes()).hexdigest());(W/'source-spec.json').write_text(json.dumps(spec,indent=2))
print('GEOMETRY_REPAIR_OK',json.dumps(reports),flush=True)
