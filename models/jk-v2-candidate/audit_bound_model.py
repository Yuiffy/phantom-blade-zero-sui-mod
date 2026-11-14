import bpy,json,math
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
me=mesh.data;me.calc_loop_triangles()
bad=sum(t.area<1e-9 for t in me.loop_triangles)
assert bad==0,bad
assert len(me.uv_layers)>=1
weights=[{mesh.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in me.vertices]
assert all(row and abs(sum(row.values())-1)<1e-5 for row in weights)
assert max(map(len,weights))<=8
points=[list(v.co) for v in me.vertices]
(ROOT/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':points,'influences':weights,'bones':[b.name for b in arm.data.bones]}),encoding='utf8')
scene=bpy.context.scene;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';cam=scene.camera;light=bpy.data.objects.get('Softbox')
scene.cycles.samples=8;scene.render.resolution_x=640;scene.render.resolution_y=800
if not scene.get('review_lighting_in_cm'):
    light.location*=200;light.data.energy*=40000;light.data.size*=200
def reset():
    for p in arm.pose.bones:p.rotation_mode='QUATERNION';p.rotation_quaternion=Quaternion();p.location=(0,0,0);p.scale=(1,1,1)
    bpy.context.view_layer.update()
def rotate(name,axis,angle):
    pb=arm.pose.bones[name];basis=pb.bone.matrix_local.to_quaternion()
    pb.rotation_quaternion=basis.inverted()@Quaternion(Vector(axis),math.radians(angle))@basis
    bpy.context.view_layer.update()
def snapshot(name,pos):
    dg=bpy.context.evaluated_depsgraph_get();ev=mesh.evaluated_get(dg);data=ev.to_mesh()
    assert all(math.isfinite(x) for v in data.vertices for x in v.co)
    maxlen=max((data.vertices[e.vertices[0]].co-data.vertices[e.vertices[1]].co).length for e in data.edges)
    ev.to_mesh_clear()
    cam.location=pos;cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=255
    scene.render.filepath=str(ROOT/(name+'.png'));bpy.ops.render.render(write_still=True)
    return {'pose':name,'finite_vertices':True,'max_edge_length_cm':maxlen}
poses=[]
reset();rotate('upperarm_r',(0,1,0),65);rotate('upperarm_l',(0,1,0),-55);rotate('lowerarm_r',(1,0,0),-65)
poses.append(snapshot('audit-arms-raised',(0,-600,115)))
reset();rotate('thigh_l',(1,0,0),-55);rotate('calf_l',(1,0,0),80);rotate('thigh_r',(1,0,0),-35);rotate('calf_r',(1,0,0),65);rotate('head',(0,0,1),45)
poses.append(snapshot('audit-crouch-head-turn',(-350,-600,115)))
reset()
for side in ['l','r']:
    for finger in ['index','middle','ring','pinky']:
        for i in [1,2,3]:
            pb=arm.pose.bones[f'{finger}_{i:02d}_{side}'];pb.rotation_quaternion=Quaternion((0,0,1),math.radians(-45 if side=='r' else 45))
bpy.context.view_layer.update()
poses.append(snapshot('audit-finger-curl',(-300,-600,115)))
report={'meshes':1,'bones':len(arm.data.bones),'vertices':len(me.vertices),'triangles':len(me.loop_triangles),'degenerate_triangles':bad,'material_slots':len(me.materials),'UV_layers':len(me.uv_layers),'max_influences':max(map(len,weights)),'poses':poses,'game_animations_executed':False}
(ROOT/'model-audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
