import bpy, json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound-v7.blend'))
ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');me=ob.data
comp=me.attributes['source_component']
COLORS={10:(1,0,0,1), 0:(0.1,0.3,1,1), 1:(1,1,0,1), 1001:(0,1,0,1), 11:(1,0,1,1), 25:(0,1,1,1),
        2:(1,1,1,1), 3:(0.5,0.5,0.5,1)}
mats={}
for c,rgba in COLORS.items():
    m=bpy.data.materials.new(f'DBG_{c}');m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=rgba
    bs.inputs['Roughness'].default_value=1.0
    bs.inputs['Emission Color'].default_value=rgba
    bs.inputs['Emission Strength'].default_value=1.0
    mats[c]=m
default=bpy.data.materials.new('DBG_other');default.use_nodes=True
default.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.2,0.2,0.2,1)
me.materials.clear()
order=list(COLORS)+['other']
for c in order: me.materials.append(default if c=='other' else mats[c])
slot={c:i for i,c in enumerate(order)}
for p in me.polygons:
    c=comp.data[p.vertices[0]].value
    p.material_index=slot.get(c,slot['other'])
sc=bpy.context.scene;cam=sc.camera
sc.render.threads_mode='FIXED';sc.render.threads=2;sc.cycles.device='CPU';sc.cycles.samples=4
for name,pos,tgt,scale,rx,ry in [('parts-hem-zoom',(0,600,104),(0,0,104),26,760,600)]:
    cam.location=pos;cam.rotation_euler=(Vector(tgt)-Vector(pos)).to_track_quat('-Z','Y').to_euler()
    cam.data.ortho_scale=scale;sc.render.resolution_x=rx;sc.render.resolution_y=ry
    sc.render.filepath=str(ROOT/'shots'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('legend',{});print('DONE')
