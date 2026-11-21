from pathlib import Path
import os

import numpy as np

WORK = Path(os.environ.get("SUI_HEM_WORK", ".")).resolve()
Y = 4.0
SAGITTAL = .735

def polar(points):
    scaled=points[:,:2].copy()
    scaled[:,1]=(scaled[:,1]-Y)/SAGITTAL
    return np.arctan2(scaled[:,1],scaled[:,0]),np.linalg.norm(scaled,axis=1)

def radial_slices(v,f,heights,angles):
    # Slice triangles with horizontal planes, then intersect each segment
    # with a ray in the plane. The largest radius is the visible shell.
    v=v.copy()
    v[:,1]=(v[:,1]-Y)/SAGITTAL
    tris=v[f]
    result=np.full((len(heights),len(angles)),np.nan)
    d=np.column_stack((np.cos(angles),np.sin(angles)))
    cross=lambda a,b:a[...,0]*b[...,1]-a[...,1]*b[...,0]
    for layer,z in enumerate(heights):
        row=tris[(z>tris[:,:,2].min(1))&(z<tris[:,:,2].max(1))]
        if not len(row):
            continue
        edges=np.stack([row, row[:,[1,2,0]]],axis=2)
        with np.errstate(divide="ignore",invalid="ignore"):
            t=(z-edges[:,:,0,2])/(edges[:,:,1,2]-edges[:,:,0,2])
        intersection=edges[:,:,0,:2]+np.where(np.isfinite(t),t,0)[:,:,None]*(edges[:,:,1,:2]-edges[:,:,0,:2])
        active=(t>0)&(t<1)
        assert np.all(active.sum(1)==2)
        a,b=intersection[active].reshape(-1,2,2).transpose(1,0,2)
        delta=b-a
        with np.errstate(divide="ignore",invalid="ignore"):
            distance=cross(a,delta)[None,:]/cross(d[:,None,:],delta[None,:,:])
            fraction=cross(a[None,:,:],d[:,None,:])/cross(d[:,None,:],delta[None,:,:])
        valid=(fraction>=0)&(fraction<=1)&(distance>4)&(distance<28)
        furthest=np.where(valid,distance,-np.inf).max(axis=1)
        result[layer]=np.where(np.isfinite(furthest),furthest,np.nan)
    return result

def main():
    vest=np.load(WORK/"vest.npz")
    d=vest["v"][vest["f"]]
    f=vest["f"][(abs(d[:,:,0]).max(1)<29)&(d[:,:,2].min(1)<136)]
    angles=np.linspace(-np.pi,np.pi,72,endpoint=False)
    z=np.arange(106.31,131,1.)
    r=radial_slices(vest["v"],f,z,angles)
    for height, row in zip(z,r):
        print(round(height,1), len(row[np.isfinite(row)]), np.round(row[::6],1))
if __name__=="__main__":
    main()
