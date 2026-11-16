import bpy, json
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=r"D:/workspace/myrepo/phantom-blade-zero-sui-mod/models/jk-v6-candidate/sui-jk-hun-bound.blend")
sc=bpy.context.scene
ob=next(o for o in sc.objects if o.type=='MESH')
mw=ob.matrix_world
me=ob.data
print("mesh",ob.name,"verts",len(me.vertices),"polys",len(me.polygons),"mats",[m.name if m else None for m in me.materials])
print("vgroups",len(ob.vertex_groups))
# material -> vertex set via polygons
matverts={}
for p in me.polygons:
    matverts.setdefault(p.material_index,set()).update(p.vertices)
rep={"materials":{},"slices":{}}
for mi,vs in sorted(matverts.items()):
    cos=[mw@me.vertices[i].co for i in vs]
    xs=[c.x for c in cos]; ys=[c.y for c in cos]; zs=[c.z for c in cos]
    name=me.materials[mi].name if me.materials[mi] else str(mi)
    rep["materials"][f"{mi}:{name}"]={"nverts":len(vs),"x":[round(min(xs),2),round(max(xs),2)],
        "y":[round(min(ys),2),round(max(ys),2)],"z":[round(min(zs),2),round(max(zs),2)]}
    print(f"mat {mi} {name:28s} n={len(vs):6d} x[{min(xs):7.2f},{max(xs):7.2f}] y[{min(ys):7.2f},{max(ys):7.2f}] z[{min(zs):7.2f},{max(zs):7.2f}]")
# global slices of width by z
allco=[mw@v.co for v in me.vertices]
zs=sorted(c.z for c in allco)
print("z min/max",round(zs[0],2),round(zs[-1],2))
import collections
bands=collections.defaultdict(list)
for c in allco:
    bands[round(c.z)].append(c)
rows=[]
for z in sorted(bands):
    cs=bands[z]
    xs=[c.x for c in cs]
    rows.append((z,len(cs),round(min(xs),2),round(max(xs),2),round(max(abs(min(xs)),abs(max(xs))),2)))
print("z  nverts  xmin  xmax  halfwidth")
for r in rows:
    if r[0]%2==0 and (180>r[0]>60 or 30<r[0]<60):
        print(f"{r[0]:6d} {r[1]:5d} {r[2]:7.2f} {r[3]:7.2f} {r[4]:7.2f}")
rep["slices"]={str(r[0]):r[1:] for r in rows}
(OUT/"measure-v6.json").write_text(json.dumps(rep,indent=2,ensure_ascii=False),encoding="utf8")
