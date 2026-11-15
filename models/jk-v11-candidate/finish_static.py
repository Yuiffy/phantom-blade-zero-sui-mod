import bpy
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
image=bpy.data.images.load(str(ROOT/'textures/sui-jk-albedo-v11.png'),check_existing=False);image.pack()
for node in o.data.materials[0].node_tree.nodes:
 if node.type=='TEX_IMAGE':node.image=image
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=16;sc.render.threads_mode='FIXED';sc.render.threads=2;sc.render.resolution_x=1100;sc.render.resolution_y=850;sc.render.resolution_percentage=100
for name,pos,target,scale in [('stockings',(0,-600,88),(0,0,88),48),('rear-skirt',(0,600,103),(0,7,103),60),('hand',(130,-250,102),(52,-12,104),24),('charm-front',(-12,-600,137),(-12,-7,137),24),('charm-side',(-600,-4,138),(-12,-4,138),24)]:
 sc.camera.location=pos;sc.camera.rotation_euler=(Vector(target)-sc.camera.location).to_track_quat('-Z','Y').to_euler();sc.camera.data.ortho_scale=scale;sc.render.filepath=str(ROOT/('after-'+name+'.png'));bpy.ops.render.render(write_still=True)
