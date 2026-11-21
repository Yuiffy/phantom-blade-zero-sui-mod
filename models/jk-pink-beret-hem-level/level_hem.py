"""Level the ribbing and spread the abrupt fold above it over the lower vest."""
from pathlib import Path
import json

import numpy as np
from scipy.interpolate import CubicSpline, RectBivariateSpline
from scipy.ndimage import gaussian_filter, gaussian_filter1d

from slices import WORK, Y, polar, radial_slices


def ease(a):
    t=np.clip(a,0,1)
    return t*t*(3-2*t)


class HemFit:
    def __init__(self, points, triangles):
        corners=points[triangles]
        local=(corners[:,:,2].min(1)<134)&(np.abs(corners[:,:,0]).max(1)<27)
        self.faces=triangles[local]
        self.angles=np.linspace(-np.pi,np.pi,160,endpoint=False)
        edge_levels=np.arange(104.913,111.9,.058)
        self.before_edge=self.bottom(points,edge_levels)
        observed=gaussian_filter1d(self.before_edge,2,mode="wrap")
        # A shallow front-to-back slope reads as fabric while the abrupt
        # angular steps where the sewn band meets the knit are leveled.
        target=107.34+.40*np.sin(self.angles)
        ext=np.r_[self.angles,np.pi]
        shift=target-observed
        self.edge_shift=CubicSpline(ext,np.r_[shift,shift[0]],bc_type="periodic")

        # Smooth a map of the outer surface in the direction around the
        # hem and up the garment. Apply the result to both sides of the shell.
        self.heights=np.arange(105.913,134,.23)
        r=radial_slices(points,self.faces,self.heights,self.angles)
        for i,row in enumerate(r.T):
            finite=np.flatnonzero(np.isfinite(row))
            assert len(finite)>=64
            r[:,i]=np.interp(self.heights,self.heights[finite],row[finite])
        filtered=gaussian_filter(r,[8.5,6],mode=("nearest","wrap"))
        residual=np.clip(filtered-r,-1.66,1.92)
        residual=gaussian_filter(residual,[2.6,2],mode=("nearest","wrap"))
        ext=np.r_[self.angles[-10:]-2*np.pi,self.angles,self.angles[:10]+2*np.pi]
        self.radius_shift=RectBivariateSpline(self.heights,ext,np.c_[residual[:,-10:],residual,residual[:,:10]])

    def bottom(self, points, heights):
        hit=radial_slices(points,self.faces,heights,self.angles)
        hit=np.isfinite(hit)&(hit>12.)
        assert hit.any(axis=0).all()
        return heights[np.argmax(hit,axis=0)]

    def transform(self, points):
        x,y,z=points.T
        angle,r=polar(points)
        torso=1-ease((np.abs(x)-22)/6)
        cloth=ease((r-7)/5)*torso
        lift=self.edge_shift(angle)*(1-ease((z-110.8)/12.5))*cloth
        band=(1-ease((z-119.5)/8.5))*cloth
        dy=self.radius_shift.ev(z,angle)*band*.94
        factor=(r+dy)/np.maximum(r,1e-8)
        return np.column_stack((x*factor,Y+(y-Y)*factor,z+lift))


def main():
    data=np.load(WORK/"vest.npz")
    before,triangles=data["v"],data["f"]
    fit=HemFit(before,triangles)
    after=fit.transform(before)
    jac=np.stack([(fit.transform(before+e)-fit.transform(before-e))/.012
                  for e in np.eye(3)*.006],axis=2)
    np.savez_compressed(WORK/"drape.npz",before=before,after=after,jac=jac)
    final_edge=fit.bottom(after,np.arange(104.923,111.9,.058))
    report={"hem_height_range_before_cm":float(np.ptp(fit.before_edge)),
            "hem_height_range_after_cm":float(np.ptp(final_edge)),
            "hem_height_step_before_cm":float(np.abs(np.diff(np.r_[fit.before_edge,fit.before_edge[0]])).max()),
            "hem_height_step_after_cm":float(np.abs(np.diff(np.r_[final_edge,final_edge[0]])).max())}
    (WORK/"height-review.json").write_text(json.dumps(report,indent=2),encoding="utf8")
    print(report)


if __name__=="__main__":
    main()
