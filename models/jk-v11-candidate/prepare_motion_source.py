"""Author low-resolution physics cages in a separate, unbuilt experiment.

This does not modify the reviewed static v11 source or any installed MOD.
"""
import bpy,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parent;OUT=ROOT.parent/'tripo-motion-v1';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT.parent/'tripo-refine-v10'));from v7_helpers import write_weights
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');old=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
vertices=[v.co[:] for v in old.vertices];faces=[p.vertices[:] for p in old.polygons];uv=[d.uv[:] for d in old.uv_layers.active.data];mats=[p.material_index for p in old.polygons];normal=[d.vector[:] for d in old.corner_normals]
W=[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in old.vertices];components=[d.value for d in old.attributes['source_component'].data];ids=[d.value for d in old.attributes['v10_vertex_index'].data];v8ids=[d.value for d in old.attributes['v8_vertex_index'].data];rest=[d.vector[:] for d in old.attributes['source_rest_position'].data];materials=list(old.materials);origco=np.array(vertices);comp=np.array(components);reports=[]
def cage(name,component,rings,source,weights=None,closed=True):
 off=len(vertices);sides=12;v=[];f=[]
 for x,y,z,rx,ry in rings:
  for i in range(sides):t=i*2*math.pi/sides;v.append((x+rx*math.cos(t),y+ry*math.sin(t),z))
 for j in range(len(rings)-1):
  for i in range(sides):k=(i+1)%sides;b=j*sides;n=b+sides;f.extend([(b+i,b+k,n+k),(b+i,n+k,n+i)])
 if closed:
  v.extend([tuple(rings[0][:3]),tuple(rings[-1][:3])]);top=len(v)-2;bottom=top+1
  for i in range(sides):k=(i+1)%sides;f.extend([(top,k,i),(bottom,(len(rings)-1)*sides+i,(len(rings)-1)*sides+k)])
 material=bpy.data.materials.new(name);material.use_nodes=True;bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.1,.6,.9,1);bs.inputs['Alpha'].default_value=0;material.surface_render_method='DITHERED';materials.append(material);mi=len(materials)-1
 src=np.flatnonzero(source);tree=KDTree(len(src))
 for i in src:tree.insert(Vector(origco[i]),int(i))
 tree.balance();wc=[]
 for p in v:
  if weights is not None:row=dict(weights)
  else:
   row={}
   for _,i,d in tree.find_n(Vector(p),4):
    for bone,w in W[i].items():row[bone]=row.get(bone,0)+w/max(d,.05)**2
   row=dict(sorted(row.items(),key=lambda p:-p[1])[:8]);s=sum(row.values());row={k:v/s for k,v in row.items()}
  wc.append(row)
 vertices.extend(v);W.extend(wc);components.extend([component]*len(v));ids.extend([-1]*len(v));v8ids.extend([-1]*len(v));rest.extend([(0,0,0)]*len(v))
 for face in f:faces.append(tuple(off+i for i in face));mats.append(mi);uv.extend([(0,0),(1,0),(0,1)]);normal.extend([(0,0,0)]*3)
 reports.append({'slot':name,'component':component,'vertices':len(v),'triangles':len(f),'render_section_must_be_removed_in_UE':True})
 return name
# The ponytail uses one continuous closed tube, even where the high-resolution
# strand geometry is disconnected. Max-distance roots will be fixed at z>=188.
rings=[]
for z in [191.4,189,186,182,178,174,170,166,162,158,154,150,148.5]:
 q=origco[np.isin(comp,[2,22])&(abs(origco[:,2]-z)<2.8)]
 if not len(q):continue
 lo=q.min(axis=0);hi=q.max(axis=0);center=(lo+hi)/2;rings.append((center[0],center[1],z,max(.7,(hi[0]-lo[0])/2+.2),max(.6,(hi[1]-lo[1])/2+.2)))
cage('MI_JK_PonytailSim',2001,rings,np.isin(comp,[2,22]),{'head':1.})
data=json.loads((ROOT/'binding-report.json').read_text());ax,ay,az=data['strap_anchor_cm'];hang=data['attachment_weights']
cage('MI_JK_CharmSim',2002,[(ax,ay-.16,143.6,.5,.28),(-12.55,-5.25,142.3,.6,.35),(-12.55,-5.5,140.4,1.2,.65),(-12.55,-6.0,138.5,3.25,1.2),(-12.55,-6.0,136.8,3.50,1.4),(-12.55,-6.05,135.0,3.30,1.15),(-12.55,-6.15,133.8,4.15,1.1),(-12.55,-6.15,132.0,1.95,1.0),(-12.55,-6.15,130.0,.8,.55)],comp==101,hang)
cage('MI_JK_SkirtSim',2003,[(0,5,113,19,10.5),(0,5,107,20.5,11.7),(0,5,101,23.3,13.6),(0,5,96,25.2,14.5),(0,5,92.5,26,14.8)],comp==10,closed=False)
cage('MI_JK_CardiganHemSim',2004,[(0,6,124,22,14.6),(0,6,118,22.8,14.9),(0,6,112,23.4,15.1),(0,6,107,24.4,15.6),(0,6,102.4,25.5,16)],(comp==0)&(origco[:,2]<126)&(abs(origco[:,0])<30),closed=False)
cage('MI_JK_BackpackSim',2005,[(-15.3,22.5,155,10,5.5),(-15.3,22.5,151,17.3,9),(-15.3,22.5,141,19.2,10.5),(-15.3,22.5,128,19.2,10.5),(-15.3,22.5,117,17.5,9),(-15.3,22.5,112,12,6.5)],np.isin(comp,[7,12,13]))
me=bpy.data.meshes.new('Sui_JK_motion_experiment');me.from_pydata(vertices,[],faces);me.update()
for mat in materials:me.materials.append(mat)
for p,mi in zip(me.polygons,mats):p.material_index=mi;p.use_smooth=True
layer=me.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',np.array(uv).ravel());o.data=me;write_weights(o,W)
for name,v in [('source_component',components),('v10_vertex_index',ids),('v8_vertex_index',v8ids)]:me.attributes.new(name=name,type='INT',domain='POINT').data.foreach_set('value',v)
me.attributes.new(name='source_rest_position',type='FLOAT_VECTOR',domain='POINT').data.foreach_set('vector',np.array(rest).ravel())
me.normals_split_custom_set([Vector(n).normalized() if Vector(n).length>1e-7 else me.vertices[me.loops[i].vertex_index].normal for i,n in enumerate(normal)])
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'sui-jk-motion-source.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
bpy.ops.export_scene.fbx(filepath=str(OUT/'Sui_JK_Hun_Body_Motion.fbx'),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
def cloth(slot,name,sim,zfixed,d1,maximum,gravity,stiffness,additional=[]):
 return {'slot':slot,'name':name,'max_distance':maximum,'mask':{'type':'plane','anchors':[[0,0,zfixed]],'dir':[0,0,-1],'d0':0,'d1':d1,'sim_slot':sim},'additional_render_slots':additional,'config':{'EdgeStiffnessWeighted':{'Low':1,'High':1},'AreaStiffnessWeighted':{'Low':1,'High':1},'BendingStiffnessWeighted':{'Low':stiffness,'High':stiffness},'bUseBendingElements':True,'bUseGeodesicDistance':True,'TetherStiffness':{'Low':1,'High':1},'TetherScale':{'Low':1,'High':1},'AnimDriveStiffness':{'Low':.15,'High':.15},'AnimDriveDamping':{'Low':.5,'High':.5},'GravityScale':gravity,'DampingCoefficient':.08,'LocalDampingCoefficient':.2,'CollisionThickness':.25,'FrictionCoefficient':.4,'bUseSelfCollisions':False,'LinearVelocityScale':[.55,.55,.55],'AngularVelocityScale':.5,'VolumeStiffness':.95 if 'Charm' in slot or 'Backpack' in slot else 0,'bUseThinShellVolumeConstraints':'Charm' in slot or 'Backpack' in slot}}
charm=json.loads((ROOT/'section-map.json').read_text())['charm_slots']
configs=[cloth('MI_JK_Ponytail','CA_Sui_Ponytail','MI_JK_PonytailSim',188,39,6,.15,.9),cloth(charm[0],'CA_Sui_Charm','MI_JK_CharmSim',142.4,12.5,3.2,.45,1,charm[1:]),cloth('MI_JK_PleatedSkirt','CA_Sui_Skirt','MI_JK_SkirtSim',106,14,.65,.15,.95),cloth('MI_JK_CardiganHem','CA_Sui_CardiganHem','MI_JK_CardiganHemSim',120,18,.8,.18,.9),cloth('MI_JK_Backpack','CA_Sui_Backpack','MI_JK_BackpackSim',151,39,.55,.2,1)]
(OUT/'cloth-spec-draft.json').write_text(json.dumps(configs,indent=2));(OUT/'source-preparation.json').write_text(json.dumps({'status':'geometry-and-config-draft-only-not-UE-imported-not-simulated-not-cooked-not-installed','baseline':'v11-static-verified','no_new_bones':True,'bones':len(a.data.bones),'simulation_cages':reports,'legacy_clothing_runtime_in_PBZ_unverified':True,'toolchain_prerequisite':'compatible MSVC and Windows SDK; user timing decision pending'},indent=2));print(json.dumps(reports),flush=True)
