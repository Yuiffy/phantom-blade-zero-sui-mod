import bpy, math
import numpy as np
from pathlib import Path
import bmesh
for tag,path in [('v6','../jk-v6-candidate/sui-jk-hun-bound.blend'),('v7','sui-jk-hun-bound-v7.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).resolve().parent/path))
    ob=next(o for o in bpy.context.scene.objects if o.type=='MESH');me=ob.data
    comp=np.array([me.attributes['source_component'].data[i].value for i in range(len(me.vertices))])
    bm=bmesh.new();bm.from_mesh(me)
    ring={}
    for e in bm.edges:
        if e.is_boundary:
            for v in e.verts:
                i=v.index
                if comp[i]!=0: continue
                if not (95<v.co.z<118): continue
                if abs(v.co.x)>30: continue
                az=int(round(math.degrees(math.atan2(v.co.x,v.co.y-5.1454))/10))*10
                ring.setdefault(az,[]).append(v.co.z)
    print(f"--- {tag} hem boundary ring z by azimuth ---")
    print("   "+" ".join(f"{a:5d}" for a in sorted(ring)))
    print("   "+" ".join(f"{min(ring[a]):5.1f}" for a in sorted(ring)))
    print("   skirt top (max z of comp10):",round(max(v.co.z for v in bm.verts if comp[v.index]==10),1))
    bm.free()
