"""Render matched A/B frames for v6 and v7 (same cameras, same lighting)."""
import bpy, json, sys, os
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
V6 = ROOT.parent / 'jk-v6-candidate' / 'sui-jk-hun-bound.blend'
V7 = ROOT / 'sui-jk-hun-bound-v7.blend'
OUT = ROOT / 'shots'
OUT.mkdir(exist_ok=True)

SHOTS = [
    ('front', (0, -600, 110), (0, 0, 110), 235, 800, 1000),
    ('side', (-600, -80, 110), (0, 0, 110), 235, 800, 1000),
    ('back', (0, 600, 110), (0, 0, 110), 235, 800, 1000),
    ('head', (0, -600, 162), (0, 0, 162), 78, 700, 700),
    ('hem-back', (0, 600, 105), (0, 0, 105), 62, 700, 620),
    ('hem-side', (-600, -150, 105), (0, 0, 105), 62, 700, 620),
]


def setup(blend):
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 8
    scene.render.film_transparent = False
    cam = scene.camera
    return scene, cam


def shoot(tag, only=None):
    for name, pos, target, scale, rx, ry in SHOTS:
        if only and name not in only:
            continue
        scene, cam = bpy.context.scene, bpy.context.scene.camera
        cam.location = pos
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        cam.data.ortho_scale = scale
        scene.render.resolution_x = rx
        scene.render.resolution_y = ry
        scene.render.filepath = str(OUT / f'{tag}-{name}.png')
        bpy.ops.render.render(write_still=True)
        print('SHOT', tag, name, flush=True)


tag = sys.argv[-1] if sys.argv[-1] in {'v6', 'v7'} else 'v7'
if tag == 'v6':
    setup(V6)
    shoot('v6')
else:
    setup(V7)
    shoot('v7')
