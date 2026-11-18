"""Continuous actual Chaos samples, using the corrected teleport consumption."""
from pathlib import Path
import unreal,json,os,hashlib
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1'
L=unreal.PBZModToolsLibrary;E=unreal.EditorAssetLibrary
stage=os.environ.get('JK_SKIRT_STAGE','baseline');out=W/stage;out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sources=[W/'selection.json',W/'pose-contract.json',W/'reference-bones.json',W/'skirt-reference-normals.json',Path(__file__),Path(__file__).parent/'author_ue.py',Path(unreal.Paths.project_dir())/'Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll']+list(W.glob('component-*.json'))
sources += [Path(__file__).parent/'coarse_ue.py',out/'selection.json',out/'render-settings.json',out/'mapping.json',W/'coarse64.json']
content=Path(unreal.Paths.project_dir())/'Plugins/HuaShira/Content/Mods/SuiPBZ'
sources += [content/'EscapeOnly/Hun_Body_Simple.uasset',content/'Physics/PA_JK_SkirtCollision1.uasset']
inputs={str(p.resolve()):sha(p) for p in sources if p.exists()}
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
skeleton=mesh.get_editor_property('skeleton');data=json.loads((W/'pose-contract.json').read_text())
(out/'cloth-details.json').write_text(L.dump_cloth_details(mesh))
for profile,clip in data['clips'].items():
 if profile not in os.environ.get('JK_PROFILES','walk,jog,crouch').split(','):continue
 folder='/HuaShira/Mods/SuiPBZ/Tests';name='JK_'+profile;path=folder+'/'+name
 if E.does_asset_exist(path):E.delete_asset(path)
 factory=unreal.AnimSequenceFactory();factory.set_editor_property('target_skeleton',skeleton)
 seq=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.AnimSequence,factory);ctrl=seq.controller
 ctrl.open_bracket('JK skirt continuous stress',False);ctrl.set_frame_rate(unreal.FrameRate(30,1),False);ctrl.set_number_of_frames(unreal.FrameNumber(480),False)
 for i,b in enumerate(clip['keys'][0]):
  ctrl.add_bone_track(b['name'],False);ctrl.set_bone_track_keys(b['name'],[unreal.Vector(*f[i]['t']) for f in clip['keys']],[unreal.Quat(*f[i]['q']) for f in clip['keys']],[unreal.Vector(*f[i]['s']) for f in clip['keys']],False)
 ctrl.close_bracket(False)
 for hz in map(int,os.environ.get('JK_HZ','30,60').split(',')):
  steps=int(os.environ.get('JK_STEPS',60+16*hz+1))
  motion=json.dumps({'frames':json.loads((W/f'component-{profile}-{hz}.json').read_text())['frames'][:steps]})
  result=L.test_cloth_animation(mesh,seq,steps,1/hz,motion);assert not result.startswith('ERROR'),result
  d=json.loads(result);assert all(f['simulated_teleport_mode']==0 for f in d['frames'])
  d.update(profile=profile,basis='continuous offline Chaos with synthetic JK joint animation',bone_names=[b['name'] for b in clip['keys'][0]])
  (out/f'{profile}-{hz}.json').write_text(json.dumps(d))
  unreal.log('JK_SKIRT_TEST_OK '+stage+' '+profile+' '+str(hz))
assert all(sha(Path(p))==h for p,h in inputs.items()),'Author/test inputs changed while solving'
(out/'input-manifest.json').write_text(json.dumps(dict(inputs=inputs,skirt_only=os.environ.get('PBZ_SKIRT_ONLY')=='1',outputs={str(p.resolve()):sha(p) for p in out.glob('*-*.json') if p.name!='input-manifest.json'}),indent=2))
