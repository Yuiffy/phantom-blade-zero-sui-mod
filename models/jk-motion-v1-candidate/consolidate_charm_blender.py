import bpy,json,numpy as np,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
d=json.loads((R/'charm-atlas.json').read_text());regions={r['old_slot']:r for r in d['regions']}
oldm=list(m.materials);oldnames=[x.name for x in oldm];facenames=[oldnames[p.material_index] for p in m.polygons]
assert set(regions)<=set(oldnames),'Run once on the six-color draft'
new=bpy.data.materials.new(d['new_slot']);new.use_nodes=True;n=new.node_tree.nodes;bs=n.get('Principled BSDF')
for path,socket in [(d['albedo'],'Base Color')]:
 image=bpy.data.images.load(path,check_existing=True);image.pack();node=n.new('ShaderNodeTexImage');node.image=image;new.node_tree.links.new(node.outputs['Color'],bs.inputs[socket])
bs.inputs['Roughness'].default_value=.72
final=[]
for mat in oldm:
 if mat.name in regions:
  if new not in final:final.append(new)
 else:final.append(mat)
m.materials.clear()
for mat in final:m.materials.append(mat)
index={mat.name:i for i,mat in enumerate(final)};count=0
for p,name in zip(m.polygons,facenames):
 p.material_index=index[d['new_slot'] if name in regions else name]
 if name in regions:
  for li in p.loop_indices:m.uv_layers.active.data[li].uv=regions[name]['uv']
  count+=1
assert len(final)==24
bpy.ops.wm.save_as_mainfile(filepath=str(R/'sui-jk-motion-source.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
fbx=R/'Sui_JK_Hun_Body_Motion.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
source=json.loads((W/'source-spec.json').read_text());source['fbx_sha256']=hashlib.sha256(fbx.read_bytes()).hexdigest();(W/'source-spec.json').write_text(json.dumps(source,indent=2))
print('CHARM_SINGLE_SECTION_OK',count,'triangles',len(final),'material_slots',flush=True)
