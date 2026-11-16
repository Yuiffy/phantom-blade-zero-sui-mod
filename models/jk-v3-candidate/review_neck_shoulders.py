import bpy,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parent
records=[]
versions=['v3'] if os.environ.get('PBZ_ONLY_V3') else ['v2','v3']
for version in versions:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/('tripo-refine-'+version)/'sui-jk-hun-bound.blend'))
    arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH')
    scene=bpy.context.scene;cam=scene.camera
    scene.render.threads_mode='FIXED';scene.render.threads=2;scene.cycles.device='CPU';scene.cycles.samples=8
    scene.render.resolution_x=720;scene.render.resolution_y=720
    if not scene.get('review_lighting_in_cm'):
        light=bpy.data.objects.get('Softbox');light.location*=200;light.data.energy*=40000;light.data.size*=200
    rest=np.array([v.co[:] for v in mesh.data.vertices]);edges=np.array([e.vertices[:] for e in mesh.data.edges])
    lengths=np.linalg.norm(rest[edges[:,0]]-rest[edges[:,1]],axis=1)
    mask=(rest[:,2]>151)&(rest[:,2]<178)&(np.abs(rest[:,0])<30)
    used=mask[edges[:,0]]&mask[edges[:,1]]&(lengths>.05)
    def reset():
        for pb in arm.pose.bones:pb.matrix_basis=Matrix.Identity(4)
        bpy.context.view_layer.update()
    def rotate(name,axis,angle):
        pb=arm.pose.bones[name];q=pb.bone.matrix_local.to_quaternion();pb.rotation_mode='QUATERNION'
        pb.rotation_quaternion=q.inverted()@Quaternion(Vector(axis),math.radians(angle))@q
        bpy.context.view_layer.update()
    def render(label,pos,target,scale):
        ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh();points=np.array([v.co[:] for v in data.vertices]);ev.to_mesh_clear()
        assert np.isfinite(points).all()
        ratios=np.linalg.norm(points[edges[:,0]]-points[edges[:,1]],axis=1)/np.maximum(lengths,1e-9)
        records.append({'version':version,'pose':label,'upper_edge_ratio_p99':float(np.percentile(ratios[used],99)),
            'upper_edge_ratio_max':float(ratios[used].max()),'upper_edge_ratio_p01':float(np.percentile(ratios[used],1))})
        cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(ROOT/(version+'-'+label+'.png'));bpy.ops.render.render(write_still=True)
    reset();render('neck-front',(0,-600,169),(0,0,169),92)
    rotate('head',(0,0,1),40);render('neck-turn',(-220,-400,171),(0,0,169),85)
    reset();rotate('upperarm_r',(0,1,0),65);rotate('upperarm_l',(0,1,0),-55);rotate('lowerarm_r',(1,0,0),-65)
    render('shoulders-raised',(0,-600,153),(0,0,153),145)
report=ROOT/'upper-pose-comparison.json'
if os.environ.get('PBZ_ONLY_V3') and report.exists():records=[r for r in json.loads(report.read_text())['measurements'] if r['version']=='v2']+records
report.write_text(json.dumps({'game_animations_executed':False,'measurements':records},indent=2),encoding='utf8')
print(json.dumps(records))
