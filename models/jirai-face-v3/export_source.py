from pathlib import Path
import bpy,numpy as np
R=Path(__file__).resolve().parents[2];W=R/'private/jirai-face-v3'
bpy.ops.wm.open_mainfile(filepath=str(R/'private/skin-eyes-v1/sui-jirai-motion.blend'))
m=next(x.data for x in bpy.context.scene.objects if x.type=='MESH')
np.savez_compressed(W/'source-uv.npz',positions=np.array([v.co[:] for v in m.vertices]),
    uv=np.array([v.uv[:] for v in m.uv_layers.active.data]),loop_vertices=np.array([v.vertex_index for v in m.loops]))
print('FACE3_SOURCE_UV_EXPORTED')
