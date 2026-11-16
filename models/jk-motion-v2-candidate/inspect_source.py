import bpy,numpy as np,json
from pathlib import Path
R=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(R.with_name('tripo-motion-v1')/'sui-jk-motion-source.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');m=o.data
co=np.array([v.co[:] for v in m.vertices]);comp=np.array([d.value for d in m.attributes['source_component'].data]);mi=np.array([p.material_index for p in m.polygons])
uv=np.array([d.uv[:] for d in m.uv_layers.active.data]).reshape(-1,3,2)
faces=np.array([p.vertices[:] for p in m.polygons]);norm=np.array([v.normal[:] for v in m.vertices])
np.savez_compressed(R/'surface.npz',co=co,comp=comp,faces=faces,uv=uv,mi=mi,norm=norm)
report={'components':{int(c):{'vertices':int((comp==c).sum()),'min':co[comp==c].min(axis=0).tolist(),'max':co[comp==c].max(axis=0).tolist(),'materials':list(map(int,np.unique(mi[np.isin(faces[:,0],np.flatnonzero(comp==c))])))} for c in np.unique(comp)},'materials':[mat.name for mat in m.materials],'images':[{'name':im.name,'path':im.filepath,'size':list(im.size)} for im in bpy.data.images]}
(R/'inspect.json').write_text(json.dumps(report,indent=2))
print('INSPECT_OK',flush=True)
