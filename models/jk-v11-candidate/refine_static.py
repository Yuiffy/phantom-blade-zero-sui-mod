"""V11 surface and attachment geometry; preserve the original joint pivots."""
import bpy,numpy as np,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent/'tripo-refine-v10';sys.path.insert(0,str(BASE))
from v7_helpers import fix_custom_normals,write_weights,sstep
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');old=o.data;a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
co=np.array([v.co[:] for v in old.vertices]);new=co.copy();comp=np.array([d.value for d in old.attributes['source_component'].data])
W=[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups if g.weight>1e-7} for v in old.vertices]
hand_reports=[]
for c,side in [(4,'r'),(5,'l')]:
 idx=np.flatnonzero(comp==c);p=co[idx];delta=np.zeros_like(p)
 # Actual child-joint positions define each phalanx axis. Imported bone tails
 # have display lengths/orientations and are not the next joint.
 for finger in ['thumb','index','middle','ring','pinky']:
  heads=[np.array(a.data.bones[f'{finger}_{j:02d}_{side}'].head_local) for j in [1,2,3]]
  heads.append(heads[-1]+(heads[-1]-heads[-2])*.85)
  for j in range(3):
   name=f'{finger}_{j+1:02d}_{side}';start=heads[j];end=heads[j+1];axis=end-start;axis/=np.linalg.norm(axis)
   d=p-start;axial=d@axis;rad=d-axial[:,None]*axis
   wt=np.array([W[i].get(name,0) for i in idx])
   # Add 24% radial volume, up to 2.6mm, without shortening fingers or
   # translating their joint centers. Fade beyond the rounded end cap.
   r=np.linalg.norm(rad,axis=1);grow=np.minimum(.24*r,.26)
   delta+=rad/np.maximum(r[:,None],1e-8)*grow[:,None]*wt[:,None]
 # Keep the crowded palm/thumb-web and the cuff aligned exactly. Additional
 # normal inflation there shortened existing 1mm seam edges; the added volume
 # belongs on the fingers and fades into the unchanged palm over 2cm.
 delta*=sstep((109-p[:,2])/2)[:,None]
 new[idx]+=delta
 hand_reports.append({'side':side,'vertices':len(idx),'max_radial_addition_cm':float(np.linalg.norm(delta,axis=1).max()),'weights_unchanged':True,'joint_matrices_unchanged':True})
old.vertices.foreach_set('co',new.ravel());old.update();fix_custom_normals(old,co,new)
# Re-seat charm reliefs against their supporting surface, rather than a stack
# of disconnected front-facing decals.
faces0=np.array([p.vertices[:] for p in old.polygons]);mi0=np.array([p.material_index for p in old.polygons])
ch=comp==101
gold=ch&np.isin(np.arange(len(comp)),np.unique(faces0[(comp[faces0[:,0]]==101)&(mi0==1)]))
new[gold&(co[:,2]>132),1]+=.66
# Move the whole existing loop behind the ears and up to a real strap point.
loop=ch&(co[:,2]>138.4)&(co[:,1]>-7.1)
new[ch&~loop,1]+=2.2
strapfaces=[p.vertices[:] for p in old.polygons if comp[p.vertices[0]] in {15,32,35}]
bvh=BVHTree.FromPolygons([Vector(v) for v in new],strapfaces,all_triangles=True)
anchor,normal,anchor_face,distance=bvh.find_nearest(Vector((-12.55,-5.2,143.5)))
anchor=np.array(anchor);top=np.array([-12.55,-6.65,143.5]);shift=anchor-top+np.array([0,-.16,0]);new[loop]+=shift
tri=np.array(strapfaces[anchor_face]);points=new[tri];bary=np.linalg.lstsq(np.column_stack((points[1]-points[0],points[2]-points[0])),anchor-points[0],rcond=None)[0];bary=np.array([1-bary.sum(),*bary]);assert bary.min()>-1e-5
attachment_weights={}
for vi,fraction in zip(tri,bary):
 for name,value in W[int(vi)].items():attachment_weights[name]=attachment_weights.get(name,0)+float(fraction)*value
attachment_weights={k:v for k,v in attachment_weights.items() if v>1e-6};total=sum(attachment_weights.values());attachment_weights={k:v/total for k,v in attachment_weights.items()}
for vi in np.flatnonzero(ch):W[int(vi)]=dict(attachment_weights)
old.vertices.foreach_set('co',new.ravel());old.update()
# Remove the old melted cat-face blobs. Face detail is painted directly on the
# stocking surface, and the charm's isolated gold block below the body is gone.
remove=np.isin(comp,[57,61,63]);remove|=ch&(co[:,2]<129)
keep=~remove;indices=np.flatnonzero(keep);mapping=np.full(len(comp),-1);mapping[indices]=np.arange(len(indices))
vertices=[tuple(v) for v in new[indices]];weights=[W[i] for i in indices];components=comp[indices].tolist();ids=[int(old.attributes['v8_vertex_index'].data[i].value) for i in indices];v10ids=indices.tolist();rest=[old.attributes['source_rest_position'].data[i].vector[:] for i in indices]
faces=[];uv=[];mats=[];normals=[]
for p in old.polygons:
 if not all(keep[i] for i in p.vertices):continue
 faces.append(tuple(mapping[i] for i in p.vertices));uv.extend([old.uv_layers.active.data[l].uv[:] for l in p.loop_indices]);mats.append(p.material_index)
 normals.extend([old.vertices[old.loops[l].vertex_index].normal[:] if comp[old.loops[l].vertex_index] in {4,5} else old.corner_normals[l].vector[:] for l in p.loop_indices])
def tube(points,radius,material,component,label):
 off=len(vertices);pts=[Vector(p) for p in points];vv=[];ff=[];sides=10
 for i,p in enumerate(pts):
  axis=(pts[min(i+1,len(pts)-1)]-pts[max(i-1,0)]).normalized();e=axis.cross(Vector((0,1,0)))
  if e.length<.01:e=axis.cross(Vector((1,0,0)))
  e.normalize();q=axis.cross(e).normalized()
  for k in range(sides):vv.append(tuple(p+radius*(math.cos(k*2*math.pi/sides)*e+math.sin(k*2*math.pi/sides)*q)))
 for i in range(len(pts)-1):
  for k in range(sides):
   h=(k+1)%sides;b=i*sides;n=b+sides;ff.extend([(b+k,b+h,n+h),(b+k,n+h,n+k)])
 vv.extend([tuple(pts[0]),tuple(pts[-1])]);s=len(vv)-2;t=s+1
 for k in range(sides):h=(k+1)%sides;ff.extend([(s,h,k),(t,(len(pts)-1)*sides+k,(len(pts)-1)*sides+h)])
 vertices.extend(vv);weights.extend([dict(attachment_weights) for _ in vv]);components.extend([component]*len(vv));ids.extend([-1]*len(vv));v10ids.extend([-1]*len(vv));rest.extend([(0,0,0)]*len(vv))
 for face in ff:faces.append(tuple(off+i for i in face));uv.extend([(0,0),(1,0),(0,1)]);mats.append(material);normals.extend([(0,0,0)]*3)
 return {'label':label,'component':component,'vertices':len(vv),'triangles':len(ff)}
# A short load-bearing textile tab actually enters the strap; its lower end
# passes into the loop. Same spine_04 weight at all ends prevents rest/pose gaps.
loopbottom=np.array([-12.55,-6.65,138.8])+shift
joinpoint=np.array([-12.55,-6.65,139.65])+shift
earpoint=np.array([-12.55,-5.55,139.45])
parts=[tube([anchor+np.array([0,.13,0]),anchor+np.array([0,-.24,-.45]),anchor+np.array([0,-.28,-1.15])],.24,4,102,'strap-embedded hanging tab'),tube([joinpoint,(joinpoint+earpoint)/2,earpoint],.17,4,101,'loop to plush sewn eyelet')]
me=bpy.data.meshes.new('Sui_JK_v11_polished');me.from_pydata(vertices,[],faces);me.update()
for mat in old.materials:me.materials.append(mat)
for p,mat in zip(me.polygons,mats):p.material_index=int(mat);p.use_smooth=True
layer=me.uv_layers.new(name=old.uv_layers.active.name);layer.data.foreach_set('uv',np.array(uv).ravel())
o.data=me;write_weights(o,weights)
for name,values,kind in [('source_component',components,'INT'),('v8_vertex_index',ids,'INT'),('v10_vertex_index',v10ids,'INT')]:me.attributes.new(name=name,type=kind,domain='POINT').data.foreach_set('value',values)
me.attributes.new(name='source_rest_position',type='FLOAT_VECTOR',domain='POINT').data.foreach_set('vector',np.array(rest).ravel())
normalout=[Vector(n).normalized() if Vector(n).length>1e-7 else me.vertices[me.loops[i].vertex_index].normal.copy() for i,n in enumerate(normals)];me.normals_split_custom_set(normalout)
np.savez_compressed(ROOT/'atlas-provenance.npz',co=np.array(vertices),comp=np.array(components),faces=np.array(faces),uv=np.array(uv).reshape(-1,3,2),mi=np.array(mats))
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sui-jk-hun-bound.blend'),compress=True)
report={'baseline':'v10','hands':hand_reports,'removed_old_cat_face_components':[57,61,63],'strap_anchor_cm':anchor.tolist(),'anchor_face_v10_indices':tri.tolist(),'anchor_barycentric':bary.tolist(),'attachment_weights':attachment_weights,'loop_translation_cm':shift.tolist(),'charm_seated_toward_strap_cm':2.2,'parts':parts,'vertices':len(vertices),'triangles':len(faces),'bones':len(a.data.bones),'material_slots':len(me.materials),'max_influences':max(map(len,weights)),'new_physics':False}
(ROOT/'binding-report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
