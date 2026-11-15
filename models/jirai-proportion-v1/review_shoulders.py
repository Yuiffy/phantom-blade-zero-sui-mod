"""Render actual shoulder/elbow/wrist projections and measure posed arm edges."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'))
body=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=body.data
bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
scene=bpy.context.scene;cam=scene.camera;scene.cycles.samples=12;scene.render.resolution_x=900;scene.render.resolution_y=900;scene.view_settings.exposure=.4
cam.location=(0,-650,153);cam.rotation_euler=(Vector((0,0,153))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=135
comp=np.array([d.value for d in m.attributes['source_component'].data]);p=np.array([v.co[:] for v in m.vertices]);edges=np.array([e.vertices[:] for e in m.edges]);length=np.linalg.norm(p[edges[:,0]]-p[edges[:,1]],axis=1)
mask=(np.isin(comp,[0,1,23,24,25,49,50]))&(np.abs(p[:,0])>9)&(p[:,2]>128)&(p[:,2]<166)
emask=mask[edges[:,0]]&mask[edges[:,1]]&(length>.05)
markers=[]
def material(name,color):
 mat=bpy.data.materials.new(name);mat.diffuse_color=(*color,1);mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(*color,1);e.inputs[1].default_value=1;out=n.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],out.inputs[0]);return mat
cyan=material('Actual_joint_projection',(.02,.8,1));white=material('Diagram_labels',(.95,.95,.95))
def tube(a,b,r=.19):
 a=Vector(a);b=Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=v.to_track_quat('Z','Y').to_euler();o.data.materials.append(cyan);markers.append(o)
def label(text,pos,size=2.):
 cu=bpy.data.curves.new('label','FONT');cu.body=text;cu.size=size;ob=bpy.data.objects.new(text,cu);scene.collection.objects.link(ob);ob.location=pos;ob.rotation_euler=(math.pi/2,0,0);cu.materials.append(white);markers.append(ob)
def reset():
 for bone in arm.pose.bones:bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion();bone.location=(0,0,0);bone.scale=(1,1,1)
def rotate(n,angle):
 b=arm.data.bones[n].matrix_local.to_quaternion();arm.pose.bones[n].rotation_quaternion=b.inverted()@Quaternion((0,1,0),math.radians(angle))@b
report=[]
for angle in [0,30,60,90]:
 reset();rotate('upperarm_l',-angle);rotate('upperarm_r',angle);bpy.context.view_layer.update()
 evaluated=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=evaluated.to_mesh();posed=np.array([v.co[:] for v in me.vertices]);ratio=np.linalg.norm(posed[edges[:,0]]-posed[edges[:,1]],axis=1)/np.maximum(length,1e-8);evaluated.to_mesh_clear()
 joints=[arm.matrix_world@arm.pose.bones[n+'_l'].head for n in ['upperarm','lowerarm','hand']]
 for j,point in enumerate(joints):
  point=Vector((point.x,-62,point.z));bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.85,location=point);ob=bpy.context.object;ob.data.materials.append(cyan);markers.append(ob)
  label(['Shoulder','Elbow','Wrist'][j],point+Vector((1.4,-1,1.4)),1.65)
 for a,b in zip(joints,joints[1:]):tube((a.x,-62,a.z),(b.x,-62,b.z))
 label(f'R3 | arm raise {angle} deg',(-62,-64,215),2.9)
 label('Cyan = actual joint projections',(-62,-64,210),2.0)
 label('Shoulder moved; elbow/wrist rest positions retained',(-62,-64,205),1.7)
 scene.render.filepath=str(ROOT/f'shoulder-r3-{angle:02d}.png');bpy.ops.render.render(write_still=True)
 report.append({'raise_degrees':angle,'shoulder_blender_cm':list(joints[0]),'elbow_blender_cm':list(joints[1]),'shoulder_edge_count':int(emask.sum()),'edge_ratio_p99':float(np.percentile(ratio[emask],99)),'edges_over_1_6':int(np.sum(ratio[emask]>1.6)),'max_ratio':float(ratio[emask].max()),'manual_pose_only':True})
 for ob in markers:bpy.data.objects.remove(ob,do_unlink=True)
 markers.clear()
reset();cam.data.ortho_scale=247;cam.location=(0,-650,115);cam.rotation_euler=(Vector((0,0,110))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=900;scene.render.resolution_y=1200;scene.render.filepath=str(ROOT/'shoulder-r3-full.png');bpy.ops.render.render(write_still=True)
(ROOT/'shoulder-r3-audit.json').write_text(json.dumps(report,indent=2));print('SHOULDER_R3_REVIEW_OK',json.dumps(report),flush=True)
