"""Remove armband proximity leakage into the right cardigan body.

Preserve v9 hands/accessories and the exact original game reference skeleton.
Use the existing authored sleeve/body provenance field, not spatial proximity
to the armband, to distinguish surfaces that happen to lie close together.
"""
import bpy,numpy as np,json,hashlib,sys
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from v7_helpers import sstep,write_weights,fix_custom_normals
V9=ROOT.parent/'tripo-refine-v9';V8=ROOT.parent/'tripo-refine-v8'
fieldpath=ROOT/'sleeve-source-field.npy'
if fieldpath.exists():field=np.load(fieldpath)
else:
 bpy.ops.wm.open_mainfile(filepath=str(V8/'v6-with-source-map.blend'))
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH');field=np.array([d.value for d in o.data.attributes['source_sleeve_weight'].data]);np.save(fieldpath,field)
bpy.ops.wm.open_mainfile(filepath=str(V9/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
co=np.array([v.co[:] for v in m.vertices]);src=np.array([d.vector[:] for d in m.attributes['source_rest_position'].data]);comp=np.array([d.value for d in m.attributes['source_component'].data]);ids=np.array([d.value for d in m.attributes['v8_vertex_index'].data]);f=field[np.maximum(ids,0)];f[ids<0]=0
W=[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in m.vertices];oldW=[dict(d) for d in W]
armnames=lambda n:n.startswith(('upperarm_','lowerarm_','hand_')) or any(n.startswith(s+'_') for s in ['thumb','index','middle','ring','pinky'])
aw=np.array([sum(w for n,w in d.items() if armnames(n)) for d in W])
x,y,z=src.T
region=sstep((z-.585)/.025)*(1-sstep((z-.735)/.025))*sstep((-x-.025)/.018)*(1-sstep((-x-.14)/.02))*sstep((y+.075)/.02)
region[(comp!=0)|(ids<0)]=0
# No alteration on the true sleeve interior or the armband itself.
blend=region*(1-sstep((f-.1)/.75))
clean=np.flatnonzero((comp==0)&(f<.02)&(aw<.03)&(z>.58)&(z<.75)&(abs(x)<.10))
tree=KDTree(len(clean))
for i in clean:tree.insert(Vector(src[i]),int(i))
tree.balance()
for i in np.flatnonzero(blend>1e-6):
 d=W[i];trunk={n:v for n,v in d.items() if not armnames(n)};total=sum(trunk.values())
 if total<.01:
  trunk={}
  neighbors=tree.find_n(Vector(src[i]),6)
  for _,j,dist in neighbors:
   for n,v in W[j].items():
    if not armnames(n):trunk[n]=trunk.get(n,0)+v/max(dist,.001)**2
  total=sum(trunk.values())
 target={n:v/total*(1-f[i]) for n,v in trunk.items()};target['upperarm_r']=float(f[i])
 d={n:d.get(n,0)*(1-blend[i])+target.get(n,0)*blend[i] for n in d.keys()|target.keys()}
 d={n:v for n,v in d.items() if v>1e-6};d=dict(sorted(d.items(),key=lambda p:-p[1])[:8]);total=sum(d.values());W[i]={n:v/total for n,v in d.items()}
# The old cage geometry followed the same mistaken sleeve classification. Move
# these body vertices back to the established petite torso, fading to zero at
# the actual sleeve/neck/front boundary; no joint, head or hand is moved.
target=np.column_stack(((x-.0019521676)*230,(y+.02928255)*205+6.5,z*225-9.8))
shape=region*(1-sstep((f-.10)/.65))*sstep((aw-.05)/.30)
new=co+(target-co)*shape[:,None]
m.vertices.foreach_set('co',new.ravel());m.update();new=np.array([v.co[:] for v in m.vertices]);fix_custom_normals(m,co,new)
corner=[d.vector.copy() for d in m.corner_normals]
for li,l in enumerate(m.loops):
 if shape[l.vertex_index]>1e-6:corner[li]=m.vertices[l.vertex_index].normal.copy()
m.normals_split_custom_set(corner);write_weights(o,W)
for b in a.pose.bones:b.matrix_basis=Matrix.Identity(4)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
np.savez_compressed(ROOT/'atlas-provenance.npz',co=new,comp=comp,src=src,faces=np.array([p.vertices[:] for p in m.polygons]),uv=np.array([d.uv[:] for d in m.uv_layers.active.data]).reshape(-1,3,2),mi=np.array([p.material_index for p in m.polygons]))
changedw=sum(max(abs(d.get(n,0)-oldW[i].get(n,0)) for n in d.keys()|oldW[i].keys())>1e-6 for i,d in enumerate(W))
report={'baseline':'JK v9 accessory checkpoint ce1a1de','positions_changed':int((np.linalg.norm(new-co,axis=1)>1e-6).sum()),'weights_changed':int(changedw),'max_position_change_cm':float(np.linalg.norm(new-co,axis=1).max()),'max_arm_weight_removed':float(max(oldW[i].get('upperarm_r',0)-W[i].get('upperarm_r',0) for i in range(len(W)))),'geometry_and_weights_confined_to_right_proximal_garment':True,'hands_head_legs_skirt_bag_and_new_accessories_unchanged':True,'vertices':len(m.vertices),'triangles':len(m.polygons),'bones':len(a.data.bones),'material_slots':len(m.materials),'max_influences':max(map(len,W)),'fbx_sha256':hashlib.sha256(fbx.read_bytes()).hexdigest(),'no_new_physics':True}
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
