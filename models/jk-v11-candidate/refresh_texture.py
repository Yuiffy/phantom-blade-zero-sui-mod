import bpy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH')
image=bpy.data.images.load(str(ROOT/'textures/sui-jk-albedo-v11.png'),check_existing=False);image.pack()
for node in o.data.materials[0].node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=image
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
