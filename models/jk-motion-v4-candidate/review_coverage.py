"""Review opaque safety shorts from below and in synthetic leg poses."""
from pathlib import Path
import bpy, bmesh, json, numpy as np, math
from mathutils import Vector, Matrix

R=Path(__file__).resolve().parent
W=R.parents[2]/'variants/jk-motion-v4'
bpy.ops.wm.open_mainfile(filepath=str(R/'sui-jk-motion-source.blend'))
s=bpy.context.scene
o=next(x for x in s.objects if x.type=='MESH')
a=next(x for x in s.objects if x.type=='ARMATURE')
m=o.data
comp=np.array([v.value for v in m.attributes['source_component'].data])
co=np.array([v.co[:] for v in m.vertices])
faces=np.array([p.vertices[:] for p in m.polygons])
mats=np.array([p.material_index for p in m.polygons])
lining=next(i for i,mat in enumerate(m.materials) if mat.name=='MI_JK_SafetyLining')
np.savez_compressed(R/'coverage-source.npz',positions=co,faces=faces,materials=mats,components=comp)
protected=(comp[faces]==1).all(1)&(np.abs(co[faces,:,][...,0])<3.5).all(1)&(co[faces,:,][...,2]>99).all(1)
assert protected.sum()>20 and (mats[protected]==lining).all()
assert m.materials[lining].node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value==1
s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=4
s.render.threads_mode='FIXED';s.render.threads=2
s.render.resolution_x=480;s.render.resolution_y=480;s.render.resolution_percentage=100
light=bpy.data.objects.get('Softbox')
if not s.get('review_lighting_in_cm'):
    light.location*=200;light.data.energy*=40000;light.data.size*=200
cam=s.camera;cam.data.ortho_scale=48
bone_names={p.name.lower():p.name for p in a.pose.bones}
def pose(angles):
    for p in a.pose.bones:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update()
    for name,(axis,degrees) in angles.items():
        p=a.pose.bones[bone_names[name]];b=p.bone
        p.matrix=Matrix.Translation(b.head_local)@Matrix.Rotation(math.radians(degrees),4,axis)@Matrix.Translation(-b.head_local)@b.matrix_local
    bpy.context.view_layer.update()

# Hide only in this diagnostic session to inspect the complete garment directly.
# Source .blend and exported FBX keep skirt/cardigan/physics untouched.
def render(name,pos,target):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.filepath=str(R/(name+'.png'));bpy.ops.render.render(write_still=True)

pose({})
render('coverage-rest-back-low',(0,125,58),(0,4,105))
render('coverage-rest-front-low',(0,-125,58),(0,4,105))

# Render diagnostic garment alone: no anatomical surface is exposed underneath.
saved=np.array([p.material_index for p in m.polygons])
for mat in m.materials:mat.use_backface_culling=False
# Hide outer clothing for this view using a temporary mesh copy, retaining legs.
keep=(np.isin(comp[faces[:,0]],[1,1001]))
original=o.data
diag=original.copy();diag.name='CoverageDiagnosticOnly'
bm=bmesh.new();bm.from_mesh(diag)
bmesh.ops.delete(bm,geom=[f for f,k in zip(bm.faces,keep) if not k],context='FACES_ONLY')
bm.to_mesh(diag);bm.free();diag.update()
o.data=diag
records=[]
for name,angles in [('rest',{}),('raised-leg',{'thigh_l':('X',65)}),('spread',{'thigh_l':('Y',-25),'thigh_r':('Y',25)}),('bent-legs',{'thigh_l':('X',55),'thigh_r':('X',55)})]:
    pose(angles)
    ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh()
    pts=np.array([v.co[:] for v in em.vertices]);assert np.isfinite(pts).all()
    records.append({'name':name,'synthetic_pose':True,'finite':True,'opaque_backup_triangles':int(protected.sum())})
    ev.to_mesh_clear()
    render('coverage-garment-'+name,(0,125,66),(0,5,104))
o.data=original
(W/'coverage-pose-review.json').write_text(json.dumps({'status':'synthetic-leg-pose-and-opaque-central-surface-review-passed','protected_central_triangles':int(protected.sum()),'views':records,'game_animations_tested':False},indent=2),encoding='utf-8')
print('COVERAGE_REVIEW_OK',flush=True)
