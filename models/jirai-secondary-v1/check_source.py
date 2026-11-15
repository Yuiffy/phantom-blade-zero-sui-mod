import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1'
bpy.ops.wm.open_mainfile(filepath=str(W/'sui-jirai-motion.blend'));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
print('IMAGES',[(i.name,list(i.size),i.filepath) for i in bpy.data.images])
print('TRANSFORM',str(o.matrix_world),str(o.parent.matrix_world));print('MODS',[(x.name,x.type) for x in o.modifiers])
for mat in m.materials:
 print('MAT',mat.name,[(n.image.name,n.image.filepath) for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image])
 if mat.name=='MI_Jirai_Skin':
  print('UVLAYERS',[(u.name,u.active_render) for u in m.uv_layers]);print('NODES',[(n.name,n.type,n.uv_map if n.type=='UVMAP' else '') for n in mat.node_tree.nodes]);print('LINKS',[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links])
for c in [5,77,940,941]:
 vs=[v for v,d in zip(m.vertices,m.attributes['source_component'].data) if d.value==c];print('COMP',c,len(vs),[[min(v.co[i] for v in vs),max(v.co[i] for v in vs)] for i in range(3)])
