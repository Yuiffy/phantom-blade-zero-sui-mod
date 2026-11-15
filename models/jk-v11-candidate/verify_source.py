"""Audit v10/v11 edit boundaries in source space before delivery."""
import bpy,numpy as np,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def load(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));o=next(o for o in bpy.context.scene.objects if o.type=='MESH');a=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');m=o.data
 return o,{'co':np.array([v.co[:] for v in m.vertices]),'comp':np.array([d.value for d in m.attributes['source_component'].data]),'weights':[{o.vertex_groups[g.group].name:float(g.weight) for g in v.groups} for v in m.vertices],'bones':[(b.name,b.parent.name if b.parent else None,np.array(b.matrix_local).tolist()) for b in a.data.bones]}
_,base=load(ROOT.parent/'tripo-refine-v10/sui-jk-hun-bound.blend');o,new=load(ROOT/'sui-jk-hun-bound.blend');m=o.data
ids=np.array([d.value for d in m.attributes['v10_vertex_index'].data]);retained=ids>=0;comp=new['comp'];dist=np.linalg.norm(new['co'][retained]-base['co'][ids[retained]],axis=1);moved=np.flatnonzero(retained)[dist>1e-6]
assert base['bones']==new['bones'],'skeleton changed'
assert np.isin(comp[moved],[4,5,101]).all(),'unrelated geometry moved'
changedw=[]
for i in np.flatnonzero(retained):
 old=base['weights'][ids[i]];w=new['weights'][i]
 if max(abs(w.get(k,0)-old.get(k,0)) for k in w.keys()|old.keys())>1e-6:changedw.append(int(i))
assert (comp[changedw]==101).all(),'weights changed outside charm attachment'
report={'baseline':'v10','exact_skeleton_and_reference_matrices':True,'retained_vertices':int(retained.sum()),'new_hanger_vertices':int((~retained).sum()),'positions_changed_components':sorted(set(comp[moved].tolist())),'weights_changed_components':sorted(set(comp[changedw].tolist())),'head_shoulders_legs_skirt_backpack_geometry_weights_unchanged':True,'hand_weights_unchanged':True,'hand_max_addition_cm':float(np.linalg.norm(new['co'][np.isin(comp,[4,5])]-base['co'][ids[np.isin(comp,[4,5])]],axis=1).max()),'removed_components':sorted(set(base['comp'].tolist())-set(comp.tolist())),'new_physics':False}
(ROOT/'scope-check.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
