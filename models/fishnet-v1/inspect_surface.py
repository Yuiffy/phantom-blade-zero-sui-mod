"""Read current editable baseline; export surface ownership and leg previews."""
from pathlib import Path
import bpy, bmesh, json
import numpy as np
from mathutils import Vector

R=Path(__file__).resolve().parents[2]; W=R/'private/fishnet-v1'
W.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R/'private/skin-eyes-v1/sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH'); m=o.data
m.calc_loop_triangles()
p=np.array([v.co[:] for v in m.vertices]); c=np.array([v.value for v in m.attributes['source_component'].data])
np.savez_compressed(W/'surface.npz',positions=p,components=c,
    uv=np.array([x.uv[:] for x in m.uv_layers.active.data]),
    loop_vertices=np.array([x.vertex_index for x in m.loops]),
    loop_triangles=np.array([x.loops[:] for x in m.loop_triangles]),
    materials=np.array([x.material_index for x in m.loop_triangles]))
rows=[]
for cid in sorted(set(c)):
    ids=np.where(c==cid)[0]; q=p[ids]
    if q[:,2].min()>120 or q[:,2].max()<20 or len(ids)<30:continue
    mats=sorted({m.materials[f.material_index].name for f in m.polygons if c[f.vertices[0]]==cid})
    rows.append(dict(component=int(cid),vertices=len(ids),minimum=q.min(0).tolist(),maximum=q.max(0).tolist(),materials=mats))
(W/'inspection.json').write_text(json.dumps(dict(components=rows,materials=[x.name for x in m.materials]),indent=2))
print(json.dumps(rows,indent=2),flush=True)
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12
s.render.resolution_x=1000;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.view_settings.exposure=.4
for name,pos,target,scale in [('front',(0,-160,70),(0,0,70),92),('back',(0,160,70),(0,0,70),92),('side',(-160,0,65),(-8,0,65),84)]:
    cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    s.render.filepath=str(W/('before-'+name+'.png'));bpy.ops.render.render(write_still=True)
