from pathlib import Path
import os
import bpy
import numpy as np
w=Path(os.environ.get("SUI_HEM_WORK", ".")).resolve()
vest=bpy.data.objects["Fitted pink JK vest"]
for name, obj, selection in [("vest",vest,None),("layers",bpy.data.objects["GuYou hands, skirt and neckline"],
                                            {"MI_JK_PleatedSkirt","MI_JK_SafetyLining"})]:
    obj.data.calc_loop_triangles()
    v=np.array([i.co[:] for i in obj.data.vertices])
    tri=[t for t in obj.data.loop_triangles if selection is None or obj.data.materials[t.material_index].name in selection]
    f=np.array([t.vertices[:] for t in tri])
    uv=np.array([[obj.data.uv_layers.active.data[l].uv[:] for l in t.loops] for t in tri])
    slots=np.array([obj.data.materials[t.material_index].name for t in tri])
    np.savez_compressed(w/f"{name}.npz",v=v,f=f,uv=uv,slots=slots)
