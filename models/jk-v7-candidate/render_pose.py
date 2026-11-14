"""Diagnostic pose renders (not game animation) for v6 vs v7."""
import bpy, sys, math
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'shots'
OUT.mkdir(exist_ok=True)
BLENDS = {'v6': ROOT.parent / 'jk-v6-candidate' / 'sui-jk-hun-bound.blend',
          'v7': ROOT / 'sui-jk-hun-bound-v7.blend'}

POSES = {
    'turn': ([('neck_01', (0, 0, 1), 12), ('neck_02', (0, 0, 1), 18),
              ('head', (0, 0, 1), 35)], (-260, -560, 150), (0, 0, 155), 105, 760, 760),
    'nod': ([('neck_01', (1, 0, 0), 8), ('neck_02', (1, 0, 0), 10),
             ('head', (1, 0, 0), 18)], (-180, -580, 150), (0, 0, 155), 105, 760, 760),
    'arms-up': ([('upperarm_l', (0, 1, 0), -70), ('upperarm_r', (0, 1, 0), 70),
                 ('lowerarm_l', (1, 0, 0), -35), ('lowerarm_r', (1, 0, 0), -35)],
                (0, -600, 118), (0, 0, 118), 240, 700, 760),
}


def reset(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)
    bpy.context.view_layer.update()


def rotate(arm, name, axis, deg):
    pb = arm.pose.bones[name]
    basis = pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion = (basis.inverted() @ Quaternion(Vector(axis), math.radians(deg)) @ basis)


def main(tag):
    bpy.ops.wm.open_mainfile(filepath=str(BLENDS[tag]))
    scene = bpy.context.scene
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    cam = scene.camera
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    for name, (rots, pos, target, scale, rx, ry) in POSES.items():
        reset(arm)
        for bone, axis, deg in rots:
            rotate(arm, bone, axis, deg)
        bpy.context.view_layer.update()
        cam.location = pos
        cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = scale
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = str(OUT / f'{tag}-pose-{name}.png')
        bpy.ops.render.render(write_still=True)
        print('POSE', tag, name, flush=True)
    reset(arm)


main(sys.argv[-1] if sys.argv[-1] in BLENDS else 'v7')
