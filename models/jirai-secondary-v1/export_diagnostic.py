import bpy,json,bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-secondary-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/jirai-proportion-v1/sui-jirai-motion.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data;arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
W.joinpath('textures').mkdir(exist_ok=True)
im=next(x for x in bpy.data.images if x.size[0]==4096 and x.type=='IMAGE');im.filepath_raw=str(W/'textures/r5-albedo.png');im.file_format='PNG';im.save()
(W/'rig-baseline.json').write_text(json.dumps({'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'matrix':[list(row) for row in b.matrix_local]} for b in arm.data.bones],'materials':[x.name for x in m.materials],'weights':[{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]},indent=1))
comp=np.array([v.value for v in m.attributes['source_component'].data]);p=np.array([v.co[:] for v in m.vertices]);m.calc_loop_triangles()
(W/'diagnostic/left-thigh-vertices.json').write_text(json.dumps([{'i':i,'p':list(v.co)} for i,v in enumerate(m.vertices) if comp[i]==5 and v.co.x>0 and 88<v.co.z<112],indent=1))
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
clay=bpy.data.materials.new('DiagnosticClay');clay.diffuse_color=(.5,.5,.5,1);clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.5,.5,.5,1)
for f in m.polygons:f.material_index=0
m.materials[0]=clay
s=bpy.context.scene;s.cycles.samples=6;s.render.resolution_x=750;s.render.resolution_y=700;s.view_settings.exposure=.4;c=s.camera
for name,pos,target,scale in [('suspender-clay',(25,-300,95),(12,0,99),25),('thigh-back-clay',(0,300,95),(8,4,102),34)]:
 c.location=pos;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale;s.render.filepath=str(W/'diagnostic'/(name+'.png'));bpy.ops.render.render(write_still=True)
