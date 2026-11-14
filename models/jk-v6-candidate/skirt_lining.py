"""Keep the leg mesh intact; add an opaque, smoothly cut safety underlayer."""
import bpy,bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def refine_clearance_and_add_lining(body):
    part=body.data.attributes['source_component']
    before=len(body.data.vertices)
    original=body.data.attributes.new('original_vertex_id','INT','POINT')
    part=body.data.attributes['source_component']
    for i,d in enumerate(original.data):d.value=i
    ids=[v.index for v in body.data.vertices if part.data[v.index].value==1]
    remap={k:i for i,k in enumerate(ids)}
    faces=[tuple(remap[i] for i in p.vertices) for p in body.data.polygons if all(i in remap for i in p.vertices)]
    tree=BVHTree.FromPolygons([body.data.vertices[i].co for i in ids],faces)
    corrected=0;max_adjust=0.
    for v in body.data.vertices:
        if part.data[v.index].value!=10 or v.co.z>=106:continue
        near,normal,_,distance=tree.find_nearest(v.co)
        if near is None or distance>6:continue
        radial=near-Vector((8.4635 if near.x>=0 else -8.4635,5.1454,near.z))
        if normal.dot(radial)<0:normal=-normal
        signed=(v.co-near).dot(normal)
        if signed<4.5:
            adjusted=near+normal*4.5
            max_adjust=max(max_adjust,(adjusted-v.co).length)
            v.co=adjusted;corrected+=1
    body.data.update()
    # Copy just the existing hips/upper thighs and interpolate the cut edge's
    # original skin weights. No changes to the original leg vertices.
    bm=bmesh.new();bm.from_mesh(body.data)
    component=bm.verts.layers.int['source_component']
    original_ids=bm.verts.layers.int['original_vertex_id']
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if v[component]!=1],context='VERTS')
    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.0001,plane_co=Vector((0,0,94)),plane_no=Vector((0,0,1)),clear_inner=True,clear_outer=False)
    bm.normal_update()
    deform=bm.verts.layers.deform.active
    for v in bm.verts:
        v.co+=v.normal*.18
        v[component]=1001;v[original_ids]=-1
        if deform:
            weights=v[deform];total=sum(weights.values())
            assert total>0
            for key in list(weights.keys()):weights[key]/=total
    bmesh.ops.triangulate(bm,faces=list(bm.faces))
    for f in bm.faces:f.material_index=0;f.smooth=True
    mesh=bpy.data.meshes.new('Sui_SafetyLining');bm.to_mesh(mesh);bm.free();mesh.update()
    assert len(mesh.vertices)>0 and min(v.co.z for v in mesh.vertices)>93
    lining=bpy.data.objects.new('Sui_SafetyLining',mesh);bpy.context.collection.objects.link(lining)
    for group in body.vertex_groups:lining.vertex_groups.new(name=group.name)
    mat=bpy.data.materials.new('MI_JK_SafetyLining');mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value=(.009,.011,.019,1.)
    bs.inputs['Roughness'].default_value=.9;bs.inputs['Metallic'].default_value=0.
    mesh.materials.clear();mesh.materials.append(mat)
    count=len(mesh.vertices);tris=sum(len(p.vertices)-2 for p in mesh.polygons)
    bpy.ops.object.select_all(action='DESELECT');body.select_set(True);lining.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
    return {'original_vertices':before,'lining_vertices':count,'lining_triangles':tris,
            'lining_lower_cut_z_cm':94,'lining_surface_offset_cm':.18,
            'skirt_clearance_corrected_vertices':corrected,'max_clearance_adjustment_cm':max_adjust,
            'original_leg_vertices_preserved':True,'lining_material':'MI_JK_SafetyLining',
            'new_physics':False}
