"""Save the current full character with the new shared atlas; no mesh edits."""
from pathlib import Path
import bpy,json,hashlib
R=Path(__file__).resolve().parents[2];W=R/'private/fishnet-v1'
source=R/'private/skin-eyes-v1/sui-jirai-motion.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH')
skin=o.data.materials['MI_Jirai_Skin'];bs=skin.node_tree.nodes.get('Principled BSDF')
old=next(l.from_node.image for l in bs.inputs['Base Color'].links if l.from_node.type=='TEX_IMAGE')
new=bpy.data.images.load(str(W/'T_Jirai_Base.png'));new.pack();old.user_remap(new)
bpy.ops.wm.save_as_mainfile(filepath=str(W/'sui-jirai-fishnet.blend'),compress=True)
(W/'editable-manifest.json').write_text(json.dumps(dict(source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    atlas_sha256=hashlib.sha256((W/'T_Jirai_Base.png').read_bytes()).hexdigest(),mesh_and_rig_unchanged=True,
    output=str(W/'sui-jirai-fishnet.blend')),indent=2))
print('FISHNET_EDITABLE_SAVED',flush=True)
