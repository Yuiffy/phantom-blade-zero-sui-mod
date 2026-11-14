"""Reference-led replacement of the small wing pin and cat bag charm.

Works on the already fixed v9-core, never on a previously refined output.
No cloth simulation, new bones or game animation data. Coordinates in cm.
"""
import bpy, math, json, hashlib, numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'sui-jk-v9-core.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');old=o.data
a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
comp=np.array([d.value for d in old.attributes['source_component'].data])
group_names=[g.name for g in o.vertex_groups]
# Wing/heart, malformed extra dots on the left stocking, cat head/body/bow/loop.
REMOVE={9,18,19,26,27,33,37,58,60,62,68}
keep=~np.isin(comp,list(REMOVE));ix=np.flatnonzero(keep);mapping={int(i):j for j,i in enumerate(ix)}
vertices=[old.vertices[i].co[:] for i in ix];faces=[];uv=[];mats=[];normals=[]
weights=[{o.vertex_groups[g.group].name:float(g.weight) for g in old.vertices[i].groups if g.weight>1e-7} for i in ix]
ids=[int(old.attributes['v8_vertex_index'].data[i].value) for i in ix]
components=[int(comp[i]) for i in ix]
rest=[old.attributes['source_rest_position'].data[i].vector[:] for i in ix]
for p in old.polygons:
 if not all(keep[v] for v in p.vertices):continue
 faces.append(tuple(mapping[v] for v in p.vertices));mats.append(p.material_index)
 uv.extend([old.uv_layers.active.data[l].uv[:] for l in p.loop_indices])
 normals.extend([old.corner_normals[l].vector[:] for l in p.loop_indices])
original_face_count=len(faces);original_vert_count=len(vertices)
materials=list(old.materials)
# Solid ivory adds only native leaf MI/VT assets through the existing pipeline.
name='MI_JK_Ivory';iv=bpy.data.materials.get(name) or bpy.data.materials.new(name);iv.use_nodes=True
bs=iv.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.92,.91,.89,1);bs.inputs['Roughness'].default_value=.55
materials.append(iv);IVORY=len(materials)-1
GOLD=1;PINK=2;INK=3;PINKDARK=4;SILVER=5;BLUSH=6
new_parts=[]
def add(v,f,mat,component,weight,label):
 offset=len(vertices);vertices.extend([tuple(p) for p in v]);weights.extend([dict(weight) for _ in v]);ids.extend([-1]*len(v));components.extend([component]*len(v));rest.extend([(0,0,0)]*len(v))
 for face in f:
  faces.append(tuple(offset+i for i in face));mats.append(mat);uv.extend([(0,0),(1,0),(0,1)]);normals.extend([(0,0,0)]*3)
 new_parts.append({'label':label,'component':component,'vertices':len(v),'triangles':len(f),'weights':weight})
def sphere(center,scale,mat,c,w,label,segments=16,rings=10):
 # Closed ellipsoid with explicit pole fans, avoiding zero-area pole quads.
 v=[(center[0],center[1],center[2]+scale[2])];f=[]
 for j in range(1,rings):
  t=math.pi*j/rings
  for i in range(segments):
   p=2*math.pi*i/segments;v.append((center[0]+scale[0]*math.sin(t)*math.cos(p),center[1]+scale[1]*math.sin(t)*math.sin(p),center[2]+scale[2]*math.cos(t)))
 bottom=len(v);v.append((center[0],center[1],center[2]-scale[2]))
 for i in range(segments):f.append((0,1+i,1+(i+1)%segments))
 for j in range(rings-2):
  b=1+j*segments;n=b+segments
  for i in range(segments):
   k=(i+1)%segments;f.extend([(b+i,n+i,n+k),(b+i,n+k,b+k)])
 for i in range(segments):f.append((bottom,1+(rings-2)*segments+(i+1)%segments,1+(rings-2)*segments+i))
 add(v,f,mat,c,w,label)
def badge(outline,y,depth,mat,c,w,label):
 # Bevelled shallow solid; outline is counterclockwise in the X/Z plane.
 pts=np.asarray(outline,float);center=pts.mean(axis=0);n=len(pts);v=[];f=[]
 for inset,dy in [(0,depth*.5),(0,-depth*.12),(.16,-depth*.5)]:
  for x,z in center+(pts-center)*(1-inset):v.append((x,y+dy,z))
 v.extend([(center[0],y+depth*.5,center[1]),(center[0],y-depth*.60,center[1])])
 for j in range(2):
  for i in range(n):
   k=(i+1)%n;f.extend([(j*n+i,j*n+k,(j+1)*n+k),(j*n+i,(j+1)*n+k,(j+1)*n+i)])
 for i in range(n):
  k=(i+1)%n;f.extend([(3*n,k,i),(3*n+1,2*n+i,2*n+k)])
 add(v,f,mat,c,w,label)
def tube(points,radius,mat,c,w,label,sides=8):
 pts=[Vector(p) for p in points];v=[];f=[]
 for i,p in enumerate(pts):
  t=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();e=t.cross(Vector((0,1,0))).normalized();q=t.cross(e).normalized()
  for k in range(sides):v.append(tuple(p+radius*(math.cos(k*2*math.pi/sides)*e+math.sin(k*2*math.pi/sides)*q)))
 for i in range(len(pts)-1):
  for k in range(sides):
   h=(k+1)%sides;b=i*sides;n=b+sides;f.extend([(b+k,b+h,n+h),(b+k,n+h,n+k)])
 v.extend([tuple(pts[0]),tuple(pts[-1])]);start=len(v)-2;end=start+1
 for k in range(sides):
  h=(k+1)%sides;f.extend([(start,h,k),(end,(len(pts)-1)*sides+k,(len(pts)-1)*sides+h)])
 add(v,f,mat,c,w,label)
def heart(x,z,y,size,c,w,label):
 outline=[]
 for t in np.linspace(0,2*math.pi,40,endpoint=False):
  outline.append((x+size*math.sin(t)**3,z+size*(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))/16))
 badge(outline[::-1],y,.32,GOLD,c,w,label)
def feather(start,tip,width,y,c,w,label):
 s=np.array(start);t=np.array(tip);d=t-s;perp=np.array([-d[1],d[0]])/np.linalg.norm(d);outline=[]
 for side,ts in [(1,np.linspace(0,1,15)),(-1,np.linspace(1,0,15)[1:-1])]:
  for u in ts:outline.append(tuple(s+d*u+perp*side*width*math.sin(math.pi*u)**.75))
 badge(outline,y,.43,IVORY,c,w,label)
stock={'thigh_l':1.};bag={'spine_04':1.}
# Original shows a small feather fan with a gold heart below the meeting point.
for sign in [-1,1]:
 for j,(dx,dz,width) in enumerate([(4.75,3.85,.70),(4.30,2.52,.70),(3.55,1.44,.65),(2.66,.65,.53)]):
  feather((10.72+sign*.30,78.75+j*.07),(10.72+sign*dx,78.55+dz),width,-3.55-j*.18,100,stock,'wing-%s-feather-%d'%(sign,j))
heart(10.72,78.22,-4.45,.72,100,stock,'stocking gold heart pin')
# Cat charm: small soft ears, dark eyes, blush, whiskers, bow and gold center.
sphere((-12.55,-8.2,136.8),(3.35,1.25,2.28),IVORY,101,bag,'cat head',24,14)
for sign in [-1,1]:
 x=-12.55+sign*2.35
 badge([(x-sign*1.0,138.0),(x+sign*.60,138.1),(x+sign*.48,140.15)],-8.15,.95,IVORY,101,bag,'cat outer ear')
 badge([(x-sign*.43,138.40),(x+sign*.26,138.45),(x+sign*.27,139.46)],-8.73,.13,BLUSH,101,bag,'cat pink inner ear')
 sphere((-12.55+sign*1.25,-9.37,136.92),(.20,.12,.30),INK,101,bag,'cat eye',12,8)
 sphere((-12.55+sign*1.28,-9.48,137.02),(.06,.03,.08),IVORY,101,bag,'cat eye catchlight',8,6)
 sphere((-12.55+sign*2.08,-9.15,136.17),(.43,.075,.19),BLUSH,101,bag,'cat blush',12,8)
 for k in [0,1]:
  tube([(-12.55+sign*2.05,-9.25,136.4+k*.29),(-12.55+sign*2.65,-9.08,136.30+k*.42)],.047,INK,101,bag,'cat whisker',6)
 # Bow lobes are fabric silhouettes rather than the old melted blobs.
 outline=[(-12.55+sign*u,133.8+z) for u,z in [(.15,.25),(1.65,1.18),(3.75,1.00),(4.0,.20),(3.65,-.85),(1.7,-.65)]]
 badge(outline,-8.45,.74,PINK,101,bag,'pink bow lobe')
 tube([(-12.55+sign*.55,-8.96,133.75),(-12.55+sign*1.5,-8.94,133.9),(-12.55+sign*2.9,-8.85,134.25)],.06,PINKDARK,101,bag,'bow fold',6)
badge([(-12.83,136.31),(-12.27,136.31),(-12.55,136.03)],-9.58,.10,BLUSH,101,bag,'cat triangle nose')
tube([(-12.55, -9.52,136.03),(-12.55,-9.51,135.82),(-12.92,-9.48,135.75)],.055,INK,101,bag,'cat mouth left',6)
tube([(-12.55,-9.51,135.82),(-12.18,-9.48,135.75)],.055,INK,101,bag,'cat mouth right',6)
sphere((-12.55,-8.15,134.2),(.88,.72,.95),IVORY,101,bag,'continuous cat neck',16,10)
sphere((-12.55,-8.35,132.2),(1.75,.86,2.10),IVORY,101,bag,'cat drop body',20,12)
heart(-12.55,133.87,-9.45,.66,101,bag,'bow gold heart')
# Narrow pink hanging loop terminates behind the ears, connected to strap.
loop=[(-12.55+.56*math.sin(t),-6.65,141.15+2.35*math.cos(t)) for t in np.linspace(0,2*math.pi,33)]
tube(loop,.18,PINKDARK,101,bag,'charm attachment loop')
badge([(-14.35,128.4),(-13.15,128.4),(-13.15,127.45),(-14.35,127.45)],-6.55,.25,GOLD,101,bag,'small lower gold clasp')

me=bpy.data.meshes.new('JK_v9_reference_ornaments');me.from_pydata(vertices,[],faces);me.update()
for mat in materials:me.materials.append(mat)
for p,mi in zip(me.polygons,mats):p.material_index=mi;p.use_smooth=True
uvl=me.uv_layers.new(name=old.uv_layers.active.name)
uvl.data.foreach_set('uv',np.asarray(uv).ravel())
for name,typ,vals in [('source_component','INT',components),('v8_vertex_index','INT',ids),('source_rest_position','FLOAT_VECTOR',rest)]:
 at=me.attributes.new(name,typ,'POINT');at.data.foreach_set('vector' if typ=='FLOAT_VECTOR' else 'value',np.asarray(vals).ravel())
# Preserve existing corner normals exactly. New smooth components get their own
# geometric vertex normals, keeping the rebuilt features independent of atlas.
for li in range(original_face_count*3,len(me.loops)):normals[li]=me.vertices[me.loops[li].vertex_index].normal[:]
me.normals_split_custom_set(normals)
o.data=me
o.vertex_groups.clear()
for name in group_names:o.vertex_groups.new(name=name)
for i,row in enumerate(weights):
 for name,w in row.items():o.vertex_groups[name].add([i],w,'REPLACE')
assert len(me.polygons)==len(faces) and len(a.data.bones)==264
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
fbx=ROOT/'Sui_JK_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report={'reference':'original single ponytail outfit art, 9245208a attachment','removed_v8_components':sorted(REMOVE),'preserved_vertices':original_vert_count,'preserved_triangles':original_face_count,'added_vertices':len(vertices)-original_vert_count,'added_triangles':len(faces)-original_face_count,'components':{'100':'stocking feather wings and gold heart; thigh_l','101':'backpack cat charm, bow and loop; spine_04'},'new_parts':new_parts,'no_new_bones_or_physics':True,'new_material':'MI_JK_Ivory; same native parent in game'}
(ROOT/'ornament-refinement.json').write_text(json.dumps(report,indent=2))
binding=json.loads((ROOT/'binding-report.json').read_text());binding.update(vertices=len(vertices),triangles=len(faces),bones=264,material_slots=len(materials),fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),max_influences=max(map(len,weights)))
binding['core_badges_rebound_before_ornament_replacement']=212
binding['badges_rebound_to_thigh']=int(np.isin(components,[57,61,63]).sum())
(ROOT/'binding-report.json').write_text(json.dumps(binding,indent=2))
spec=json.loads((ROOT/'game-materials.json').read_text());spec=[m for m in spec if m['slot']!='MI_JK_Ivory'];spec.append({'slot':'MI_JK_Ivory','base_color_linear':[.92,.91,.89,1],'roughness':.55,'metallic':0,'source_texture':None})
(ROOT/'game-materials.json').write_text(json.dumps(spec,indent=2))
print(json.dumps(binding))
