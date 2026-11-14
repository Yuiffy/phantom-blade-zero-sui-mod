"""Export only v8 authored-model/UV provenance for deterministic atlas repair."""
import bpy,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(ROOT.parent/'tripo-refine-v8/sui-jk-hun-bound.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
np.savez_compressed(ROOT/'inspect-data.npz',co=np.array([v.co[:] for v in m.vertices]),faces=np.array([p.vertices[:] for p in m.polygons]),uv=np.array([d.uv[:] for d in m.uv_layers.active.data]).reshape(-1,3,2),comp=np.array([d.value for d in m.attributes['source_component'].data]),mi=np.array([p.material_index for p in m.polygons]))
