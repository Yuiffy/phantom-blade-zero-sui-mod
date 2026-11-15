"""Five cloth guides; cotton ornaments retain one coherent padded render section."""
import bpy,json,math,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jirai-final.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');arm=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
m.calc_loop_triangles();BASE_TRIANGLES=len(m.loop_triangles)
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]==4096:
  im.unpack(method='REMOVE') if im.packed_file else None;im.filepath=str(ROOT/'textures/jirai-albedo.png');im.reload();im.pack()
indices={mat.name:i for i,mat in enumerate(m.materials)}
spec=[s for s in json.loads((ROOT/'game-materials.json').read_text()) if s['slot'] in indices]
assert len(m.materials)==12
# A rerun reads the previous motion material manifest, where the two static
# wing colors have already been replaced. Restore their source-only records.
for mat in m.materials:
 if not any(s['slot']==mat.name for s in spec):
  assert mat.name in ['MI_Jirai_WingWhite','MI_Jirai_WingPink'],mat.name
  bs=mat.node_tree.nodes.get('Principled BSDF');spec.append({'slot':mat.name,'source_texture':False,'base_color_linear':list(bs.inputs['Base Color'].default_value),'roughness':bs.inputs['Roughness'].default_value,'metallic':bs.inputs['Metallic'].default_value})
assert len(spec)==12
comp=np.array([d.value for d in m.attributes['source_component'].data]);points=np.array([v.co[:] for v in m.vertices])
# Taper the high waistband under the raised corset; retain the shorts' lower
# clearance and thigh support. A straight two-tube top protrudes at a slim waist.
for vertex in m.vertices:
 if comp[vertex.index]!=920:continue
 p=vertex.co;side=1 if p.x>=0 else -1;t=max(0,min(1,(p.z-125)/7))
 if t:
  p.x=side*(9-4*t)+(p.x-side*9)*(1-t/3);p.y=5.5+(p.y-5.5)*(1-t/6)
points=np.array([v.co[:] for v in m.vertices])
for name,parts in [('TailL',[4,16,31]),('TailR',[3,17,30])]:
 mat=m.materials[indices['MI_Jirai_Hair']].copy();mat.name='MI_Jirai_'+name;m.materials.append(mat);new=len(m.materials)-1
 for f in m.polygons:
  if comp[f.vertices[0]] in parts:f.material_index=new
 row=dict(next(s for s in spec if s['slot']=='MI_Jirai_Hair'));row['slot']=mat.name;spec.append(row)
# Seat the raised ribbon strips on the actual cotton surface. The original
# analytic dome approximation left strips floating and produced ~0.49 cm cloth
# projection error on curved patches. Retain a small, real 0.08 cm stand-off.
for side in [1,-1]:
 ids=np.where((comp==910)&(points[:,0]*side>0))[0];lookup={int(v):i for i,v in enumerate(ids)}
 tris=[tuple(lookup[int(v)] for v in t.vertices) for t in m.loop_triangles if all(int(v) in lookup for v in t.vertices)]
 tree=BVHTree.FromPolygons([Vector(p) for p in points[ids]],tris,all_triangles=True)
 for i in np.where((comp==911)&(points[:,0]*side>0))[0]:
  p=m.vertices[int(i)].co;base=22+(abs(p.x)-9)*.1;sign=1 if p.y>=base else -1
  hit,normal,face,distance=tree.ray_cast(Vector((p.x,base+sign*10,p.z)),Vector((0,-sign,0)),20)
  assert hit is not None,('ribbon outside cotton silhouette',i)
  p.y=hit.y+sign*.08
points=np.array([v.co[:] for v in m.vertices])
# White padding and its pink strips must be in the SAME render section. UE's
# rebuild discards manually attached secondary sections for the same cloth LOD.
# Two constant UV swatches preserve their exact colors without rebaking geometry.
def srgb(v):return 12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055
atlas=bpy.data.images.new('CottonWing_white_and_pink',width=64,height=32,alpha=True)
rgba=np.ones((32,64,4),dtype=np.float32)
rgba[:,:32,:3]=[srgb(v) for v in (.83,.81,.86)]
rgba[:,32:,:3]=[srgb(v) for v in (.56,.15,.30)]
atlas.pixels.foreach_set(rgba.ravel());atlas.filepath_raw=str(ROOT/'textures/wing-atlas.png');atlas.file_format='PNG';atlas.save();atlas.pack()
for side,label in [(1,'L'),(-1,'R')]:
 mat=bpy.data.materials.new('MI_Jirai_Wing'+label);mat.use_nodes=True
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.7
 tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=atlas;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
 m.materials.append(mat);slot=len(m.materials)-1
 for f in m.polygons:
  v=f.vertices[0]
  if comp[v] in [910,911] and points[v,0]*side>0:
   f.material_index=slot
   for li in f.loop_indices:m.uv_layers.active.data[li].uv=(.25 if comp[v]==910 else .75,.5)
 spec.append({'slot':mat.name,'source_texture':False,'albedo_path':str(ROOT/'textures/wing-atlas.png'),'two_color_arm':True,'base_color_linear':[1,1,1,1],'roughness':.7,'metallic':0})
# Compact unused white/pink slots without changing any other face assignment.
for i in reversed(range(len(m.materials))):
 if m.materials[i].name in ['MI_Jirai_WingWhite','MI_Jirai_WingPink']:m.materials.pop(index=i)
spec=[s for s in spec if s['slot'] not in ['MI_Jirai_WingWhite','MI_Jirai_WingPink']]
objects=[o];cages=[]
# The old sleeve liner masked a displaced humerus pivot and has been removed.
def guide(name,verts,faces,weights):
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.parent=arm;ob.modifiers.new('Hun','ARMATURE').object=arm
 mat=bpy.data.materials.new(name);mat.use_nodes=True;me.materials.append(mat);uv=me.uv_layers.new(name='UVMap')
 for p in me.polygons:
  for li,val in zip(p.loop_indices,[(0,0),(1,0),(0,1)]):uv.data[li].uv=val
 me.attributes.new('source_component','INT','POINT').data.foreach_set('value',[2000+len(cages)]*len(verts));me.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(verts))
 for n in sorted({n for w in weights for n in w}):
  g=ob.vertex_groups.new(name=n)
  for i,w in enumerate(weights):
   if n in w:g.add([i],w[n],'REPLACE')
 objects.append(ob);cages.append({'slot':name,'vertices':len(verts),'triangles':len(faces)})
for side,parts,label in [(1,[4,16,31],'L'),(-1,[3,17,30],'R')]:
 q=points[np.isin(comp,parts)];lo=q.min(0);hi=q.max(0);x=float(np.median(q[:,0]));vs=[];fs=[];cols=7;rows=26
 for z in np.linspace(hi[2]+.4,lo[2]-.4,rows):
  for y in np.linspace(lo[1]-.4,hi[1]+.4,cols):vs.append((x,y,z))
 for j in range(rows-1):
  for i in range(cols-1):a=j*cols+i;b=a+cols;fs.extend([(a,a+1,b+1),(a,b+1,b)])
 guide('MI_Jirai_Tail'+label+'Sim',vs,fs,[{'head':1.} for v in vs])

# Elliptical guide shares the garment's cross sections, including the lower lace.
q=points[comp==2];zlo=q[:,2].min()-.2;zhi=q[:,2].max()+.2;vs=[];fs=[];ww=[];sides=72;rows=25;cy=5.0
for z in np.linspace(zhi,zlo,rows):
 near=q[np.abs(q[:,2]-z)<2.5]
 if not len(near):near=q[np.argsort(np.abs(q[:,2]-z))[:30]]
 rx=max(abs(near[:,0]).max(),12.);ry=max(abs(near[:,1]-cy).max(),8.)
 for i in range(sides):
  t=i*2*math.pi/sides;x=rx*math.cos(t);y=cy+ry*math.sin(t);vs.append((x,y,z));follow=.58*max(0,min(1,(129-z)/30));left=max(0,min(1,(x+7)/14));ww.append({'pelvis':1-follow,'thigh_l':follow*left,'thigh_r':follow*(1-left)})
for j in range(rows-1):
 for i in range(sides):k=(i+1)%sides;a=j*sides;b=a+sides;fs.extend([(a+i,a+k,b+k),(a+i,b+k,b+i)])
guide('MI_Jirai_SkirtSim',vs,fs,ww)
# Follow the actual padded surface. A horizontal plate had perfect zero-time
# projection, but its changing normals compressed some tall offset render edges
# down to 5% during motion; particle-only shape checks did not catch that.
# This dense, closed cotton surface avoids long normal-offset extrapolation.
for side,label in [(1,'L'),(-1,'R')]:
 ids=np.where((comp==910)&(points[:,0]*side>0))[0];lookup={int(v):i for i,v in enumerate(ids)}
 vs=points[ids].tolist();fs=[tuple(lookup[int(v)] for v in t.vertices) for t in m.loop_triangles if all(int(v) in lookup for v in t.vertices)]
 assert len(vs)==522 and len(fs)==910,(label,len(vs),len(fs))
 guide('MI_Jirai_Wing'+label+'Sim',vs,fs,[{'spine_05':1.} for v in vs])
bpy.ops.object.select_all(action='DESELECT')
for ob in objects:ob.select_set(True)
bpy.context.view_layer.objects.active=o;bpy.ops.object.join();m=o.data;m.calc_loop_triangles()
weights=[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in m.vertices]
(ROOT/'source-render-contract.json').write_text(json.dumps({'positions_blender_cm':[list(v.co) for v in m.vertices],'influences':weights,'bones':[b.name for b in arm.data.bones]}))
(ROOT/'game-materials.json').write_text(json.dumps(spec,indent=2))
report=json.loads((ROOT/'binding-report.json').read_text());report.update(vertices=len(m.vertices),visible_triangles=BASE_TRIANGLES,triangles=len(m.loop_triangles),render_material_slots=len(m.materials),material_slots=len(spec),new_physics=True,simulation_cages=cages)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);arm.select_set(True);bpy.context.view_layer.objects.active=arm
fbx=ROOT/'Sui_Jirai_Hun_Body.fbx';bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report['fbx_sha256']=hashlib.sha256(fbx.read_bytes()).hexdigest();(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2))
def cloth(slot,fixed,d1,maximum,gravity,drive):
 return {'slot':'MI_Jirai_'+slot,'name':'CA_Jirai_'+slot,'max_distance':maximum,'mask':{'type':'plane','anchors':[[0,0,fixed]],'dir':[0,0,-1],'d0':0,'d1':d1,'sim_slot':'MI_Jirai_'+slot+'Sim'},'additional_render_slots':[],'config':{'EdgeStiffnessWeighted':{'Low':1,'High':1},'AreaStiffnessWeighted':{'Low':1,'High':1},'BendingStiffnessWeighted':{'Low':.9,'High':.9},'bUseBendingElements':True,'bUseGeodesicDistance':True,'TetherStiffness':{'Low':1,'High':1},'TetherScale':{'Low':1,'High':1},'AnimDriveStiffness':{'Low':drive,'High':drive},'AnimDriveDamping':{'Low':.6,'High':.6},'GravityScale':gravity,'DampingCoefficient':.1,'LocalDampingCoefficient':.25,'CollisionThickness':.2,'FrictionCoefficient':.4,'bUseSelfCollisions':False,'LinearVelocityScale':{'X':.6,'Y':.6,'Z':.6},'AngularVelocityScale':.5}}
configs=[cloth('TailL',189,42,9,.6,.07),cloth('TailR',189,42,9,.6,.07),cloth('Skirt',121,33,2.2,.22,.2)]
for side,label in [(1,'L'),(-1,'R')]:
 row=cloth('Wing'+label,0,27,2.4,.06,.08)
 row['mask'].update(anchors=[[side*12,0,0]],dir=[side,0,0])
 row['config'].update(BendingStiffnessWeighted={'Low':1.,'High':1.},DampingCoefficient=.12,LocalDampingCoefficient=.35)
 configs.append(row)
(ROOT/'cloth-spec.json').write_text(json.dumps(configs,indent=2));print('JIRAI_MOTION_SOURCE_OK',json.dumps(report),flush=True)
