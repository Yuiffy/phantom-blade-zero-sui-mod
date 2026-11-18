"""Continuous local rest-shape edit in author Blender centimetres."""
import numpy as np

def smooth(x):
 t=np.clip(x,0,1);return t*t*(3-2*t)

def reshape(p,visible=True):
 q=p.copy();rad=p[:,:2]-[0,5];radius=np.linalg.norm(rad,axis=1)
 undo=4*smooth((122-p[:,2])/14) if visible else 0
 tuck=.9*smooth((114-p[:,2])/9)
 q[:,:2]-=rad/np.maximum(radius[:,None],1)*(undo+tuck)[:,None]
 q[:,2]-=1.5*smooth((113-p[:,2])/10)+2.2*smooth((np.abs(q[:,0])-18)/12)*smooth((117-p[:,2])/13)
 return q

def transformed_normals(p,n,visible=True):
 j=np.empty((len(p),3,3))
 for axis in range(3):
  d=np.zeros_like(p);d[:,axis]=.002
  j[:,:,axis]=(reshape(p+d,visible)-reshape(p-d,visible))/.004
 assert np.linalg.det(j).min()>.5,'Shape transform folds a volume'
 q=np.linalg.solve(j.transpose(0,2,1),n[...,None])[...,0]
 return q/np.linalg.norm(q,axis=1)[:,None]
