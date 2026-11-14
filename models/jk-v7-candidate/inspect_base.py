import bpy, json, math
from mathutils import Vector
from pathlib import Path
OUT=Path(__file__).resolve().parent
BLEND=r"D:/workspace/myrepo/phantom-blade-zero-sui-mod/models/jk-v6-candidate/sui-jk-hun-bound.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND)
sc=bpy.context.scene
rep={"objects":[],"bones":{},"mesh":{}}
for o in sc.objects:
    rep["objects"].append({"name":o.name,"type":o.type,"parent":o.parent.name if o.parent else None,
        "loc":[round(v,4) for v in o.location],"scale":[round(v,4) for v in o.scale]})
arm=next(o for o in sc.objects if o.type=='ARMATURE')
print("ARMATURE",arm.name,"bones",len(arm.data.bones))
want=["Root","Pelvis","Spine","Spine1","Spine2","Spine3","Neck","Neck1","Head","Head1",
      "Clavicle_L","Clavicle_R","UpperArm_L","UpperArm_R","LowerArm_L","LowerArm_R",
      "Thigh_L","Thigh_R","UpperLeg_L","UpperLeg_R"]
for b in arm.data.bones:
    h=arm.matrix_world@b.head_local; t=arm.matrix_world@b.tail_local
    if any(w.lower() in b.name.lower() for w in ["clavicle","neck","head","spine","pelvis","upperarm","shoulder","root","thigh","upleg"]):
        rep["bones"][b.name]={"head":[round(v,3) for v in h],"tail":[round(v,3) for v in t],
            "len":round(b.length,3),"parent":b.parent.name if b.parent else None}
me=None
for o in sc.objects:
    if o.type=='MESH':
        me=o
        break
if me:
    me_eval=me
    d=me.data
    rep["mesh"]={"name":me.name,"verts":len(d.vertices),"polys":len(d.polygons),
                 "vgroups":len(me.vertex_groups),"modifiers":[m.type for m in me.modifiers],
                 "dims":[round(v,3) for v in me.dimensions],
                 "bbox_min":[round(v,3) for v in me.bound_box[0]],
                 "matrix_world":[[round(v,4) for v in r] for r in me.matrix_world]}
    # world-space bbox
    cos=[me.matrix_world@Vector(c) for c in me.bound_box]
    mn=[min(c[i] for c in cos) for i in range(3)]; mx=[max(c[i] for c in cos) for i in range(3)]
    rep["mesh"]["world_min"]=[round(v,3) for v in mn]; rep["mesh"]["world_max"]=[round(v,3) for v in mx]
    print("MESH world bbox",[round(v,2) for v in mn],[round(v,2) for v in mx])
(OUT/"inspect-base.json").write_text(json.dumps(rep,indent=2,ensure_ascii=False),encoding="utf8")
print("bones_total",len(arm.data.bones))
for k,v in rep["bones"].items(): print(k,v["head"],"len",v["len"],"parent",v["parent"])
