import bpy,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
ROOT=Path(__file__).resolve().parent
reports=[]
def configure(version):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/('tripo-refine-'+version)/'sui-jk-hun-bound.blend'))
    scene=bpy.context.scene
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.resolution_x=720;scene.render.resolution_y=720
    return scene,next(o for o in scene.objects if o.type=='ARMATURE'),next(o for o in scene.objects if o.type=='MESH')
def aim(arm,side,target,pole):
    upper=arm.pose.bones['upperarm_'+side];lower=arm.pose.bones['lowerarm_'+side];hand=arm.pose.bones['hand_'+side]
    s=upper.head.copy();e=lower.head.copy();w=hand.head.copy();l1=(e-s).length;l2=(w-e).length
    v=Vector(target)-s;d=min(v.length,l1+l2-.1);u=v.normalized();along=(l1*l1-l2*l2+d*d)/(2*d)
    perp=Vector(pole)-s;perp-=u*perp.dot(u);perp.normalize()
    elbow=s+u*along+perp*math.sqrt(max(0,l1*l1-along*along));wrist=s+u*d
    q=(e-s).rotation_difference(elbow-s)
    upper.matrix=Matrix.Translation(s)@q.to_matrix().to_4x4()@Matrix.Translation(-s)@upper.matrix
    bpy.context.view_layer.update()
    e=lower.head.copy();w=hand.head.copy();q=(w-e).rotation_difference(wrist-e)
    lower.matrix=Matrix.Translation(e)@q.to_matrix().to_4x4()@Matrix.Translation(-e)@lower.matrix
    bpy.context.view_layer.update()
def render(scene,mesh,version,label,pos,target,scale):
    cam=scene.camera;cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh()
    assert all(math.isfinite(c) for v in data.vertices for c in v.co);ev.to_mesh_clear()
    scene.render.filepath=str(ROOT/f'{version}-{label}.png');bpy.ops.render.render(write_still=True)
    reports.append({'version':version,'pose':label,'finite_geometry':True})
for version in ['v2','v6']:
    scene,arm,mesh=configure(version)
    for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    render(scene,mesh,version,'neck-front',(0,-600,169),(0,0,169),92)
    aim(arm,'r',(-8,-35,139),(-65,-12,139));aim(arm,'l',(10,-29,143),(65,-8,139))
    render(scene,mesh,version,'weapon-guard',(0,-600,154),(0,0,154),130)
for version in ['v5','v6']:
    scene,arm,mesh=configure(version)
    for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    render(scene,mesh,version,'backpack',(0,600,137),(-5,0,137),125)
(ROOT/'shoulder-bag-review.json').write_text(json.dumps({'game_animations_executed':False,'poses_are_manual_diagnostics':True,'checks':reports},indent=2),encoding='utf8')
