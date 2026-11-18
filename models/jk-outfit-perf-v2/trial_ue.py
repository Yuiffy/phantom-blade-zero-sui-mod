import json
import os
from pathlib import Path
import unreal

repo = Path(__file__).resolve().parents[2]
prior = repo / 'private/jk-skirt-perf-v1'
out = repo / 'private/jk-outfit-perf-v2'
mesh = unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple')
lib = unreal.PBZModToolsLibrary
clips = json.loads((prior/'pose-contract.json').read_text())['clips']
sequences = {}
jobs = json.loads(os.environ['JK_PERF_JOBS'])
if os.environ.get('JK_GUIDES')=='1':
    for part,slot in [('Charm','CharmAtlas'),('CardiganHem','CardiganHem'),('Backpack','Backpack')]:
        name='CA_Sui_'+part+'_0'
        assert lib.tune_cloth_guide(mesh,name,(out/'guides'/(name+'.json')).read_text())
        mapping=json.loads(lib.reproject_cloth_mapping(mesh,'MI_JK_'+slot,name,''))
        (out/'guides'/(name+'-map.json')).write_text(json.dumps(mapping))
    if os.environ.get('JK_SAVE_GUIDES')=='1':
        assert unreal.EditorAssetLibrary.save_loaded_asset(mesh)
for job in jobs:
    label, volume, simple_bend, iters, profile, hz, steps = job
    for part in ['Charm','Backpack','CardiganHem','Ponytail']:
        config = {'bUseBendingElements': not simple_bend}
        if part in ['Charm','Backpack']:
            config['bUseThinShellVolumeConstraints'] = volume
        assert lib.tune_cloth_config(mesh, 'CA_Sui_'+part+'_0', json.dumps(config))
    assert lib.set_cloth_solver(mesh,iters,3)==5
    stage=out/label
    stage.mkdir(exist_ok=True)
    if profile not in sequences:
        factory=unreal.AnimSequenceFactory()
        factory.set_editor_property('target_skeleton',mesh.get_editor_property('skeleton'))
        seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset('Perf_'+profile,'/Game/PerfTest',unreal.AnimSequence,factory)
        ctrl=seq.controller
        keys=clips[profile]['keys']
        ctrl.open_bracket('Motion',False)
        ctrl.set_frame_rate(unreal.FrameRate(30,1),False)
        ctrl.set_number_of_frames(unreal.FrameNumber(len(keys)-1),False)
        for i,b in enumerate(keys[0]):
            ctrl.add_bone_track(b['name'],False)
            ctrl.set_bone_track_keys(b['name'],[unreal.Vector(*f[i]['t']) for f in keys],[unreal.Quat(*f[i]['q']) for f in keys],[unreal.Vector(*f[i]['s']) for f in keys],False)
        ctrl.close_bracket(False)
        sequences[profile]=seq
    motion=json.loads((prior/f'component-{profile}-{hz}.json').read_text())
    motion['frames']=motion['frames'][:steps]
    result=json.loads(lib.test_cloth_animation(mesh,sequences[profile],steps,1/hz,json.dumps(motion)))
    assert all(f['simulated_teleport_mode']==0 and len(f['assets'])==5 for f in result['frames'])
    result.update(profile=profile,bone_names=[b['name'] for b in clips[profile]['keys'][0]])
    (stage/f'{profile}-{hz}.json').write_text(json.dumps(result))
    (stage/'cloth-details.json').write_text(lib.dump_cloth_details(mesh))
    unreal.log('JK_TRIAL_OK '+label+' '+profile+' '+str(hz))
