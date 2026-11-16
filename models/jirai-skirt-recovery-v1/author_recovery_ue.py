"""Save only a selected, evaluated parameter change on the unchanged R7 mesh."""
from pathlib import Path
import unreal,json,hashlib,runpy,os
C=Path(__file__).resolve().parent;W=C.parents[1]/'private/jirai-skirt-recovery-v1';V=W/'variant'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
selection=read(W/'selection.json');evaluation=read(V/'sweep/recovery-evaluation.json')
rows=[r for r in evaluation['records'] if r['preset']==selection['preset']]
assert len(rows)==6 and all(r['passed'] for r in rows),'Selected config did not pass both rates and all three recovery clips'
assert selection['evaluation_sha256']==sha(V/'sweep/recovery-evaluation.json')
spec=read(W/'cloth-spec.json');row=next(r for r in spec if r['slot']=='MI_Jirai_Skirt')
assert row['config']==read(V/'sweep'/(selection['preset']+'-config.json'))
assert row['render_pin_plane']['max_simulated_blend']==evaluation['predicted_quantized_render_blend_cap']==selection['max_simulated_blend']
assert Path(unreal.Paths.project_dir()).resolve()==(V/'ue/ProjectPBZ').resolve()
L=unreal.PBZModToolsLibrary;E=unreal.EditorAssetLibrary
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');before=read(V/'cloth-details.json')
asset=next(a for a in before['assets'] if a['name'].startswith('CA_Jirai_Skirt'))
assert L.tune_cloth_config(mesh,asset['name'],json.dumps(row['config']))
collision=read(V/'skirt-collision-spec.json')
assert sha(V/'skirt-collision-spec.json')==selection['collision_spec_sha256']
pa=unreal.load_asset('/HuaShira/Mods/SuiPBZ/Physics/PA_Jirai_SkirtCollision')
assert L.build_physics_asset(pa,mesh,json.dumps(collision)).startswith('ok')
assert E.save_loaded_asset(pa)
after=json.loads(L.dump_cloth_details(mesh))
for old,new in zip(before['assets'],after['assets']):
 assert {k:v for k,v in old.items() if k!='config'}=={k:v for k,v in new.items() if k!='config'}
 if not old['name'].startswith('CA_Jirai_Skirt'):assert old==new,'Hair cloth changed'
assert E.save_loaded_asset(mesh)
(V/'cloth-details.json').write_text(json.dumps(after,indent=2))
assert sha(V/'ue/ProjectPBZ/Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll')==read(W/'editor-tools-build.json')['dll_sha256']
os.environ['PBZ_REUSE_RECOVERY_SWEEP']='1'
for script in ['test_cloth_ue.py','test_articulation_ue.py']:
 runpy.run_path(str(C/script),run_name='__main__')
inputs=[W/'Sui_Jirai_Hun_Body.fbx',W/'cloth-spec.json',W/'pose-contract.json',W/'source-render-contract.json',W/'selection.json',V/'skirt-collision-spec.json',V/'ue/ProjectPBZ/Plugins/PBZModTools/Binaries/Win64/UnrealEditor-PBZModTools.dll']+[C/n for n in ['author_recovery_ue.py','test_cloth_ue.py','test_articulation_ue.py']]+list(W.glob('component-*.json'))+[V/'sweep'/f"{selection['preset']}-{n}-{hz}hz.json" for n in ['walk-recover','jog-recover','crouch-recover'] for hz in [30,60]]
outputs=[V/('simulation-'+n+'.json') for n in ['60hz','30hz','foreaft']]+[V/('articulation-'+n+'.json') for n in read(W/'pose-contract.json')['clips']]+[V/f'articulation-{n}-60hz.json' for n in ['walk-recover','jog-recover','crouch-recover']]
(V/'combined-tests.json').write_text(json.dumps({'inputs':{str(p):sha(p) for p in inputs},'outputs':{str(p):sha(p) for p in outputs}},indent=2))
unreal.log('RECOVERY_PARAMETERS_SAVED_AND_TESTED')
