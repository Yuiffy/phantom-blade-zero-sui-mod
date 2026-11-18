"""Apply the independently verified native face changes to the bound JK mother."""
from pathlib import Path
import bpy,numpy as np,json,hashlib
from mathutils.kdtree import KDTree

R=Path(__file__).resolve().parents[2];W=R/'private/jk-face-polish-v2';P=R/'private/jk-face-shape-v1/Sui_JK_FaceShape1_Bound.blend'
bpy.ops.wm.open_mainfile(filepath=str(P))
o=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));m=o.data
positions=np.array([v.co[:] for v in m.vertices]);weights=[[(g.group,g.weight) for g in v.groups] for v in m.vertices];indices=[list(p.vertices) for p in m.polygons]
a=np.load(W/'before.npz');b=np.load(W/'final-render.npz');p=a['positions'].copy();q=b['positions'].copy();p[:,1]*=-1;q[:,1]*=-1;delta=q-p
tree=KDTree(len(p))
for i,v in enumerate(p):tree.insert(v,i)
tree.balance();changed=[];iris=[];mapped={}
for v in m.vertices:
 _,i,dist=tree.find(v.co)
 if dist<.001:
  mapped[v.index]=i
  if np.linalg.norm(delta[i])>1e-7:v.co=positions[v.index]+delta[i];changed.append(v.index)
  if b['iris_vertices'][i]:iris.append(v.index)
assert len(changed)>50 and len(iris)>50
norm=np.array([n.vector[:] for n in m.corner_normals]);newnorm=b['normals'].copy();newnorm[:,1]*=-1
changed=set(changed);iris=set(iris)
for l in m.loops:
 if l.vertex_index in changed:
  near=[i for _,i,_ in tree.find_range(positions[l.vertex_index],.001)];oldnorm=a['normals'][near].copy();oldnorm[:,1]*=-1
  best=near[int(np.argmax(oldnorm@norm[l.index]))];norm[l.index]=newnorm[best]
 if l.vertex_index in iris:
  u,v=b['uv'][mapped[l.vertex_index],0];m.uv_layers.active.data[l.index].uv=(float(u),1-float(v))
m.normals_split_custom_set(norm.tolist());m.update()
assert weights==[[(g.group,g.weight) for g in v.groups] for v in m.vertices] and indices==[list(p.vertices) for p in m.polygons]
assert len([a for a in bpy.context.scene.objects if a.type=='ARMATURE'])==1
assert len(next(a for a in bpy.context.scene.objects if a.type=='ARMATURE').data.bones)==264
# Keep the original shared atlas for hair/garments; only the base/face material
# samples the isolated iris patch, exactly as the game-native MI does.
replaced=[]
for mat in m.materials:
 if mat and mat.use_nodes and ('base' in mat.name.lower() or 'skin' in mat.name.lower() or mat==m.materials[0]):
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image:
    name=node.image.name.lower()
    if 'albedo' in name or 't_jk_base' in name:
     im=bpy.data.images.load(str(W/'T_Jirai_Base.png'),check_existing=True);im.pack();node.image=im;replaced.append(mat.name)
out=W/'Sui_JK_FacePolish2_Bound.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(W/'editable-source.json').write_text(json.dumps(dict(passed=True,source_sha256=sha(P),output_sha256=sha(out),native_sha256=sha(W/'final-render.npz'),changed_source_vertices=len(changed),iris_source_vertices=len(iris),bones=264,source_weights_and_topology_exact=True,isolated_base_atlas_materials=replaced),indent=2),encoding='utf8')
print('JK_BOUND_SOURCE_SAVED',len(changed),len(iris),replaced)
