import bpy,bmesh,json
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[2]/'private/jirai-proportion-v1';OUT=R/'diagnostic'
bpy.ops.wm.open_mainfile(filepath=r'D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui/models/new-outfit-20261114/tripo-motion-v4/sui-jk-motion-source.blend')
o=next(x for x in bpy.context.scene.objects if x.type=='MESH');a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE');m=o.data
bm=bmesh.new();bm.from_mesh(m);c=bm.verts.layers.int['source_component'];bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[c] not in [4,5]],context='VERTS')
names=[g.name for g in o.vertex_groups];dg=bm.verts.layers.deform.active;uv=bm.loops.layers.uv.active
bm.verts.ensure_lookup_table();bm.verts.index_update()
co=np.array([v.co[:] for v in bm.verts]);faces=[[v.index for v in f.verts] for f in bm.faces]
weights=[{names[i]:w for i,w in v[dg].items()} for v in bm.verts]
loops=[]
for side in ['l','r']:
 wrist=a.data.bones['hand_'+side].head_local;axis=(a.data.bones['middle_01_'+side].head_local-wrist).normalized()
 selected=[v for v in bm.verts if (v.co.x>0)==(side=='l')];bd=[v for v in selected if any(e.is_boundary for e in v.link_edges)]
 loops.append({'side':side,'vertices':len(selected),'boundary_vertices':len(bd),'boundary_projection':[min((v.co-wrist).dot(axis) for v in bd),max((v.co-wrist).dot(axis) for v in bd)],'projection':[min((v.co-wrist).dot(axis) for v in selected),max((v.co-wrist).dot(axis) for v in selected)]})
data={'positions':co.tolist(),'faces':faces,'uv':[[list(l[uv].uv) for l in f.loops] for f in bm.faces],'weights':weights,'boundaries':loops,'bones':{b.name:list(b.head_local) for b in a.data.bones}}
(OUT/'jk-hands.json').write_text(json.dumps(data))
print('JK_HANDS',json.dumps(loops))
