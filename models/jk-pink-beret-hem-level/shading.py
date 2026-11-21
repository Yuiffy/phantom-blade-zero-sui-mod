"""Use a continuous shading normal across the lower ribbing contour."""
from pathlib import Path
import numpy as np
from scipy.interpolate import RectBivariateSpline
from scipy.ndimage import gaussian_filter

from level_hem import ease
from slices import WORK,Y,SAGITTAL,polar,radial_slices


def main():
    vest=np.load(WORK/"vest.npz")
    edit=np.load(WORK/"drape.npz")
    p=edit["after"]
    q=p[vest["f"]]
    faces=vest["f"][(q[:,:,2].min(1)<133)&(abs(q[:,:,0]).max(1)<26)]
    angles=np.linspace(-np.pi,np.pi,160,endpoint=False)
    heights=np.arange(106.837,131,.22)
    radial=radial_slices(p,faces,heights,angles)
    for col in radial.T:
        valid=np.isfinite(col)
        assert np.count_nonzero(valid)>80
        col[:]=np.interp(heights,heights[valid],col[valid])
    # Smooth the sampled surface before deriving its slope to keep the coarse
    # triangle edges and formerly baked pinch from sharpening the highlights.
    radius=gaussian_filter(radial,[5.9,5.0],mode=("nearest","wrap"))
    padded=np.r_[angles[-10:]-2*np.pi,angles,angles[:10]+2*np.pi]
    curve=RectBivariateSpline(heights,padded,np.c_[radius[:,-10:],radius,radius[:,:10]])
    x,y,z=p.T
    phi,r=polar(p)
    zz=np.clip(z,heights[0],heights[-1])
    average=curve.ev(zz,phi)
    circumferential=curve.ev(zz,phi,dy=1)
    vertical=curve.ev(zz,phi,dx=1)
    c,s=np.cos(phi),np.sin(phi)
    tangent=np.column_stack((circumferential*c-average*s,
                             (circumferential*s+average*c)*SAGITTAL,np.zeros(len(p))))
    height=np.column_stack((vertical*c,vertical*s*SAGITTAL,np.ones(len(p))))
    normal=np.cross(tangent,height)
    normal/=np.linalg.norm(normal,axis=1,keepdims=True)
    fit=.74*ease((r-11)/4)*(1-ease((z-117.5)/6.1))
    # Preserve the shading of the rolled underside.
    fit*=ease((z-107.1)/.8)
    fit*=1-ease((abs(x)-22)/5)
    fit[np.linalg.norm(edit["after"]-edit["before"],axis=1)<=1e-6]=0
    np.savez_compressed(WORK/"shading.npz",normal=normal,weight=fit)


if __name__=="__main__":
    main()
