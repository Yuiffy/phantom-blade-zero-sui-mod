"""Raster actual half-float UV0, retaining source face and surface coordinates."""
import numpy as np,cv2

def samples(data,face_mask,size):
 p=data['positions'];uv=data['uv'][:,0].astype(float)*(size-1);tri=data['indices'].reshape(-1,3)
 rows=[]
 for i in np.flatnonzero(face_mask):
  t=tri[i];q=uv[t];lo=np.floor(q.min(0)).astype(int).clip(0,size-1);hi=np.ceil(q.max(0)).astype(int).clip(0,size-1)
  m=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(m))<1e-9:continue
  assert np.prod(hi-lo+1)<3000000,'Unexpected atlas-wide face'
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
  b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(m).T;b=np.dstack([b,1-b.sum(-1)]);valid=(b>=-1e-6).all(-1)
  if not valid.any():continue
  bary=b[valid];xyz=bary@p[t];normal=bary@data['normals'][t]
  rows.append((xx[valid],yy[valid],xyz,normal,np.full(valid.sum(),i)))
 if not rows:return None
 return [np.concatenate([r[k] for r in rows]) for k in range(5)]

def ownership(data,face_mask,size):
 out=np.zeros((size,size),np.uint8);tri=data['indices'].reshape(-1,3);uv=data['uv'][:,0].astype(float)*(size-1)
 for t in tri[face_mask]:cv2.fillConvexPoly(out,np.rint(uv[t]).astype('i4'),255)
 return out

def line_distance(xy,points):
 distance=np.full(len(xy),np.inf)
 for a,b in zip(points[:-1],points[1:]):
  a=np.array(a);ab=np.array(b)-a;t=np.clip(((xy-a)*ab).sum(1)/max(1e-12,ab@ab),0,1);distance=np.minimum(distance,np.linalg.norm(xy-a-t[:,None]*ab,axis=1))
 return distance

def stroke(xy,points,width,soft=.012):return np.clip((width/2+soft-line_distance(xy,points))/(2*soft),0,1)
