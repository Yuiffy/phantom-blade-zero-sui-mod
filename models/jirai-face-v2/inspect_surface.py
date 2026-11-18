"""Read the installed R7 authoring surface and export face/UV diagnostics."""
from pathlib import Path
import bpy, bmesh, json
import numpy as np
from mathutils import Vector

R=Path(__file__).resolve().parents[2]; W=R/'private/jirai-face-v2'
W.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-skirt-v1/sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
m.calc_loop_triangles()
p=np.array([v.co[:] for v in m.vertices]);c=np.array([v.value for v in m.attributes['source_component'].data])
uv=np.array([v.uv[:] for v in m.uv_layers.active.data]);lv=np.array([v.vertex_index for v in m.loops])
lt=np.array([t.loops[:] for t in m.loop_triangles]);mt=np.array([t.material_index for t in m.loop_triangles])
np.savez_compressed(W/'surface.npz',positions=p,components=c,uv=uv,loop_vertices=lv,loop_triangles=lt,materials=mt)
rows=[]
for cid in sorted(set(c)):
 ids=np.where(c==cid)[0];q=p[ids]
 if q[:,2].max()<174 or cid>=2000:continue
 rows.append(dict(component=int(cid),vertices=len(ids),min=q.min(0).tolist(),max=q.max(0).tolist(),materials=sorted({m.materials[f.material_index].name for f in m.polygons if c[f.vertices[0]]==cid})))
(W/'inspection.json').write_text(json.dumps(dict(components=rows,materials=[x.name for x in m.materials]),indent=2))
# Render atlas colors without shadows to distinguish painted marks from lighting.
atlas=bpy.data.images.load(str(R/'private/fishnet-v1/T_Jirai_Base.png'),check_existing=True)
for material in m.materials:
 if not material.use_nodes:continue
 nodes=material.node_tree.nodes; bs=nodes.get('Principled BSDF')
 if not bs:continue
 image=next((n for n in nodes if n.type=='TEX_IMAGE'),None)
 if image:image.image=atlas
 color=bs.inputs['Base Color']; emission=nodes.new('ShaderNodeEmission')
 if color.is_linked:material.node_tree.links.new(color.links[0].from_socket,emission.inputs['Color'])
 else:emission.inputs['Color'].default_value=color.default_value
 material.node_tree.links.new(emission.outputs[0],nodes.get('Material Output').inputs['Surface'])
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=4
s.render.resolution_x=1200;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
cam=s.camera;cam.location=(-.35,-120,180);target=Vector((-.35,0,180))
cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=22
s.render.filepath=str(W/'before-unlit.png');bpy.ops.render.render(write_still=True)
print('FACE_INSPECTED',len(rows))
