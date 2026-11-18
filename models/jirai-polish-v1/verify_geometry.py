"""Surface preservation, seam closure, eye projection and UV chart regression gates."""
from common import *
import numpy as np,collections,importlib.util,cv2
from PIL import Image
def edge_counts(p,t):
 _,inv=np.unique(np.round(p,4),axis=0,return_inverse=True);t=inv[t]
 good=(t[:,0]!=t[:,1])&(t[:,1]!=t[:,2])&(t[:,2]!=t[:,0]);t=t[good]
 e=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);e.sort(1);uniq,n=np.unique(e,axis=0,return_counts=True)
 return inv,{tuple(e):int(nn) for e,nn in zip(uniq,n)}
def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);old=np.load(PIN/'final-render.npz');sel=np.load(ROOT/'author-selections.npz');report=read(ROOT/'author-report.json')
 assert report['native_sha256']==sha(ROOT/'patched-render.npz') and report['atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 p=d['positions'];t=d['indices'].reshape(-1,3);mat=d['materials'];reserve=np.zeros(len(p),bool);reserve[sel['reserve']]=True
 allowed=sel['eye']|sel['mouth']|reserve;allowed[sel['halo']]=True
 assert np.array_equal(p[~allowed],old['positions'][~allowed])
 assert np.array_equal(d['packed_tangents'][~allowed],old['packed_tangents'][~allowed])
 assert np.array_equal(d['uv'][:,1],old['uv'][:,1]) and np.array_equal(d['uv'][mat!=0],old['uv'][mat!=0])
 keep=np.ones(len(t),bool);keep[sel['slots']]=False
 assert np.array_equal(t[keep],old['indices'].reshape(-1,3)[keep])
 assert np.isfinite(p).all() and np.isfinite(d['normals']).all()
 n=d['normals'];tan=d['packed_tangents'][:,:3].view('i1').astype(float)/127
 assert np.max(abs(np.linalg.norm(n[allowed],axis=1)-1))<.014
 assert np.max(abs((tan[allowed]*n[allowed]).sum(1)))<.025
 assert np.array_equal(p[sel['mouth']],old['positions'][sel['mouth']]),'Original coherent lip geometry changed'
 # New triangles remain inside the original Skin render section.
 assert np.all(mat[sel['bridge_triangles']]==0)
 tri=sel['bridge_triangles'];area=np.linalg.norm(np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]),axis=1)
 assert area.min()>1e-5
 lids=sel['rim_triangles'];assert len(lids)==report['eyelid_patch_triangles'] and np.all(mat[lids]==0)
 lid_cross=np.cross(p[lids[:,1]]-p[lids[:,0]],p[lids[:,2]]-p[lids[:,0]])
 assert np.linalg.norm(lid_cross,axis=1).min()>1e-5
 assert np.all(lid_cross[:,1]<-1e-9),'Eyelid projection folds or reversed triangles'
 edges=np.concatenate([lids[:,[0,1]],lids[:,[1,2]],lids[:,[2,0]]]);edges.sort(1);_,incidence=np.unique(edges,axis=0,return_counts=True)
 assert np.count_nonzero(incidence==1)==len(sel['eye_seams'])+96 and np.all(incidence<=2),'Invalid eyelid patch topology'
 inv,counts=edge_counts(p,t[mat[t[:,0]]==0]);rings=[];directions=collections.defaultdict(list)
 for face in inv[t[mat[t[:,0]]==0]]:
  if len(set(face))<3:continue
  for a,b in zip(face,np.roll(face,-1)):directions[tuple(sorted((int(a),int(b))))].append(int(a)<int(b))
 copies=dict(sel['weight_copies'].tolist())
 for a,b in sel['eye_seams']:
  edge=tuple(sorted((int(inv[a]),int(inv[b]))))
  assert counts[edge]==2 and directions[edge][0]!=directions[edge][1],('Unstitched eye seam',edge)
 for row in report['bridges']:
  for name in ['upper_original','lower_original']:
   ring=np.array(row[name]);edges=[tuple(sorted((int(inv[a]),int(inv[b])))) for a,b in zip(ring,np.roll(ring,-1))]
   # Angularly ordered points are the actual geometric boundary ring.
   assert all(counts[e]==2 for e in edges),(name,[(e,counts.get(e)) for e in edges if counts.get(e)!=2])
   assert all(directions[e][0]!=directions[e][1] for e in edges),'Arm seam triangle winding disagrees with original skin'
   rings.append(dict(side=row['side'],ring=name,closed_edges=len(edges)))
  for idx in row['new_vertices']:assert np.array_equal(p[idx],p[copies[idx]])
 # Colors on every non-head triangle must stay within a uniform, feature-free
 # portion of the new chart; no face pattern can leak onto torso/arms/legs.
 head=sel['head'];atlas=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'));body=np.zeros((8192,8192),np.uint8)
 for f in t[(mat[t[:,0]]==0)&~head[t].all(1)]:
  q=np.rint(d['uv'][f,0].astype(float)*8191).astype('i4');cv2.fillConvexPoly(body,q,255)
 assert np.all(atlas[body>0]==[247,225,224]),'Facial patterns leak into body chart'
 # Evaluate visible projected eye material coverage with the same ray grid.
 spec=importlib.util.spec_from_file_location('face3_projection',REPO/'models/jirai-face-v3/verify_geometry.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 cover=[]
 for name,data in [('before',old),('after',d)]:
  _,owner,_,_,x,z=m.raster(data['positions'],data['indices'].reshape(-1,3),mat,w=600,h=220)
  cover.append(dict(stage=name,visible_sclera_rays=int((owner==19).sum()),visible_iris_rays=int((owner==18).sum())))
 assert cover[1]['visible_sclera_rays']<cover[0]['visible_sclera_rays']*.80,cover
 assert cover[1]['visible_iris_rays']>cover[0]['visible_iris_rays']*.50,cover
 # Native iris and sclera remain unchanged topologically, with the same UVs.
 for material in [18,19]:
  active=t[mat[t[:,0]]==material];assert np.array_equal(active,old['indices'].reshape(-1,3)[mat[old['indices'].reshape(-1,3)[:,0]]==material])
 halo=p[sel['halo']];eig=np.linalg.eigvalsh(np.cov(halo.T));aspect=float(np.sqrt(eig[-2]/eig[-1]));assert .72<aspect<1.15
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),unrelated_positions_frames_indices_exact=True,uv1_and_non_skin_uv_exact=True,mouth_geometry_exact=True,bridge_triangles=len(tri),closed_arm_boundaries=rings,bridge_boundary_position_copies_exact=True,skin_weight_copy_count=len(copies),eyelid_patch_triangles=len(lids),eyelid_head_seam_edges_closed=int(len(sel['eye_seams'])),eyelid_projection_unfolded=True,eye_projection=cover,halo_principal_plane_aspect=aspect,body_chart_uniform_verified=True,game_runtime_tested=False))
 print('POLISH_GEOMETRY_VERIFIED',cover,flush=True)
if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
