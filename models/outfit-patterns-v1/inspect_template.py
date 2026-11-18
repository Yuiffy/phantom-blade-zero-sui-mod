from pathlib import Path
import bpy,json
R=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-face-v3/face-preview.blend'))
m=next(x for x in bpy.context.scene.objects if x.type=='MESH')
rows=[]
for i,mat in enumerate(m.data.materials):
 rows.append(dict(index=i,name=mat.name,images=[dict(name=n.image.name,path=n.image.filepath) for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]))
(R/'private/outfit-patterns-v1/template-materials.json').write_text(json.dumps(rows,indent=2))
print('TEMPLATE_INSPECTED')
