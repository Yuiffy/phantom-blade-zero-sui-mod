"""Trim only the independent safety-short hem; retain original leg and cloth data."""
from pathlib import Path
import bpy, numpy as np, json, hashlib, math
from mathutils import Vector

R=Path(__file__).resolve().parent
W=R.parents[2]/'variants/jk-motion-v4'
BASE=R.with_name('tripo-motion-v2')
CUT=100.0
# Keep the outer hem short, but retain the lower central bridge between thighs.
def hem_z(p):return 98.0
def height(p):return float(p[2])-hem_z(p)
print('OPEN_SOURCE',flush=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE/'sui-jk-motion-source.blend'))
print('SOURCE_OPEN',flush=True)
o=next(x for x in bpy.context.scene.objects if x.type=='MESH')
a=next(x for x in bpy.context.scene.objects if x.type=='ARMATURE')
m=o.data
group_names=[g.name for g in o.vertex_groups]
co=[list(v.co) for v in m.vertices]
weights=[{g.group:g.weight for g in v.groups} for v in m.vertices]
comp=[d.value for d in m.attributes['source_component'].data]
pointattrs={at.name:(at.data_type,[d.value for d in at.data]) for at in m.attributes
            if at.domain=='POINT' and at.data_type in {'INT','FLOAT','BOOLEAN'} and not at.name.startswith('.')}
uvs={uv.name:[list(d.uv) for d in uv.data] for uv in m.uv_layers}
norms=[np.array(d.vector[:],dtype=float) for d in m.corner_normals]
lin=next(i for i,x in enumerate(m.materials) if x.name=='MI_JK_SafetyLining')
assert set(comp[v] for p in m.polygons if p.material_index==lin for v in p.vertices)=={1001}
before_faces=len(m.polygons)
before_lining=sum(p.material_index==lin for p in m.polygons)
old_min=min(co[v][2] for p in m.polygons if p.material_index==lin for v in p.vertices)
newfaces=[];facemats=[];smooth=[];newuvs={k:[] for k in uvs};newnorms=[];edges={}

def cross(prev,cur):
    i,j=prev[0],cur[0]
    hi,hj=height(co[i]),height(co[j])
    t=hi/(hi-hj)
    if t<=1e-9:return prev
    if t>=1-1e-9:return cur
    key=tuple(sorted((i,j)))
    if key not in edges:
        ix=len(co);edges[key]=ix
        co.append((np.array(co[i])*(1-t)+np.array(co[j])*t).tolist())
        ws={g:weights[i].get(g,0)*(1-t)+weights[j].get(g,0)*t for g in weights[i].keys()|weights[j].keys()}
        total=sum(ws.values());assert total>0
        weights.append({g:v/total for g,v in ws.items() if v>0})
        comp.append(1001)
        for name,(typ,vals) in pointattrs.items():
            if typ=='FLOAT':v=vals[i]*(1-t)+vals[j]*t
            else:v=vals[i] if vals[i]==vals[j] else (-1 if typ=='INT' else False)
            vals.append(v)
    n=prev[2]*(1-t)+cur[2]*t;n/=max(np.linalg.norm(n),1e-12)
    return (edges[key],{k:prev[1][k]*(1-t)+cur[1][k]*t for k in uvs},n)

for p in m.polygons:
    assert len(p.vertices)==3
    corners=[(l.vertex_index,{k:np.array(uvs[k][l.index]) for k in uvs},norms[l.index]) for l in (m.loops[i] for i in p.loop_indices)]
    if p.material_index==lin:
        clipped=[]
        for j,cur in enumerate(corners):
            prev=corners[j-1];pin=height(co[prev[0]])>=0;cin=height(co[cur[0]])>=0
            if cin:
                if not pin:clipped.append(cross(prev,cur))
                clipped.append(cur)
            elif pin:clipped.append(cross(prev,cur))
        corners=clipped
    for j in range(1,len(corners)-1):
        tri=[corners[0],corners[j],corners[j+1]]
        if len(set(x[0] for x in tri))!=3:continue
        q=np.array([co[x[0]] for x in tri])
        if p.material_index==lin and np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-8:continue
        newfaces.append([x[0] for x in tri]);facemats.append(p.material_index);smooth.append(p.use_smooth)
        newnorms.extend(x[2] for x in tri)
        for k in uvs:newuvs[k].extend(x[1][k] for x in tri)

used=sorted({v for f in newfaces for v in f});remap={old:new for new,old in enumerate(used)}
new=bpy.data.meshes.new('Sui_JK_ContinuousLining_Motion_v4')
new.from_pydata([co[i] for i in used],[],[[remap[v] for v in f] for f in newfaces])
for mat in m.materials:new.materials.append(mat)
backup_faces=0
for p,mi,sm in zip(new.polygons,facemats,smooth):
    p.material_index=mi;p.use_smooth=sm
    # Opaque fallback on the underlying skin uses the same exact weights, so
    # tiny shell/skin differences during animation cannot reveal skin here.
    if all(comp[used[i]]==1 for i in p.vertices) and all(height(co[used[i]])>.7 for i in p.vertices):
        p.material_index=lin;backup_faces+=1
for name,values in newuvs.items():
    uv=new.uv_layers.new(name=name);uv.data.foreach_set('uv',np.asarray(values,dtype='f4').ravel())
for name,(typ,vals) in pointattrs.items():
    at=new.attributes.new(name,typ,'POINT')
    for d,i in zip(at.data,used):d.value=vals[i]
sharp={tuple(sorted(e.vertices)):e.use_edge_sharp for e in m.edges}
for e in new.edges:e.use_edge_sharp=sharp.get(tuple(sorted(used[i] for i in e.vertices)),False)
new.update()
new.normals_split_custom_set([Vector(n).normalized() for n in newnorms])
o.data=new
o.vertex_groups.clear()
for name in group_names:o.vertex_groups.new(name=name)
for ni,oi in enumerate(used):
    for g,v in weights[oi].items():o.vertex_groups[g].add([ni],v,'REPLACE')
new.update()

# Scope check uses retained source vertex IDs and original corner order, so a
# global normal/UV/weight change cannot hide behind a successful FBX export.
old_unrelated=[p for p in m.polygons if p.material_index!=lin]
new_unrelated=[p for p in new.polygons if all(comp[used[i]]!=1001 for i in p.vertices)]
assert len(old_unrelated)==len(new_unrelated)
print('CHECK_UNRELATED_SURFACES',flush=True)
oldloops=[];newloops=[]
for p,q in zip(old_unrelated,new_unrelated):
    assert p.material_index==q.material_index or (q.material_index==lin and all(comp[i]==1 for i in p.vertices))
    assert [remap[i] for i in p.vertices]==list(q.vertices)
    oldloops.extend(p.loop_indices);newloops.extend(q.loop_indices)
cn=np.array([d.vector[:] for d in new.corner_normals])
normal_delta=np.linalg.norm(cn[newloops]-np.asarray(norms)[oldloops],axis=1)
normal_errors=[(float(normal_delta.max()),0,0,0)]
for k in uvs:
    nuv=np.array([d.uv[:] for d in new.uv_layers[k].data])
    assert np.max(np.abs(nuv[newloops]-np.asarray(uvs[k])[oldloops]))<1e-6
print('NORMAL_ROUNDTRIP',max(normal_errors),flush=True)
# Blender compresses custom normals into its local normal spaces again. Preserve
# original sharp edges; bound that re-encoding to 0.05 degrees (not exact bytes).
normal_angle=math.degrees(2*math.asin(min(1,max(normal_errors)[0]/2)))
assert normal_angle<.05
for ni,oi in enumerate(used):
    assert np.array_equal(np.array(new.vertices[ni].co[:]),np.asarray(co[oi],dtype='f4'))
    actual={g.group:g.weight for g in new.vertices[ni].groups}
    assert max([abs(actual.get(g,0)-v) for g,v in weights[oi].items()]+[0])<1e-7
assert len(a.data.bones)==264
lining_faces=[p for p in new.polygons if all(comp[used[i]]==1001 for i in p.vertices)]
from collections import Counter,defaultdict
edge_count=Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%3]))) for p in lining_faces for i in range(3))
adj=defaultdict(set)
for (i,j),count in edge_count.items():
    assert count<=2
    if count==1:adj[i].add(j);adj[j].add(i)
assert all(len(v)==2 for v in adj.values())
seen=set();boundaries=[]
for i in adj:
    if i in seen:continue
    todo=[i];part=[];seen.add(i)
    while todo:
        j=todo.pop();part.append(j)
        for k in adj[j]:
            if k not in seen:seen.add(k);todo.append(k)
    points=np.array([new.vertices[j].co[:] for j in part]);boundaries.append({'vertices':len(part),'min':points.min(0).tolist(),'max':points.max(0).tolist()})
assert len(boundaries)==3,('Must have one waist and two separate leg openings',boundaries)
hems=[b for b in boundaries if b['max'][2]<101]
assert len(hems)==2 and any(b['max'][0]<0 for b in hems) and any(b['min'][0]>0 for b in hems),hems
central=[p for p in m.polygons if p.material_index==lin and all(abs(co[i][0])<1.2 and co[i][2]>98 for i in p.vertices)]
assert central and all(all(i in remap for i in p.vertices) for p in central),'Central bridge must be preserved'
report={'baseline':'motion-v3-release','change':'level-short-leg-openings-preserving-closed-crotch-bridge-and-opaque-underlying-surface',
 'flat_cut_fault':'v3 has one wide lower opening, removing the low central bridge',
 'outer_hem_z_cm':98,'central_minimum_cut_z_cm':98,'hem_lowered_from_v3_cm':2,
 'boundary_loops':boundaries,'one_waist_two_leg_openings':True,'underlying_opaque_backup_triangles':backup_faces,
 'central_bridge_triangles_preserved':len(central),
 'total_triangles':len(new.polygons),'visible_triangles':len(new.polygons)-3264,
 'vertices':len(new.vertices),'bones':264,'original_leg_positions_and_weights_unchanged':True,
 'unrelated_triangles_uv_weights_preserved':True,
 'unrelated_custom_normals_max_roundtrip_angle_degrees':normal_angle,
 'cloth_geometry_and_materials_unchanged':True,'runtime_tested':False}
assert sum(p.material_index>=19 for p in new.polygons)==3264
(R/'coverage-repair.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
contract={'positions_blender_cm':[v.co[:] for v in new.vertices],
 'influences':[{o.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>1e-7} for v in new.vertices],
 'bones':[b.name for b in a.data.bones],'source_components':[d.value for d in new.attributes['source_component'].data]}
(R/'source-render-contract.json').write_text(json.dumps(contract),encoding='utf-8')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'sui-jk-motion-source.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT');o.select_set(True);a.select_set(True);bpy.context.view_layer.objects.active=a
fbx=R/'Sui_JK_Hun_Body_Motion.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
spec=json.loads((W/'source-spec.json').read_text());spec.update(fbx=str(fbx),source_root=str(R),fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest(),expected_triangles=len(new.polygons),expected_visible_triangles=report['visible_triangles'])
(W/'source-spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
print('SHORTEN_LINING_OK',json.dumps(report),flush=True)
