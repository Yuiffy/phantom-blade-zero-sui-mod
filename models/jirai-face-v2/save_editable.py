"""Save the exact two-albedo preview setup without altering source geometry."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v2'
bpy.ops.wm.open_mainfile(filepath=str(W/'face-preview.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
baseline=bpy.data.images.load(str(R/'private/fishnet-v1/T_Jirai_Base.png'),check_existing=True)
new=bpy.data.images.load(str(W/'T_Jirai_Base.png'),check_existing=True)
for mat in m.materials:
 if not mat.use_nodes:continue
 for node in mat.node_tree.nodes:
  if node.type=='TEX_IMAGE' and node.image and node.image.size[0]>=4096:
   node.image=new if mat.name in ['MI_Jirai_Skin','MI_Jirai_Hair'] else baseline
baseline.pack();new.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'face-preview.blend'),compress=True)
(W/'editable-source.json').write_text(json.dumps(dict(path='face-preview.blend',sha256=hashlib.sha256((W/'face-preview.blend').read_bytes()).hexdigest(),scope='R6 head geometry with isolated skin/hair albedo; offline preview only; no game physics exports',source_atlas_sha256=hashlib.sha256((W/'T_Jirai_Base.png').read_bytes()).hexdigest()),indent=2))
print('FACE_EDITABLE_BINDINGS_SAVED')
