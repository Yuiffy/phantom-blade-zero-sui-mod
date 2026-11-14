"""Close-up of the nape/trapezius during a head turn, seen from behind."""
import bpy, math
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'shots'
BLENDS = {'v6': ROOT.parent / 'jk-v6-candidate' / 'sui-jk-hun-bound.blend',
          'v7': ROOT / 'sui-jk-hun-bound-v7.blend'}
ROTS = [('neck_01', (0, 0, 1), 12), ('neck_02', (0, 0, 1), 18), ('head', (0, 0, 1), 35)]
VIEWS = {'nape': ((210, 520, 175), (0, 0, 163), 62),
         'nape-45': ((-430, 330, 185), (0, 0, 163), 62)}


def main(tag):
    bpy.ops.wm.open_mainfile(filepath=str(BLENDS[tag]))
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    cam = scene.camera
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 10
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
    for name, axis, deg in ROTS:
        pb = arm.pose.bones[name]
        basis = pb.bone.matrix_local.to_quaternion()
        pb.rotation_quaternion = (basis.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ basis)
    bpy.context.view_layer.update()
    for view, (pos, target, scale) in VIEWS.items():
        cam.location = pos
        cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = scale
        scene.render.resolution_x = 620
        scene.render.resolution_y = 620
        scene.render.filepath = str(OUT / f'{tag}-{view}.png')
        bpy.ops.render.render(write_still=True)
        print('SHOT', tag, view, flush=True)


import sys
main(sys.argv[sys.argv.index('--') + 1])
