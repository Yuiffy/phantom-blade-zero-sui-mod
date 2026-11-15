"""Separate surface response and secondary-motion sections; no new bones."""
import bpy,json,numpy as np,shutil,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent/'tripo-refine-v10'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-static-polished.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
co=np.array([v.co[:] for v in m.vertices]);comp=np.array([d.value for d in m.attributes['source_component'].data]);fc=co[np.array([p.vertices[:] for p in m.polygons])].mean(axis=1);c=np.array([comp[p.vertices[0]] for p in m.polygons]);mi=np.array([p.material_index for p in m.polygons])
materials=json.loads((BASE/'game-materials.json').read_text());slots={mat.name:i for i,mat in enumerate(m.materials)}
def slot(name,base,rough):
 mat=m.materials[base].copy();mat.name=name
 mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=rough;m.materials.append(mat);slots[name]=len(m.materials)-1
 spec=dict(materials[base]);spec.update(slot=name,roughness=rough);materials.append(spec);return len(m.materials)-1
assignments={}
for name,mask,rough in [
 ('MI_JK_Ponytail',np.isin(c,[2,22]),.43),
 ('MI_JK_HairMain',np.isin(c,[3,6]),.43),
 ('MI_JK_CardiganHem',(c==0)&(fc[:,2]<124)&(abs(fc[:,0])<30),.91),
 ('MI_JK_Cardigan',(c==0)&(fc[:,2]>=124)&(fc[:,2]<159)&((abs(fc[:,0])>9)|(fc[:,2]<147))&(mi==0),.91),
 ('MI_JK_PleatedSkirt',c==10,.79),
 ('MI_JK_Backpack',np.isin(c,[7,12,13]),.72),
 ('MI_JK_Straps',np.isin(c,[14,15,32,35,38,39]),.77),
 ('MI_JK_Stockings',c==1,.76)]:
 idx=slot(name,0,rough)
 for fi in np.flatnonzero(mask&(mi==0)):m.polygons[int(fi)].material_index=idx
 assignments[name]=int((mask&(mi==0)).sum())
# Separate charm sections by color while keeping a common low-poly simulation
# cage. Every visible detail will bind to that same cage, not run alone.
charm_slots=[]
for i in sorted(set(mi[c==101])):
 name='MI_JK_Charm_'+materials[i]['slot'].removeprefix('MI_JK_');rough=.81 if i==9 else materials[i]['roughness'];idx=slot(name,int(i),rough);mask=(c==101)&(mi==i)
 for fi in np.flatnonzero(mask):m.polygons[int(fi)].material_index=idx
 assignments[name]=int(mask.sum());charm_slots.append(name)
used=sorted(set(p.material_index for p in m.polygons));saved=[m.materials[i] for i in used];remap={i:j for j,i in enumerate(used)};face_mats=[remap[p.material_index] for p in m.polygons]
m.materials.clear()
for mat in saved:m.materials.append(mat)
for p,idx in zip(m.polygons,face_mats):p.material_index=idx
materials=[materials[i] for i in used]
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-surface-sections.blend'),compress=True)
shutil.copy2(ROOT/'sui-jk-surface-sections.blend',ROOT/'sui-jk-hun-bound.blend')
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
bpy.ops.export_scene.fbx(filepath=str(ROOT/'Sui_JK_Hun_Body.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
(ROOT/'game-materials.json').write_text(json.dumps(materials,indent=2));(ROOT/'section-map.json').write_text(json.dumps({'assigned_triangles':assignments,'charm_slots':charm_slots,'geometry_unchanged':True,'skeleton_unchanged':True,'physics_not_yet_authored':True},indent=2))
report=json.loads((ROOT/'binding-report.json').read_text());report['material_slots']=len(m.materials);report['fbx_sha256']=hashlib.sha256((ROOT/'Sui_JK_Hun_Body.fbx').read_bytes()).hexdigest();(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(assignments),flush=True)
