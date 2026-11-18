"""Carry the verified native displacement back to the complete bound JK source."""
from pathlib import Path
import bpy, numpy as np, json, hashlib
from mathutils.kdtree import KDTree

R=Path(__file__).resolve().parents[2];W=R/'private/jk-face-shape-v1'
P=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui/models/new-outfit-20261114/tripo-motion-v5/sui-jk-motion-source.blend')
bpy.ops.wm.open_mainfile(filepath=str(P))
o=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));m=o.data
old=np.array([v.co[:] for v in m.vertices]);uv=[np.array([p.uv[:] for p in layer.data]) for layer in m.uv_layers]
weights=[[(g.group,g.weight) for g in v.groups] for v in m.vertices]
indices=[list(p.vertices) for p in m.polygons]
d=np.load(W/'before.npz');f=np.load(W/'final.npz');p=d['positions'].copy();q=f['positions'].copy();p[:,1]*=-1;q[:,1]*=-1
delta=q-p;tree=KDTree(len(p))
for i,v in enumerate(p):tree.insert(v,i)
tree.balance();changed=[]
for v in m.vertices:
    _,i,dist=tree.find(v.co)
    if dist<.001 and np.linalg.norm(delta[i])>1e-7:
        v.co=old[v.index]+delta[i];changed.append(v.index)
assert len(changed)>300
assert weights==[[(g.group,g.weight) for g in v.groups] for v in m.vertices]
assert indices==[list(p.vertices) for p in m.polygons]
assert all(np.array_equal(a,np.array([p.uv[:] for p in layer.data])) for a,layer in zip(uv,m.uv_layers))
# Preserve the source's custom shading and transform it by the same local
# differential as the native authoring function, rather than smooth unrelated
# garments, fingers or accessories during a broad normal recalculation.
source_norm=np.array([n.vector[:] for n in m.corner_normals]);source_v=np.array([l.vertex_index for l in m.loops])
normal=f['normals'].copy();normal[:,1]*=-1
changed_set=set(changed)
for loop in m.loops:
    if loop.vertex_index not in changed_set:continue
    v=loop.vertex_index;near=tree.find_range(old[v],.001)
    candidates=[i for _,i,dist in near]
    oldnormal=d['normals'][candidates].copy();oldnormal[:,1]*=-1
    best=candidates[int(np.argmax(oldnormal@source_norm[loop.index]))]
    source_norm[loop.index]=normal[best]
m.normals_split_custom_set(source_norm.tolist());m.update()
armatures=[a for a in bpy.context.scene.objects if a.type=='ARMATURE']
assert len(armatures)==1 and len(armatures[0].data.bones)==264
# Keep the complete editable mother with the current Patterns1 atlas embedded.
replaced=[]
for image in list(bpy.data.images):
    if image.source!='FILE':continue
    n=image.name.lower()
    if ('albedo' in n and 'jk' in n) or n.startswith('t_jk_base'):
        image.filepath=str(R/'private/outfit-patterns-v1/jk-after.png');image.reload();image.pack();replaced.append(image.name)
out=W/'Sui_JK_FaceShape1_Bound.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(out),compress=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(W/'editable-source.json').write_text(json.dumps(dict(passed=True,source_sha256=sha(P),output_sha256=sha(out),native_sha256=sha(W/'final.npz'),changed_source_vertices=len(changed),bones=264,source_weights_uv_and_topology_exact=True,embedded_atlas_replacements=replaced),indent=2),encoding='utf8')
print('JK_FACE_BOUND_SOURCE_SAVED',len(changed),replaced)
