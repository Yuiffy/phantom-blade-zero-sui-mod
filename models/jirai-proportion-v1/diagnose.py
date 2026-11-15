import bpy,json,math,bmesh
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
REPO=Path(__file__).resolve().parents[2];OUT=REPO/'private/jirai-proportion-v1/diagnostic';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(REPO/'private/jirai-v1/sui-jirai-motion.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=body.data
comp=np.array([v.value for v in m.attributes['source_component'].data]);p=np.array([v.co[:] for v in m.vertices]);weights=[{body.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
report={'components':[]}
for c in sorted(set(comp)):
 q=p[comp==c];ids=np.where(comp==c)[0]
 report['components'].append({'id':int(c),'verts':len(q),'bounds':[q.min(0).tolist(),q.max(0).tolist()],'material_slots':sorted(set(m.polygons[f].material_index for f in range(len(m.polygons)) if comp[m.polygons[f].vertices[0]]==c))})
hand=np.array([sum(v for k,v in w.items() if k.startswith(('hand_','index_','middle_','ring_','pinky_','thumb_')))>.95 for w in weights]);edges=np.array([e.vertices[:] for e in m.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1);emask=hand[edges].all(1)&(length>.015)
def reset():
 for b in arm.pose.bones:b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion();b.location=(0,0,0);b.scale=(1,1,1)
def rotate(n,axis,a):
 b=arm.data.bones[n].matrix_local.to_quaternion();arm.pose.bones[n].rotation_quaternion=b.inverted()@Quaternion(Vector(axis),math.radians(a))@b
def evaluated():
 bpy.context.view_layer.update();o=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=o.to_mesh();q=np.array([v.co[:] for v in me.vertices]);o.to_mesh_clear();return q
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=6;scene.render.resolution_x=600;scene.render.resolution_y=700;scene.view_settings.exposure=.3
# Guides are disabled only in the diagnostic copy.
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
def render(name,pos,target,scale):
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
reset();render('hand-rest',(115,-260,140),(56,-8,105),30)
for side in ['l','r']:
 for f in ['index','middle','ring','pinky']:
  for i in [1,2,3]:arm.pose.bones[f'{f}_{i:02d}_{side}'].rotation_quaternion=Quaternion((0,0,1),math.radians(35 if side=='l' else -35))
render('hand-curl',(115,-260,140),(55,-8,106),30)
reset();rotate('upperarm_l',(0,1,0),-65);rotate('upperarm_r',(0,1,0),65)
render('shoulder-raised',(-200,500,170),(0,4,155),80)
reset();rotate('thigh_l',(1,0,0),-45);rotate('calf_l',(1,0,0),70);rotate('thigh_r',(1,0,0),25);rotate('calf_r',(1,0,0),15)
render('stride-back',(0,550,126),(0,5,119),85)
(OUT/'source-components.json').write_text(json.dumps(report,indent=2))
print('DIAGNOSED')
