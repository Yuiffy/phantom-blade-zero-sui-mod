"""V9: restore actual hand pivots, remove a duplicate loose strap, fix badges."""
import bpy,bmesh,json,hashlib,sys,numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from v7_helpers import write_weights,fix_custom_normals,sstep
V8=ROOT.parent/'tripo-refine-v8';REPO=Path('D:/workspace/myrepo/phantom-blade-zero-sui-mod')
bpy.ops.wm.open_mainfile(filepath=str(REPO/'models/jk-v6-candidate/sui-jk-hun-bound.blend'))
baseline=next(o for o in bpy.context.scene.objects if o.type=='MESH')
v6co=np.array([v.co[:] for v in baseline.data.vertices]);v6comp=np.array([d.value for d in baseline.data.attributes['source_component'].data])
v6w=[{baseline.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in baseline.data.vertices]
bpy.ops.wm.open_mainfile(filepath=str(V8/'sui-jk-hun-bound.blend'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');me=ob.data;arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
old=np.array([v.co[:] for v in me.vertices]);new=old.copy();comp=np.array([d.value for d in me.attributes['source_component'].data]);src=np.array([d.vector[:] for d in me.attributes['source_rest_position'].data])
assert np.array_equal(comp,v6comp)
W=[{ob.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in me.vertices]
skeleton={b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}
hand=np.isin(comp,[4,5]);new[hand]=v6co[hand]
for i in np.flatnonzero(hand):W[i]=v6w[i]
# The v7 shoulder squeeze also moved cuffs away from the real wrist. Restore
# v6's distal sleeve shape continuously, with zero influence above the elbow.
armweight=np.array([sum(v for n,v in d.items() if n.startswith(('lowerarm_','hand_'))) for d in W])
fade=sstep((.635-src[:,2])/.10)*sstep((np.abs(src[:,0])-.105)/.065)
fade[(comp!=0)|(armweight<.5)]=0.
new+=(v6co-old)*fade[:,None]
badges=np.isin(comp,[57,58,60,61,62,63])
for i in np.flatnonzero(badges):W[i]={'thigh_l' if old[i,0]>0 else 'thigh_r':1.}
# Component 44 is an extra strip, 100% pelvis-bound. The correct pink strap is
# already present on the thigh surface; removing the duplicate prevents a second
# strip from hanging freely when the legs separate.
remove=comp==44
report={'baseline':'JK v8','hand_vertices_restored':int(hand.sum()),'hand_max_restore_cm':float(np.linalg.norm(new[hand]-old[hand],axis=1).max()),'distal_sleeve_vertices':int((fade>0).sum()),'badges_rebound_to_thigh':int(badges.sum()),'duplicate_strap_vertices_removed':int(remove.sum()),'material_slots':len(me.materials),'skeleton_exactly_unchanged':True,'no_new_physics':True}
changed=np.linalg.norm(new-old,axis=1)>1e-6
me.vertices.foreach_set('co',new.ravel());me.update()
fix_custom_normals(me,old,new)
corner=[n.vector.copy() for n in me.corner_normals]
for li,loop in enumerate(me.loops):
 if fade[loop.vertex_index]>0:corner[li]=me.vertices[loop.vertex_index].normal.copy()
me.normals_split_custom_set(corner)
write_weights(ob,W)
orig=me.attributes.new('v8_vertex_index','INT','POINT')
for i,v in enumerate(orig.data):v.value=i
normal=me.attributes.new('v9_saved_normal','FLOAT_VECTOR','CORNER')
for d,n in zip(normal.data,me.corner_normals):d.vector=n.vector
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in np.flatnonzero(remove)],context='VERTS');bm.to_mesh(me);bm.free();me.update()
me.normals_split_custom_set([d.vector[:] for d in me.attributes['v9_saved_normal'].data]);me.attributes.remove(me.attributes['v9_saved_normal'])
image_path=ROOT/'textures/sui-jk-albedo-v9.png';image=bpy.data.images.load(str(image_path),check_existing=False);image.pack()
mat=me.materials[0]
for node in mat.node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=image
for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
assert {b.name:(b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in arm.data.bones}==skeleton
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.render.threads_mode='FIXED';sc.render.threads=2;sc.cycles.device='CPU';sc.cycles.samples=8
sc.unit_settings.system='METRIC';sc.unit_settings.scale_length=.01
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);ob.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report.update(vertices=len(me.vertices),triangles=len(me.polygons),bones=len(arm.data.bones),fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),max_influences=max(len([g for g in v.groups if g.weight>1e-7]) for v in me.vertices))
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
