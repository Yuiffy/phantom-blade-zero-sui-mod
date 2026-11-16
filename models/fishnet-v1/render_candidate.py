"""Compare identical offline lighting and geometry with only atlas changed."""
from pathlib import Path
import bpy,bmesh,json
from mathutils import Vector
R=Path(__file__).resolve().parents[2];W=R/'private/fishnet-v1'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/skin-eyes-v1/sui-jirai-motion.blend'))
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component']
bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free()
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=20
s.render.resolution_x=850;s.render.resolution_y=1050;s.render.resolution_percentage=100
s.view_settings.exposure=.4
skin=m.materials['MI_Jirai_Skin']
bs=skin.node_tree.nodes.get('Principled BSDF')
nodes=[link.from_node for link in bs.inputs['Base Color'].links if link.from_node.type=='TEX_IMAGE']
assert len(nodes)==1
packed=nodes[0].image
atlas_nodes=[n for mat in m.materials if mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image==packed]
original=bpy.data.images.load(str(R/'private/skin-eyes-v1/variant/textures/T_Jirai_Base.png'),check_existing=False)
print('ATLAS',original.filepath,flush=True)
candidate=bpy.data.images.load(str(W/'T_Jirai_Base.png'),check_existing=True)
views=[('front',(-16,-160,43),(-16,10,43),32),('back',(-16,160,43),(-16,10,43),32),('side',(-160,10,43),(-16,10,43),32)]
for version in ['before','after']:
    for node in atlas_nodes:node.image=original if version=='before' else candidate
    for name,pos,target,scale in views:
        cam=s.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        s.render.filepath=str(W/(version+'-calf-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('FISHNET_PREVIEW_COMPLETE',flush=True)
