"""Reshape only the skirt/cage; preserve UV, weights, body and opaque shorts."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';B=R/'private/jirai-skirt-recovery-v1'
sys.path.insert(0,str(C));from skirt_shape import reshape,transformed_normals
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(B/'sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
p=np.array([v.co[:] for v in m.vertices]);n=np.array([v.vector[:] for v in m.corner_normals]);q=p.copy();components=np.array([v.value for v in m.attributes['source_component'].data])
skirt=sorted({i for f in m.polygons if m.materials[f.material_index].name=='MI_Jirai_Skirt' for i in f.vertices});cage=np.where(components==2002)[0]
q[skirt]=reshape(p[skirt]);q[cage]=reshape(p[cage],False)
for f in m.polygons:
 slot=m.materials[f.material_index].name
 if slot not in ['MI_Jirai_Skirt','MI_Jirai_SkirtSim']:continue
 ix=np.array(f.vertices);li=list(f.loop_indices);n[li]=transformed_normals(p[ix],n[li],slot=='MI_Jirai_Skirt')
m.vertices.foreach_set('co',q.ravel());m.update();m.normals_split_custom_set(n.tolist());m.update();m.calc_loop_triangles()
used={i for f in m.polygons for i in f.vertices}
contract={'used_vertices':[i in used for i in range(len(m.vertices))],'positions_blender_cm':[list(v.co) for v in m.vertices],'components':components.tolist(),'influences':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices],'bones':[b.name for b in a.data.bones]}
(W/'source-render-contract.json').write_text(json.dumps(contract))
bpy.ops.wm.save_as_mainfile(filepath=str(W/'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
fbx=W/'Sui_Jirai_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report=json.loads((B/'binding-report.json').read_text());report.update(fbx_sha256=sha(fbx),vertices=len(m.vertices),triangles=len(m.loop_triangles));(W/'binding-report.json').write_text(json.dumps(report,indent=2))
spec=json.loads((W/'variant/source-spec.json').read_text());spec.update(fbx=str(fbx),fbx_sha256=sha(fbx),source_root=str(W),expected_triangles=report['triangles']);(W/'variant/source-spec.json').write_text(json.dumps(spec,indent=2))
selection=json.loads((W/'selection.json').read_text());selection.update(source_fbx_sha256=sha(fbx),cloth_spec_sha256=sha(W/'cloth-spec.json'));(W/'selection.json').write_text(json.dumps(selection,indent=2))
report={'source_fbx_sha256':sha(fbx),'basis_fbx_sha256':sha(B/'Sui_Jirai_Hun_Body.fbx'),'visible_width_before_cm':float(np.ptp(p[skirt,0])),'visible_width_after_cm':float(np.ptp(q[skirt,0])),'rest_flare_removed_cm':4,'lower_radial_tuck_cm':.9,'lower_drop_cm':1.5,'side_additional_drop_cm':2.2,'visible_skirt_vertices':len(skirt),'cage_vertices':len(cage),'non_skirt_positions_exact':bool(np.array_equal(p[np.setdiff1d(np.arange(len(p)),skirt+list(cage))],q[np.setdiff1d(np.arange(len(p)),skirt+list(cage))])),'game_runtime_tested':False}
(W/'shape-authoring.json').write_text(json.dumps(report,indent=2));print('SKIRT_SHAPE_AUTHORED',report)
