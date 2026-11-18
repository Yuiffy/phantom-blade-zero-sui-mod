"""Run the original Jirai recovery motions using the timed Chaos helper."""
import json
import os
from pathlib import Path

import unreal

repo = Path(__file__).resolve().parents[2]
reference = repo / 'private/jirai-skirt-shape-v1'
results = repo / 'private/jirai-perf-v1'
clips = json.loads((reference / 'pose-contract.json').read_text())['clips']
mesh = unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
library = unreal.PBZModToolsLibrary
assets = unreal.EditorAssetLibrary


def animation(profile):
    clip = clips[profile]
    factory = unreal.AnimSequenceFactory()
    factory.set_editor_property('target_skeleton', mesh.get_editor_property('skeleton'))
    seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        'Perf_' + profile.replace('-', '_'), '/Game/TransientPerf', unreal.AnimSequence, factory)
    ctrl = seq.controller
    ctrl.open_bracket('Recovery', False)
    ctrl.set_frame_rate(unreal.FrameRate(clip['fps'], 1), False)
    keys = clip['keys']
    ctrl.set_number_of_frames(unreal.FrameNumber(len(keys) - 1), False)
    for index, bone in enumerate(keys[0]):
        name = bone['name']
        ctrl.add_bone_track(name, False)
        ctrl.set_bone_track_keys(name, [unreal.Vector(*f[index]['t']) for f in keys],
                                 [unreal.Quat(*f[index]['q']) for f in keys],
                                 [unreal.Vector(*f[index]['s']) for f in keys], False)
    ctrl.close_bracket(False)
    return seq


jobs = json.loads(os.environ['JIRAI_TEST_JOBS'])
sequences = {name: animation(name) for name in dict.fromkeys(j['profile'] for j in jobs)}
for job in jobs:
    iterations, substeps = job['solver']
    assert library.set_cloth_solver(mesh, iterations, substeps) == 3
    profile, hz, steps = job['profile'], job['hz'], job['steps']
    motion = json.loads((reference / f'component-{profile}-{hz}hz.json').read_text())
    motion['frames'] = motion['frames'][:steps]
    assert len(motion['frames']) == steps
    sim = json.loads(library.test_cloth_animation(mesh, sequences[profile], steps, 1/hz, json.dumps(motion)))
    assert all(f['simulated_teleport_mode'] == 0 and len(f['assets']) == 3 for f in sim['frames'])
    assert len(sim['timings']) == steps - 60
    sim.update(job)
    (results / (job['label'] + '.json')).write_text(json.dumps(sim))
    unreal.log('JIRAI_PERF_DONE ' + job['label'])
