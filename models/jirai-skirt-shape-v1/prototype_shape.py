"""Compare real geometry variants; no generated paintover or game capture."""
import bpy,bmesh,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Vector
C=Path(__file__).resolve().parent;R=C.parents[1];W=R/'private/jirai-skirt-shape-v1';B=R/'private/jirai-skirt-recovery-v1'
sys.path.insert(0,str(C));from current_atlas import apply as apply_atlas

def smooth(x):
 t=np.clip(x,0,1);return t*t*(3-2*t)

def transform(p,trim=True):
 q=p.copy();rad=p[:,:2]-[0,5];radius=np.linalg.norm(rad,axis=1)
 undo=4*smooth((122-p[:,2])/14)
 tuck=.9*smooth((114-p[:,2])/9) if trim else 0
 q[:,:2]-=rad/np.maximum(radius[:,None],1)*(undo+tuck)[:,None]
 if trim:q[:,2]-=1.5*smooth((113-p[:,2])/10)+2.2*smooth((np.abs(q[:,0])-18)/12)*smooth((117-p[:,2])/13)
 return q

for mode in ['lowered-sides']:
 bpy.ops.wm.open_mainfile(filepath=str(B/'sui-jirai-motion.blend'))
 o=next(x for x in bpy.context.scene.objects if x.type=='MESH');m=o.data;apply_atlas(m)
 for mod in o.modifiers:mod.show_render=False;mod.show_viewport=False
 ids=sorted({i for f in m.polygons if m.materials[f.material_index].name=='MI_Jirai_Skirt' for i in f.vertices})
 old=np.array([v.co[:] for v in m.vertices]);normals=np.array([n.vector[:] for n in m.corner_normals]);new=old.copy()
 if mode!='before':
  new[ids]=transform(old[ids],True)
  for f in m.polygons:
   if m.materials[f.material_index].name!='MI_Jirai_Skirt':continue
   ix=np.array(f.vertices);p=old[ix];j=np.empty((len(ix),3,3))
   for axis in range(3):
    d=np.zeros_like(p);d[:,axis]=.002
    j[:,:,axis]=(transform(p+d,True)-transform(p-d,True))/.004
   n=np.linalg.solve(j.transpose(0,2,1),normals[list(f.loop_indices)][...,None])[...,0]
   normals[list(f.loop_indices)]=n/np.linalg.norm(n,axis=1)[:,None]
  m.vertices.foreach_set('co',new.ravel());m.update();m.normals_split_custom_set(normals.tolist());m.update()
 report={'bounds_before':[old[ids].min(0).tolist(),old[ids].max(0).tolist()],'bounds_after':[new[ids].min(0).tolist(),new[ids].max(0).tolist()]}
 (W/(mode+'-dimensions.json')).write_text(json.dumps(report,indent=2))
 bm=bmesh.new();bm.from_mesh(m);layer=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[layer]>=2000],context='VERTS');bm.to_mesh(m);bm.free();m.update()
 s=bpy.context.scene;s.cycles.samples=4;s.render.resolution_x=640;s.render.resolution_y=800;s.render.resolution_percentage=100;s.view_settings.exposure=.4;cam=s.camera
 for name,pos in [('front',(0,-400,109)),('side',(400,-40,109))]:
  cam.location=pos;cam.rotation_euler=(Vector((0,0,109))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=100
  s.render.filepath=str(W/'preview'/f'{mode}-{name}.png');bpy.ops.render.render(write_still=True)
print('PROTOTYPE_SILHOUETTES_RENDERED')
