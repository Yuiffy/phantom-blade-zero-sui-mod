"""Build legacy Chaos cage simulations with distinct, kinematic collisions."""
from pathlib import Path
import unreal,json,math
CODE=Path(__file__).resolve().parent;R=CODE.parents[1]/'private/jirai-skirt-shape-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=R/'variant'
E=unreal.EditorAssetLibrary;L=unreal.PBZModToolsLibrary
assert Path(unreal.Paths.project_dir()).resolve()==(W/'ue/ProjectPBZ').resolve()
mesh=unreal.load_asset('/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple');assert mesh
assert L.remove_all_clothing(mesh)==0,'Run this only on a fresh import'
pa=L.create_physics_asset('/HuaShira/Mods/SuiPBZ/Physics','PA_Jirai_ClothCollision',mesh)
mod=unreal.SkeletonModifier();assert mod.set_skeletal_mesh(mesh)
# Component-space spheres, converted with the actual imported reference transforms.
# These affect cloth only; the body's native gameplay/ragdoll PA remains unchanged.
shapes=[('head',(0,-7,177),7),('neck_02',(0,-5,166.5),4),('spine_05',(0,-5,151),8),('spine_04',(0,-5,140),8),('spine_03',(0,-5,128),8),('pelvis',(0,-5,111),8),('thigh_l',(9,-5,101),5.5),('thigh_r',(-9,-5,101),5.5)]
bodies=[]
names={str(n).lower():str(n) for n in mod.get_all_bone_names()}
for bone,center,radius in shapes:
 assert bone in names,bone
 t=mod.get_bone_transform(names[bone],True);local=t.inverse_transform_location(unreal.Vector(*center))
 bodies.append({'bone':names[bone],'type':'sphere','center':[local.x,local.y,local.z],'radius':radius,'kinematic':True})
collision={'bodies':bodies,'joints':[],'disable_pairs':[]}
result=L.build_physics_asset(pa,mesh,json.dumps(collision));assert result.startswith('ok'),result
assert E.save_loaded_asset(pa)
(W/'collision-spec.json').write_text(json.dumps(collision,indent=2))
# Hair retains the exact R6 cloth-only PA; the skirt gets a separate envelope.
skirt_pa=L.create_physics_asset('/HuaShira/Mods/SuiPBZ/Physics','PA_Jirai_SkirtCollision',mesh)
skirt_bodies=[]
for bone,center,radius in [('pelvis',(0,-5,115),11)]:
 t=mod.get_bone_transform(names[bone],True);p=t.inverse_transform_location(unreal.Vector(*center));skirt_bodies.append({'bone':names[bone],'type':'sphere','center':[p.x,p.y,p.z],'radius':radius,'kinematic':True})
for bone,a,b,radius in [('thigh_l',(9.3,-5.3,111),(12.7,-5.3,82),9.2),('thigh_r',(-9.3,-5.3,111),(-12.7,-5.3,82),9.2),('thigh_l',(10.824,-5.3,98),(12.7,-5.3,82),9.5),('thigh_r',(-10.824,-5.3,98),(-12.7,-5.3,82),9.5)]:
 t=mod.get_bone_transform(names[bone],True);a=t.inverse_transform_location(unreal.Vector(*a));b=t.inverse_transform_location(unreal.Vector(*b));axis=b-a;center=(a+b)*.5;q=unreal.MathLibrary.make_rot_from_z(axis).quaternion();rot=q.rotator()
 skirt_bodies.append({'bone':names[bone],'type':'capsule','center':[center.x,center.y,center.z],'quat':[q.x,q.y,q.z,q.w],'rotation':[rot.pitch,rot.yaw,rot.roll],'radius':radius,'length':axis.length(),'kinematic':True})
skirt_collision={'bodies':skirt_bodies,'joints':[],'disable_pairs':[]}
result=L.build_physics_asset(skirt_pa,mesh,json.dumps(skirt_collision));assert result.startswith('ok'),result;assert E.save_loaded_asset(skirt_pa)
(W/'skirt-collision-spec.json').write_text(json.dumps(skirt_collision,indent=2))
spec=json.loads((R/'cloth-spec.json').read_text());results=[];asset_names={}
assert all(not row['additional_render_slots'] for row in spec),'Merge color regions into one atlas; shared section binding does not survive UE rebuild'
for row in spec:
 before={a['guid'] for a in json.loads(L.dump_cloth_details(mesh))['assets']}
 result=L.create_cloth_from_slot(mesh,row['slot'],row['name'],skirt_pa if row['slot']=='MI_Jirai_Skirt' else pa,row['max_distance'],json.dumps(row['mask']),json.dumps(row['config']))
 unreal.log(result);assert result.startswith('ok'),result;results.append(result)
 created=[a for a in json.loads(L.dump_cloth_details(mesh))['assets'] if a['guid'] not in before]
 assert len(created)==1,('expected exactly one new clothing asset',row['name'],created)
 asset_names[row['name']]=created[0]['name']
 for slot in row['additional_render_slots']:
  result=L.bind_existing_cloth_to_slot(mesh,slot,asset_names[row['name']]);unreal.log(result);assert result.startswith('ok'),result
assert L.set_cloth_solver(mesh,24,6)==len(spec)
detail=json.loads(L.dump_cloth_details(mesh));assert len(detail['assets'])==len(spec)
pending={r['slot'] for r in spec if r.get('render_pin_plane')}
# The separate render pin mask is authored after cook, because UE rebuilds
# regenerate it from the physical pin mask. Final-container reconstruction
# retains the original .3 cm / .5 cm mapping and first-tick thresholds.
assert all(s['slot'] in pending or s.get('rest_mapping_max_error_cm',0)<.3 for s in detail['sections'])
detail['pending_cooked_render_pin_slots']=sorted(pending)
assets={a['name']:a for a in detail['assets']};sections={s['slot']:s for s in detail['sections']}
for row in spec:
 a=assets[asset_names[row['name']]];maps={m['name']:m for m in a['maps']};v=maps['MaxDistance']['values']
 assert maps['MaxDistance']['enabled'] and len(v)==len(a['positions'])
 assert sum(x==0 for x in v)>=12 and max(v)<=row['max_distance']+.0001 and max(v)>0
 assert sections[row['mask']['sim_slot']]['disabled'],row
 for slot in [row['slot']]+row['additional_render_slots']:
  assert sections[slot]['cloth_guid']==a['guid'] and not sections[slot]['disabled'],slot
 config={k.casefold():v for k,v in a['config'].items()}
 def check_applied(wanted,actual,path):
  if isinstance(wanted,dict):
   actual={k.casefold():v for k,v in actual.items()}
   for key,value in wanted.items():
    assert key.casefold() in actual,('missing config',path,key)
    check_applied(value,actual[key.casefold()],path+'.'+key)
  elif isinstance(wanted,bool):assert wanted==actual,(path,wanted,actual)
  else:assert abs(float(wanted)-float(actual))<1e-5,(path,wanted,actual)
 check_applied(row['config'],a['config'],row['name'])
 assert abs(config['gravityscale']-row['config']['GravityScale'])<1e-5
 vector={k.casefold():v for k,v in config['linearvelocityscale'].items()}
 assert all(abs(vector[x]-row['config']['LinearVelocityScale'][x.upper()])<1e-5 for x in ['x','y','z'])
assert E.save_loaded_asset(mesh)
(W/'cloth-details.json').write_text(json.dumps(detail,indent=2))
(W/'cloth-authoring-report.json').write_text(json.dumps({'status':'authored-not-runtime-tested','results':results,'assets':len(spec),'simulation_particles':sum(len(a['positions']) for a in assets.values()),'body_gameplay_physics_unchanged':True},indent=2))
unreal.log('SUI_CLOTH_AUTHOR_OK')
