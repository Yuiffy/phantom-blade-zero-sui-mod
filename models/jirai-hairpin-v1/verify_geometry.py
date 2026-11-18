"""Check final topology, rigid binding, retained face, atlas ownership and clearance."""
from common import *
import numpy as np,collections,cv2
from PIL import Image

def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);old=np.load(FACE/'native/final-render.npz');a=np.load(ROOT/'authored-geometry.npz');report=read(ROOT/'author-report.json')
 ids=a['selected_vertices'];slots=a['selected_triangles'];count=report['new_vertices'];num=report['new_triangles']
 mask=np.zeros(len(d['positions']),bool);mask[ids]=True
 for key in ['positions','normals','packed_tangents','uv']:assert np.array_equal(d[key][~mask],old[key][~mask]),key
 assert np.array_equal(d['uv'][:,1],old['uv'][:,1])
 tmask=np.zeros(len(d['indices'])//3,bool);tmask[slots]=True
 tri=d['indices'].reshape(-1,3);assert np.array_equal(tri[~tmask],old['indices'].reshape(-1,3)[~tmask])
 assert np.array_equal(tri[slots[:num]],ids[a['triangles']])
 assert np.all(tri[slots[num:]]==ids[0])
 assert np.isfinite(d['positions']).all() and np.isfinite(d['normals']).all()
 assert np.max(np.abs(np.linalg.norm(d['normals'][ids],axis=1)-1))<.012
 tangent=d['packed_tangents'][ids,:3].view('i1').astype(float)/127
 assert np.abs((tangent*d['normals'][ids]).sum(1)).max()<.016
 edges=collections.defaultdict(list)
 for i,face in enumerate(a['triangles']):
  for x,y in zip(face,np.roll(face,-1)):edges[tuple(sorted((int(x),int(y))))].append((i,int(x)<int(y)))
 assert all(len(rows)==2 and rows[0][1]!=rows[1][1] for rows in edges.values()),'Open or inconsistently oriented accessory'
 # Verify source PNG changes against actual half-float native UV ownership.
 before=np.array(Image.open(FACE/'T_Jirai_Base.png').convert('RGB'));after=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'))
 changed=np.any(before!=after,axis=2);deprojection=np.array(Image.open(ROOT/'hair-deprojection-mask.png'))>0
 protected=np.zeros((8192,8192),np.uint8);carrier=protected.copy()
 basis=a['basis'];local=(old['positions']-a['center'])@basis.T;normal=basis[2]
 for face in old['indices'].reshape(-1,3)[(old['materials'][old['indices'].reshape(-1,3)[:,0]]==1)&~tmask]:
  q=old['uv'][face,0].astype(float)*8191;q3=local[face]
  outside=(q3[:,0].min()>3.7 or q3[:,0].max()<-3.7 or q3[:,1].min()>2.9 or q3[:,1].max()<-4.6 or q3[:,2].max()<-1.25 or old['normals'][face].mean(0)@normal<.05)
  if outside:cv2.fillConvexPoly(protected,np.rint(q).astype('i4'),255);continue
  lo=np.floor(q.min(0)).astype(int).clip(0,8191);hi=np.ceil(q.max(0)).astype(int).clip(0,8191)
  m=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(m))<1e-9:continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
  bary=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(m).T;bary=np.dstack([bary,1-bary.sum(-1)]);valid=(bary>=-1e-6).all(-1)
  xyz=(bary@q3)[valid];ok=(np.abs(xyz[:,0])<3.7)&(xyz[:,1]>-4.6)&(xyz[:,1]<2.9)&(xyz[:,2]>-1.25)&(xyz[:,2]<.25)
  x=xx[valid];y=yy[valid];carrier[y[ok],x[ok]]=255;protected[y[~ok],x[~ok]]=255
 protected=cv2.erode(protected,np.ones((3,3),np.uint8))
 assert not np.any(changed&(protected>0)),('Unrelated hair surface changed',int(np.count_nonzero(changed&(protected>0))))
 assert not np.any(deprojection&(carrier==0))
 tx,ty,w,h=report['uv_tile'];allowed=deprojection.copy();allowed[ty:ty+h,tx:tx+w]=True
 assert not np.any(changed&~allowed)
 # Sample supporting hair along the badge's fitted normal. It is acceptable
 # for a back edge to sit slightly inside hair, but no pink/black front face
 # may disappear below the carrier surface.
 p=(old['positions']-a['center'])@basis.T
 def depth_at(q):
  nearest=-np.inf
  for face in old['indices'].reshape(-1,3)[(old['materials'][old['indices'].reshape(-1,3)[:,0]]==1)&~tmask]:
   xy=p[face,:2]
   if np.any(q<xy.min(0)) or np.any(q>xy.max(0)):continue
   m=np.column_stack([xy[0]-xy[2],xy[1]-xy[2]])
   if abs(np.linalg.det(m))<1e-10:continue
   b=np.linalg.solve(m,q-xy[2]);b=np.r_[b,1-b.sum()]
   if b.min()>=-1e-6:nearest=max(nearest,float(b@p[face,2]))
  return nearest
 gen=(d['positions'][ids[:count]]-a['center'])@basis.T
 # Pink panel ring and center, cross caps, pin caps.
 front_ids=list(range(216,288))+[288]
 gaps=[]
 for i in front_ids:
  support=depth_at(gen[i,:2])
  if np.isfinite(support):gaps.append(float(gen[i,2]-support))
 assert len(gaps)>50
 assert min(gaps)>.012,('Front badge penetrates its carrier hair',min(gaps))
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),source_face3_native_sha256=sha(FACE/'native/final-render.npz'),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),closed_solids=5,consistently_oriented_watertight_solids=True,new_vertices=count,new_triangles=num,inactive_degenerate_triangle_slots=len(slots)-num,all_non_accessory_positions_frames_uv_indices_exact=True,uv1_exact=True,unrelated_hair_changed_texels=0,carrier_deprojection_texels=int(deprojection.sum()),minimum_front_panel_hair_clearance_cm=min(gaps),game_runtime_tested=False))
 print('HAIRPIN_GEOMETRY_VERIFIED','final' if final else 'preflight','front clearance',min(gaps))

if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
