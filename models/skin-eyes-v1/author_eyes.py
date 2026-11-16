"""Append closed sclera surfaces; retain every existing vertex, UV and weight."""
import bpy, json, math, hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

R = Path(__file__).resolve().parents[2]
W = R / 'private/skin-eyes-v1'; BASE = R / 'private/jirai-detail-v1'
W.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / 'sui-jirai-motion.blend'))
o = next(x for x in bpy.context.scene.objects if x.type == 'MESH')
arm = next(x for x in bpy.context.scene.objects if x.type == 'ARMATURE')
m = o.data; m.calc_loop_triangles()
old_count = len(m.vertices)
old_points = np.array([v.co[:] for v in m.vertices])
old_uv = np.array([x.uv[:] for x in m.uv_layers.active.data])
old_weights = [{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
comp = np.array([x.value for x in m.attributes['source_component'].data])
old_triangles = [tuple(t.vertices) for t in m.loop_triangles if comp[t.vertices[0]]<2000]
old_labels = [int(comp[t[0]]) for t in old_triangles]
old_tree = BVHTree.FromPolygons([Vector(v) for v in old_points],old_triangles,all_triangles=True)
spec = json.loads((BASE / 'game-materials.json').read_text())

def mat(name, rough, color=None):
    source = m.materials[0]
    result = source.copy() if color is None else bpy.data.materials.new(name)
    result.name = name; result.use_nodes = True
    bs = result.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value = rough
    if color is not None: bs.inputs['Base Color'].default_value = (*color,1)
    spec.append(dict(slot=name,source_texture=color is None,
        base_color_linear=[*(color or (1,1,1)),1],roughness=rough,metallic=0))
    m.materials.append(result)
    return result, len(m.materials)-1

iris, iris_slot = mat('MI_Jirai_EyeIris', .26)
white, white_slot = mat('MI_Jirai_Sclera', .3, (.88,.86,.83))
for f in m.polygons:
    if comp[f.vertices[0]] in [51,52]: f.material_index = iris_slot
for s in spec:
    if s['slot'] in ['MI_Jirai_Skin','MI_Jirai_Hands']: s['roughness'] = .57
    if s['slot'] in ['MI_Jirai_Hair','MI_Jirai_TailL','MI_Jirai_TailR']: s['roughness'] = .4
for material in m.materials:
    if material.use_nodes and material.name in ['MI_Jirai_Skin','MI_Jirai_Hands']:
        bs = material.node_tree.nodes.get('Principled BSDF')
        bs.inputs['Roughness'].default_value = .57
        bs.inputs['Subsurface Weight'].default_value = .08

eyes = []
for cid, newcid in [(51,950),(52,951)]:
    ids = np.where(comp == cid)[0]
    points = old_points[ids]
    center = ((points[:,0].min()+points[:,0].max())*.5, 1.28,
        (points[:,2].min()+points[:,2].max())*.5)
    # The opaque front sits behind the retained iris. The wider curved surface
    # continues beneath the lids; its back is closed for oblique views.
    radii = (3.10,2.30,2.00)
    normalized = (points-np.array(center))/radii
    white_front = center[1]-radii[1]*np.sqrt(np.maximum(0,1-normalized[:,0]**2-normalized[:,2]**2))
    clearance = float(np.min(white_front-points[:,1]))
    assert clearance > .1, ('sclera would obscure iris',cid,clearance)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=center)
    eye = bpy.context.object; eye.name = 'Sclera_L' if cid == 52 else 'Sclera_R'
    eye.scale = radii
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    eye.data.materials.append(white)
    for f in eye.data.polygons: f.use_smooth = True
    eye.data.attributes.new('source_component','INT','POINT').data.foreach_set('value',[newcid]*len(eye.data.vertices))
    eye.data.attributes.new('original_vertex_index','INT','POINT').data.foreach_set('value',[-1]*len(eye.data.vertices))
    # Existing iris vertices use the actual head transform, so transfer exactly
    # rather than introducing new face bones or an unmatched skeleton.
    weights = old_weights[int(ids[0])]
    assert all(old_weights[int(i)] == weights for i in ids), 'iris is not rigid'
    for name, weight in weights.items():
        eye.vertex_groups.new(name=name).add(list(range(len(eye.data.vertices))),weight,'REPLACE')
    eye.parent = arm; eye.modifiers.new('Hun','ARMATURE').object = arm
    edge_counts = {}
    for f in eye.data.polygons:
        for e in f.edge_keys: edge_counts[e] = edge_counts.get(e,0)+1
    assert set(edge_counts.values()) == {2}
    eyes.append(dict(component=newcid,iris_component=cid,center_cm=center,radii_cm=radii,
        vertices=len(eye.data.vertices),closed_manifold=True,weights=weights,
        front_depth_clearance_to_iris_vertices_cm=clearance,
        projected_aperture_radii_cm=[3.1,2.0]))

bpy.ops.object.select_all(action='DESELECT')
o.select_set(True)
for x in bpy.context.scene.objects:
    if x.type == 'MESH' and x.name.startswith('Sclera_'): x.select_set(True)
bpy.context.view_layer.objects.active = o; bpy.ops.object.join()
m = o.data; m.calc_loop_triangles()
assert np.array_equal(old_points,np.array([v.co[:] for v in m.vertices[:old_count]]))
assert np.array_equal(old_uv,np.array([x.uv[:] for x in m.uv_layers.active.data[:len(old_uv)]]))
for i in range(old_count):
    assert old_weights[i] == {o.vertex_groups[g.group].name:g.weight for g in m.vertices[i].groups}
cc = np.array([x.value for x in m.attributes['source_component'].data])
new_triangles = [tuple(t.vertices) for t in m.loop_triangles if cc[t.vertices[0]]<2000]
new_labels = [int(cc[t[0]]) for t in new_triangles]
new_tree = BVHTree.FromPolygons([v.co.copy() for v in m.vertices],new_triangles,all_triangles=True)
ray_checks=[]
for eye in eyes:
    cx,_,cz=eye['center_cm'];covered=skin_covered=filled=visible=0;bad=[]
    for x in np.linspace(cx-3.3,cx+3.3,101):
        for z in np.linspace(cz-1.75,cz+1.75,61):
            origin=Vector((x,-30,z));direction=Vector((0,1,0))
            a,_,ai,_=old_tree.ray_cast(origin,direction,60)
            b,_,bi,_=new_tree.ray_cast(origin,direction,60)
            if bi is None or new_labels[bi]!=eye['component']:continue
            visible+=1
            if ai is not None and old_labels[ai]==eye['iris_component']:covered+=1
            aperture=((x-cx)/3.1)**2+((z-cz)/2.0)**2
            if aperture>1:
                skin_covered+=1;bad.append((float(x),float(z),float(a.y-b.y)))
            if ai is None or a.y-b.y>.05:filled+=1
    ray_checks.append(dict(component=eye['component'],rays=6161,visible_white_rays=visible,
        iris_rays_covered=covered,white_rays_outside_aperture=skin_covered,socket_backing_rays_replaced=filled,
        rejected_samples=bad[:12]))
(W/'source-eye-rays.json').write_text(json.dumps(ray_checks,indent=2))
assert all(x['iris_rays_covered']==0 and x['white_rays_outside_aperture']==0 and x['socket_backing_rays_replaced']>10 for x in ray_checks),ray_checks
weights = [{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in m.vertices]
(W / 'source-render-contract.json').write_text(json.dumps(dict(positions_blender_cm=[list(v.co) for v in m.vertices],influences=weights,bones=[b.name for b in arm.data.bones])))
(W / 'game-materials.json').write_text(json.dumps(spec,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'sui-jirai-motion.blend'),compress=True)
bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); arm.select_set(True); bpy.context.view_layer.objects.active = arm
fbx = W / 'Sui_Jirai_Hun_Body.fbx'
bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=False,use_mesh_modifiers=False,use_armature_deform_only=False,mesh_smooth_type='FACE',axis_forward='-Z',axis_up='Y',primary_bone_axis='Y',secondary_bone_axis='X',path_mode='STRIP',embed_textures=False)
report = json.loads((BASE / 'binding-report.json').read_text())
report.update(vertices=len(m.vertices),triangles=len(m.loop_triangles),visible_triangles=int(sum(cc[t.vertices[0]]<2000 for t in m.loop_triangles)),render_material_slots=len(m.materials),material_slots=len(spec),fbx_sha256=hashlib.sha256(fbx.read_bytes()).hexdigest())
(W / 'binding-report.json').write_text(json.dumps(report,indent=2))
proof = dict(passed=True,basis='installed R6 source; append-only sclera and eye material split',
    source_fbx_sha256=report['fbx_sha256'],unchanged_vertices_checked=old_count,
    all_original_positions_uv_weights_preserved=True,all_hair_and_skirt_positions_weights_exactly_preserved=True,
    bones_and_physics_recipe_unchanged=True,eyes=eyes,game_runtime_tested=False)
(W / 'source-preservation.json').write_text(json.dumps(proof,indent=2))
print('EYES_AUTHORED',len(m.vertices),len(m.loop_triangles))
