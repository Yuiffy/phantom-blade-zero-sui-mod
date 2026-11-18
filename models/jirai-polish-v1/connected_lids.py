"""Replace orbital fragments with a patch sharing the real head boundary."""
import numpy as np, collections
from shapely import Polygon, constrained_delaunay_triangles
from scipy.interpolate import RBFInterpolator
from common import unit

def rebuild(d,components,p,frames,tri,copies,eye):
 mat=d['materials'];skin=mat[tri[:,0]]==0;reference=p.copy()
 lower=np.isin(components,[125,126,128,136])
 cut=lower[tri].all(1);mean=reference[tri].mean(1)
 for cx in [-5.317217,4.614422]:
  radial=((mean[:,0]-cx)/4.4)**2+((mean[:,2]-177.95)/2.9)**2
  cut|=skin&(radial<1)&(reference[tri,1].max(1)>-3.0)
 # Discard detached remnants of old lash tabs, while retaining eyebrows,
 # the connected head, mouth, arms and every non-Skin section.
 up,weld=np.unique(np.round(reference,4),axis=0,return_inverse=True)
 parent=np.arange(len(up))
 def root(k):
  while parent[k]!=k:parent[k]=parent[parent[k]];k=parent[k]
  return k
 for f in weld[tri[skin&~cut]]:
  a=root(f[0])
  for b in f[1:]:parent[root(b)]=a
 groups=collections.defaultdict(list)
 for i in np.where(skin&~cut)[0]:groups[root(weld[tri[i,0]])].append(i)
 for part in groups.values():
  q=reference[np.unique(tri[part])]
  if len(part)<100 and q[:,2].min()>174 and q[:,2].max()<180.5 and abs(q[:,0].mean())>1:
   cut[part]=True
 retained=tri[skin&~cut];tt=weld[retained]
 good=(tt[:,0]!=tt[:,1])&(tt[:,0]!=tt[:,2])&(tt[:,1]!=tt[:,2]);tt=tt[good];retained=retained[good]
 directed=collections.defaultdict(list);representatives={}
 for f,ff in zip(retained,tt):
  for a,b in zip(f,ff):representatives.setdefault(int(b),int(a))
  for a,b in zip(ff,np.roll(ff,-1)):directed[tuple(sorted((int(a),int(b))))].append((int(a),int(b)))
 graph=collections.defaultdict(set)
 for edge,arrows in directed.items():
  if len(arrows)==1:
   a,b=edge;graph[a].add(b);graph[b].add(a)
 seen=set();loops=[]
 for k in graph:
  if k in seen:continue
  todo=[k];part=[]
  while todo:
   a=todo.pop()
   if a in seen:continue
   seen.add(a);part.append(a);todo.extend(graph[a]-seen)
  q=up[part]
  if not (len(part)>20 and q[:,2].min()>173 and q[:,2].max()<181.5 and q[:,1].max()>3):continue
  assert all(len(graph[a])==2 for a in part)
  order=[k];prev=-1;cur=k
  while True:
   nxt=next(x for x in sorted(graph[cur]) if x!=prev)
   if nxt==k:break
   order.append(nxt);prev,cur=cur,nxt
   assert len(order)<=len(part)
  assert len(order)==len(part)
  loops.append(np.array([representatives[a] for a in order]))
 assert len(loops)==2,[len(x) for x in loops]
 active=np.zeros(len(p),bool);active[tri[~cut].ravel()]=True
 free=np.where((mat==0)&~active)[0];cursor=0;used=[];faces=[];seams=[]
 head=int(np.where((mat==0)&(components==0)&(reference[:,2]>183)&(reference[:,2]<184))[0][0])
 original=d['indices'].reshape(-1,3)
 near=original[np.isin(mat[original[:,0]],[18,19])];pp=reference[near];xz=pp[:,:,[0,2]]
 matrix=np.stack([xz[:,0]-xz[:,2],xz[:,1]-xz[:,2]],-1);valid=abs(np.linalg.det(matrix))>1e-9
 pp=pp[valid];xz=xz[valid];inverse=np.linalg.inv(matrix[valid])
 def eye_depth(x,z):
  bary=np.einsum('nij,nj->ni',inverse,np.array([x,z])-xz[:,2]);bary=np.c_[bary,1-bary.sum(1)]
  ok=(bary>=-1e-6).all(1)
  if not ok.any():return None
  depth=(bary[:,:,None]*pp).sum(1)[:,1];return depth[ok].max()+.15
 def allocate(q):
  nonlocal cursor
  idx=int(free[cursor]);cursor+=1;used.append(idx);p[idx]=q;copies.append((idx,head));eye[idx]=True
  return idx
 for outer in loops:
  cx=-5.317217 if reference[outer,0].mean()<0 else 4.614422
  theta=np.arange(48)*2*np.pi/48;dx=2.55*np.cos(theta)
  zz=177.95+np.where(np.sin(theta)>=0,1.,.90)*np.sin(theta)+.075*dx*(-1 if cx<0 else 1)
  inner=np.array([allocate([cx+x,eye_depth(cx+x,z),z]) for x,z in zip(dx,zz)])
  coords=p[np.r_[outer,inner]][:,[0,2]].astype(float);ids=np.r_[outer,inner]
  poly=Polygon(coords[:len(outer)],holes=[coords[len(outer):]])
  assert poly.is_valid and poly.area>0
  lookup={tuple(x):int(i) for x,i in zip(coords,ids)}
  base=[]
  for cell in constrained_delaunay_triangles(poly).geoms:
   base.append([lookup[tuple(x)] for x in np.array(cell.exterior.coords)[:3]])
  # Thin plate interpolation supplies a continuous curved surface between the
  # closed eye and exact head seam. Split each cell for geometric curvature.
  rbf=RBFInterpolator(coords,p[ids,1].astype(float),kernel='thin_plate_spline',smoothing=0)
  def surface_y(xz):
   return rbf(xz)
  patch=base
  for level in range(2):
   refined=[]
   for face in patch:
    q=p[face].mean(0);q[1]=float(surface_y(q[[0,2]][None])[0]);center=allocate(q)
    refined.extend([[face[0],face[1],center],[face[1],face[2],center],[face[2],face[0],center]])
   patch=refined
  patch=np.array(patch)
  # Match the original head's edge direction instead of assuming handedness.
  a,b=outer[:2];existing=directed[tuple(sorted((int(weld[a]),int(weld[b]))))][0]
  candidate=next((u,v) for f in patch for u,v in zip(f,np.roll(f,-1)) if {int(u),int(v)}=={int(a),int(b)})
  if (candidate==(a,b))==(existing==(weld[a],weld[b])):patch=patch[:,[0,2,1]]
  faces.extend(patch.tolist());seams.extend(zip(outer.tolist(),np.roll(outer,-1).tolist()))
  new=np.setdiff1d(np.unique(patch),outer);xy=p[new][:,[0,2]].astype(float)
  inner_normal=unit(np.c_[.12*(p[inner,0]-cx),np.ones(len(inner)),.18*(p[inner,2]-177.95)])
  seam_normal=frames[outer,4:7].view('i1').astype(float)/127
  normal_field=RBFInterpolator(coords,np.r_[seam_normal,inner_normal],kernel='thin_plate_spline',smoothing=0)
  normals=unit(normal_field(xy));tangent=unit(np.array([1.,0,0])-normals*normals[:,0,None])
  frames[new,4:7]=np.rint(normals*127).astype('i1').view('u1');frames[new,:3]=np.rint(tangent*127).astype('i1').view('u1')
 slots=np.where(cut)[0];faces=np.array(faces);assert len(faces)<=len(slots) and cursor<=len(free)
 tri[slots[:len(faces)]]=faces;tri[slots[len(faces):]]=free[-1]
 # Relax depth through the surrounding original orbital skin as well as the
 # replacement. The source has deep zigzags at the cut boundary; keeping those
 # coordinates rigid would transfer sharp folds into an otherwise welded lid.
 _,first,iv=np.unique(np.round(p,4),axis=0,return_index=True,return_inverse=True)
 wp=p[first].astype(float);wt=iv[tri[mat[tri[:,0]]==0]]
 wt=wt[(wt[:,0]!=wt[:,1])&(wt[:,1]!=wt[:,2])&(wt[:,0]!=wt[:,2])]
 edges=np.concatenate([wt[:,[0,1]],wt[:,[1,2]],wt[:,[2,0]]]);edges.sort(1);edges=np.unique(edges,axis=0)
 aa=np.r_[edges[:,0],edges[:,1]];bb=np.r_[edges[:,1],edges[:,0]]
 degree=np.bincount(aa,minlength=len(wp));amount=np.zeros(len(wp))
 for cx in [-5.317217,4.614422]:
  radial=np.sqrt(((wp[:,0]-cx)/4.9)**2+((wp[:,2]-177.95)/4.)**2)
  inner=np.sqrt(((wp[:,0]-cx)/2.55)**2+((wp[:,2]-177.95)/.95)**2)
  blend=np.clip((1-radial)/.25,0,1)*np.clip((inner-1.15)/.4,0,1)
  amount=np.maximum(amount,blend)
 amount*=((wp[:,1]>-5.5)&(wp[:,2]>173)&(wp[:,2]<182.5)&(degree>0))
 for step in range(100):
  average=np.bincount(aa,weights=wp[bb,1],minlength=len(wp))/np.maximum(degree,1)
  wp[:,1]+=.45*amount*(average-wp[:,1])
 affected=(mat==0)&(amount[iv]>0);p[affected,1]=wp[iv[affected],1];eye[affected]=True
 # Derive a continuous normal across all welded skin seams in the relaxed
 # region, using the source winding (the native front normal is -cross).
 cross=-np.cross(wp[wt[:,1]]-wp[wt[:,0]],wp[wt[:,2]]-wp[wt[:,0]])
 accum=np.zeros_like(wp)
 for column in range(3):np.add.at(accum,wt[:,column],cross)
 normal=unit(accum[iv[affected]]);oldnormal=frames[affected,4:7].view('i1').astype(float)/127
 blend=amount[iv[affected],None];normal=unit(oldnormal*(1-blend)+normal*blend)
 tangent=unit(np.array([1.,0,0])-normal*normal[:,0,None])
 frames[affected,4:7]=np.rint(normal*127).astype('i1').view('u1');frames[affected,:3]=np.rint(tangent*127).astype('i1').view('u1')
 return np.array(used),slots,faces,used,seams
