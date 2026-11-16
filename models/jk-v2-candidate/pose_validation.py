"""Compare V1/V2 under the same explicit Hun-bone poses, not game animations."""
import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parent
report_file=ROOT/'pose-comparison.json'
reports=[r for r in json.loads(report_file.read_text())['measurements'] if r['version']=='v1'] if os.environ.get('PBZ_ONLY_V2') and report_file.exists() else []
for version in (['v2'] if os.environ.get('PBZ_ONLY_V2') else ['v1','v2']):
    folder=ROOT.parent/('tripo-refine-'+version)
    bpy.ops.wm.open_mainfile(filepath=str(folder/'sui-jk-hun-bound.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
    mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    scene=bpy.context.scene;cam=scene.camera
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.resolution_x=640;scene.render.resolution_y=800
    if not scene.get('review_lighting_in_cm'):
        light=bpy.data.objects.get('Softbox');light.location*=200;light.data.energy*=40000;light.data.size*=200
    rest=np.array([v.co[:] for v in mesh.data.vertices]);edges=np.array([e.vertices[:] for e in mesh.data.edges])
    lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
    part=mesh.data.attributes.get('source_component')
    hand_ids={v.index for v in mesh.data.vertices if part and part.data[v.index].value in [4,5]}
    hand_edges=np.array([a in hand_ids and b in hand_ids for a,b in edges])
    def reset():
        for p in arm.pose.bones:p.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
    def rotate_world(name,axis,degrees):
        pb=arm.pose.bones[name];basis=pb.bone.matrix_local.to_quaternion()
        pb.rotation_mode='QUATERNION';pb.rotation_quaternion=basis.inverted()@Quaternion(Vector(axis),math.radians(degrees))@basis
        bpy.context.view_layer.update()
    def point_limb(name,child,direction):
        pb=arm.pose.bones[name];a=arm.pose.bones[child].head-pb.head
        q=a.rotation_difference(Vector(direction));m=pb.matrix.copy()
        pb.matrix=Matrix.LocRotScale(m.translation,q@m.to_quaternion(),m.to_scale())
        bpy.context.view_layer.update()
    def capture(label,position,target,scale):
        evaluated=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=evaluated.to_mesh()
        points=np.array([v.co[:] for v in data.vertices]);evaluated.to_mesh_clear()
        assert np.isfinite(points).all()
        ratios=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)/np.maximum(lengths,1e-9)
        ratio=ratios[hand_edges & (lengths>.01)]
        reports.append({'version':version,'pose':label,'hand_edge_stretch_p99':float(np.percentile(ratio,99)),
            'hand_edge_stretch_max':float(ratio.max()),'hand_edge_compression_p01':float(np.percentile(ratio,1))})
        cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(ROOT/(version+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
    reset()
    capture('hand-rest',(-125,-180,120),(-58,-8,104),42)
    # Same target skeleton and exact same posed transforms in both comparisons.
    for side,sign in [('r',-1),('l',1)]:
        point_limb('upperarm_'+side,'lowerarm_'+side,(sign*4,0,-30))
        point_limb('lowerarm_'+side,'hand_'+side,(sign*3,-5,-30))
    capture('arms-down',(0,-600,110),(0,0,110),235)
    for side in ['r','l']:
        for finger in ['index','middle','ring','pinky']:
            for i in [1,2,3]:
                pb=arm.pose.bones[f'{finger}_{i:02d}_{side}'];pb.rotation_mode='QUATERNION'
                pb.rotation_quaternion=Quaternion((0,0,1),math.radians(-45 if side=='r' else 45))
    bpy.context.view_layer.update();target=arm.pose.bones['hand_r'].head+Vector((0,0,-7))
    capture('hand-curl',target+Vector((-80,-180,25)),target,43)
    reset();rotate_world('head',(0,0,1),40)
    capture('chin-turn',(-220,-400,175),(0,0,171),65)
(ROOT/'pose-comparison.json').write_text(json.dumps({'game_animations_executed':False,'measurements':reports},indent=2),encoding='utf8')
print(json.dumps(reports))
