"""Tune the existing skirt without rebuilding other clothing or importing the face."""
from pathlib import Path
import unreal,json,runpy
W=Path(__file__).resolve().parents[2]/'private/jk-skirt-perf-v1';C=Path(__file__).resolve().parent
L=unreal.PBZModToolsLibrary;E=unreal.EditorAssetLibrary
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
selection=json.loads((W/'selection.json').read_text())
pa=L.create_physics_asset('/HuaShira/Mods/SuiPBZ/Physics','PA_JK_SkirtCollision1',mesh)
mod=unreal.SkeletonModifier();assert mod.set_skeletal_mesh(mesh)
bodies=[]
for bone,center,radius in [('pelvis',(0,-5.5,114),11)]:
 t=mod.get_bone_transform(bone,True);p=t.inverse_transform_location(unreal.Vector(*center));bodies.append({'bone':bone,'type':'sphere','center':[p.x,p.y,p.z],'radius':radius,'kinematic':True})
capsules=selection.get('capsules') or [('thigh_l',(9.3,-5.5,107),(12.7,-5.5,80),selection['radius']),('thigh_r',(-9.3,-5.5,107),(-12.7,-5.5,80),selection['radius']),('thigh_l',(10.43,-5.5,98),(12.7,-5.5,80),selection.get('lower_radius',selection['radius'])),('thigh_r',(-10.43,-5.5,98),(-12.7,-5.5,80),selection.get('lower_radius',selection['radius']))]
for bone,a,b,radius in capsules:
 t=mod.get_bone_transform(bone,True);a=t.inverse_transform_location(unreal.Vector(*a));b=t.inverse_transform_location(unreal.Vector(*b));axis=b-a;center=(a+b)*.5;q=unreal.MathLibrary.make_rot_from_z(axis).quaternion();rot=q.rotator()
 bodies.append({'bone':bone,'type':'capsule','center':[center.x,center.y,center.z],'quat':[q.x,q.y,q.z,q.w],'rotation':[rot.pitch,rot.yaw,rot.roll],'radius':radius,'length':axis.length(),'kinematic':True})
collision={'bodies':bodies,'joints':[],'disable_pairs':[]}
result=L.build_physics_asset(pa,mesh,json.dumps(collision));assert result.startswith('ok'),result;assert E.save_loaded_asset(pa)
(W/'skirt-collision-spec.json').write_text(json.dumps(collision,indent=2))
if selection.get('simulation_positions'):assert L.tune_cloth_guide(mesh,'CA_Sui_Skirt_0',json.dumps({'positions':selection['simulation_positions']}))
assert L.tune_cloth_mask(mesh,'CA_Sui_Skirt_0',selection['pin_z'],selection['full_z'],selection['max_distance'],pa)
if selection.get('simulation_reference_bone'):assert L.tune_cloth_skinning(mesh,'CA_Sui_Skirt_0',selection['simulation_reference_bone'],(W/'skirt-reference-normals.json').read_text())
if selection.get('backstop'):assert L.tune_cloth_backstop(mesh,'CA_Sui_Skirt_0',selection['backstop']['distance'],selection['backstop']['radius'],selection['backstop'].get('normal_mode',1 if selection['backstop'].get('radial',False) else 0),selection['backstop'].get('down_tilt',0.))
assert L.tune_cloth_config(mesh,'CA_Sui_Skirt_0',json.dumps(selection['config']))
if selection.get('drive_mask'):assert L.tune_cloth_drive_mask(mesh,'CA_Sui_Skirt_0',selection['drive_mask']['low_z'],selection['drive_mask']['high_z'])
assert L.set_cloth_solver(mesh,selection['iterations'],selection['substeps'])==5
assert E.save_loaded_asset(mesh)
runpy.run_path(str(C/'test_ue.py'),run_name='__main__')
