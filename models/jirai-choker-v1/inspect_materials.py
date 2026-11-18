from pathlib import Path
import bpy,numpy as np
r=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(r/'private/jirai-face-v3/face-preview.blend'))
obj=next(x for x in bpy.context.scene.objects if x.type=='MESH')
for i in [16,17]:
 m=obj.data.materials[i];print('CHOKER_MAT',i,m.name)
 for node in m.node_tree.nodes:
  if node.type=='BSDF_PRINCIPLED':print('BSDF',[(k,node.inputs[k].default_value[: ] if k=='Base Color' else node.inputs[k].default_value) for k in ['Base Color','Roughness','Metallic']])
  if node.type=='TEX_IMAGE':print('TEX',node.image.name,node.image.filepath)
