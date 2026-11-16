"""Isolate bag to inspect the normally occluded body-facing texture panel."""
import bpy,bmesh
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
for version in ['v9','v10']:
 bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/('tripo-refine-'+version)/'sui-jk-hun-bound.blend'))
 o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
 comp=[d.value for d in m.attributes['source_component'].data]
 bm=bmesh.new();bm.from_mesh(m);bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if comp[v.index]!=7],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.render.threads_mode='FIXED';s.render.threads=2
 s.render.resolution_x=800;s.render.resolution_y=800
 s.camera.location=(45,-340,150);s.camera.rotation_euler=(Vector((-14,19,135))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.ortho_scale=58
 s.render.filepath=str(ROOT/('bag-inner-'+version+'.png'));bpy.ops.render.render(write_still=True)
