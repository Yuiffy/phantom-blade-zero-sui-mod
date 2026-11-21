"""Repaint the two ribbing stripes along the leveled garment edge."""
from pathlib import Path
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt
from scipy.interpolate import CubicSpline
from scipy.ndimage import gaussian_filter1d

from level_hem import HemFit, ease
from slices import WORK, polar
from raster import raster_surface, uv_footprint


def main():
    vest=np.load(WORK/"vest.npz")
    edit=np.load(WORK/"drape.npz")
    occupied=np.load(WORK/"top.npz")
    atlas=WORK/"source-albedo.png"
    original=np.array(Image.open(atlas).convert("RGB"))
    half=(4096,4096)
    v,f,uv=edit["after"],vest["f"],vest["uv"]
    q=v[f]
    lower=(q[:,:,2].min(1)<119)&(abs(q[:,:,0]).max(1)<24)
    to_pixels=lambda uv:uv*[8192,-4096]+[-.5,4095.5]
    index,xyz=raster_surface(to_pixels(uv[lower]),f[lower],v,half)
    other=uv_footprint(to_pixels(np.concatenate([uv[~lower],occupied["other_uv"]])),half)
    y,x=np.nonzero((index>=0)&~other)
    p=xyz[y,x].astype(float)
    phi,r=polar(p)
    fit=HemFit(edit["before"],f)
    edge=fit.bottom(v,np.arange(104.923,111.9,.058))
    edge=gaussian_filter1d(edge,2.2,mode="wrap")
    edge_height=CubicSpline(np.r_[fit.angles,np.pi],np.r_[edge,edge[0]],bc_type="periodic")
    t=p[:,2]-edge_height(phi)
    pixels=original[y,x].astype(float)
    luma=pixels@[.2126,.7152,.0722]
    # Keep the vest's gray weave. Straighten the two pale stripes by setting
    # their height from the hem rather than from the original warped UVs.
    worn=(t>-.43)&(t<8.05)&(r>12)
    bounds=(t>=.15)&(t<=5.8)&(r>13)
    dark=(luma>41)&(luma<133)
    rgb=np.median(pixels[bounds&dark],axis=0)
    bright=np.median(pixels[bounds&(luma>152)],axis=0)
    print("COLOR SAMPLES",rgb,bright,len(x))
    assert np.isfinite(bright).all()
    base=np.clip(luma-rgb@[.2126,.7152,.0722],-18,19)*.31
    rib=3.2*np.cos(121*phi)+1.20*np.cos(242*phi)
    satin=np.cos(2*np.pi*t/.67+np.cos(121*phi)*.22)
    def stripe(center):
        return 1-ease((abs(t-center)-.42)/.19)
    bars=np.maximum(stripe(1.97),stripe(4.08))
    new=rgb+base[:,None]+rib[:,None]+satin[:,None]*.75
    new+=(bright-rgb)[None,:]*bars[:,None]
    # Suppress any fragment of a former white stripe between the new bands
    # and blend the gray into the upper sweater.
    coverage=(1-ease((t-5.0)/1.55))*ease((r-11.1)/2)
    old_bars=ease((luma-112)/40)*(1-ease((t-5.9)/1.9))
    weight=np.maximum(coverage,old_bars*.96)*worn
    final=np.rint(np.clip(pixels*(1-weight[:,None])+new*weight[:,None],0,255)).astype(np.uint8)
    changed=np.any(final!=pixels,axis=1)
    mask=np.zeros(half,bool)
    mask[y[changed],x[changed]]=True
    original[y[changed],x[changed]]=final[changed]
    full=other|uv_footprint(to_pixels(uv),half)
    distance,nearest=distance_transform_edt(~mask,return_indices=True)
    gutter=~full&(distance<=5)
    original[:,:4096][gutter]=original[nearest[0][gutter],nearest[1][gutter]]
    Image.fromarray(original).save(WORK/"PinkBeret_Final.png")
    print("REPAINTED",int(mask.sum()),"GUTTER",int(gutter.sum()))


if __name__=="__main__":
    main()
