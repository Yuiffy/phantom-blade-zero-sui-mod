import bpy, math
import numpy as np
from pathlib import Path
for tag,path in [('v6','../jk-v6-candidate/sui-jk-hun-bound.blend'),('v7','sui-jk-hun-bound-v7.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent/path))
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');me=ob.data
    co=np.array([v.co[:] for v in me.vertices]);comp=np.array([me.attributes['source_component'].data[i].value for i in range(len(co))])
    print(f"--- {tag} jacket hem profile (per 30 deg bin) ---")
    sel=(comp==0)&(np.abs(co[:,2]-110)<30)&(np.abs(co[:,0])<29)&(co[:,2]>90)&(co[:,2]<125)
    idx=np.flatnonzero(sel)
    ang=np.degrees(np.arctan2(co[idx,0],co[idx,1]-5.1454))
    for a0 in range(-180,180,30):
        m=(ang>=a0)&(ang<a0+30)
        if m.sum()<5: continue
        zz=co[idx[m],2]
        # skirt tops in same bin
        sk=comp==10
        skm=sk&(np.abs(np.degrees(np.arctan2(co[:,0],co[:,1]-5.1454))-a0-15)<15)&(co[:,2]>100)
        print(f"  az {a0:4d}..{a0+30:4d}: jacket_zmin={zz.min():6.2f} p5={np.percentile(zz,5):6.2f} | skirt_zmax={co[skm,2].max() if skm.sum() else float('nan'):6.2f}")
