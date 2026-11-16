import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1';O=W/'diagnostic';O.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-proportion-v1/sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;m.calc_loop_triangles();p=np.array([v.co[:] for v in m.vertices]);comp=np.array([v.value for v in m.attributes['source_component'].data])
uv=np.array([x.uv[:] for x in m.uv_layers[0].data]);lv=np.array([l.vertex_index for l in m.loops]);tri=np.array([t.loops[:] for t in m.loop_triangles]);mat=np.array([t.material_index for t in m.loop_triangles])
np.savez_compressed(W/'surface-baseline.npz',positions=p,components=comp,uv=uv,loop_vertices=lv,loop_triangles=tri,materials=mat)
summary=[]
for c in sorted(set(comp)):
 q=p[comp==c];summary.append({'id':int(c),'vertices':len(q),'bounds':[q.min(0).tolist(),q.max(0).tolist()],'centroid':q.mean(0).tolist(),'materials':sorted({m.materials[t.material_index].name for t in m.loop_triangles if comp[t.vertices[0]]==c})})
(O/'components.json').write_text(json.dumps(summary,indent=2))
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
scene=bpy.context.scene;scene.cycles.samples=6;scene.render.resolution_x=750;scene.render.resolution_y=700;scene.view_settings.exposure=.4;cam=scene.camera
for name,pos,target,scale in [('thigh-back',(0,300,82),(6,5,105),52),('suspender-front',(30,-300,90),(12,0,102),38),('hair-front',(0,-400,168),(0,0,169),85),('hair-side',(400,-80,160),(0,6,165),90)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(O/(name+'.png'));bpy.ops.render.render(write_still=True)
print('R5_SURFACE_INSPECTED')
