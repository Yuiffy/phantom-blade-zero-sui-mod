"""Numeric checks for the v7 candidate: layering, proportions, skin quality."""
import bpy, json, math
import numpy as np
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parent
V6 = ROOT.parent / 'jk-v6-candidate' / 'sui-jk-hun-bound.blend'
V7 = ROOT / 'sui-jk-hun-bound-v7.blend'


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    me = ob.data
    n = len(me.vertices)
    co = np.array([v.co[:] for v in me.vertices], dtype=float)
    comp = np.array([me.attributes['source_component'].data[i].value for i in range(n)])
    return ob, arm, co, comp


def layering(me, co, comp, zlo=103.0, zhi=115.0):
    """Ray-cast outward from the body axis through each skirt vertex.

    If the ray leaves the body without crossing the jacket, that skirt vertex is
    exposed and can be seen poking through the jacket hem.
    """
    from mathutils.bvhtree import BVHTree
    idx, verts, faces = {}, [], []
    for p in me.polygons:
        if comp[p.vertices[0]] != 0:
            continue
        c = co[list(p.vertices)].mean(axis=0)
        if not (94 <= c[2] <= 122 and abs(c[0]) < 30):
            continue
        f = []
        for vi in p.vertices:
            if vi not in idx:
                idx[vi] = len(verts)
                verts.append(co[vi])
            f.append(idx[vi])
        faces.append(tuple(f))
    if not faces:
        return {'error': 'no jacket faces'}
    tree = BVHTree.FromPolygons(verts, faces)
    exposed, tested, miss = 0, 0, []
    for i in range(len(co)):
        if comp[i] != 10 or not (zlo <= co[i, 2] < zhi):
            continue
        # the cardigan is open at the front: exposure there is intentional
        if co[i, 1] - 5.1454 < 0.0 and abs(co[i, 0]) < 14.0:
            continue
        tested += 1
        r = math.hypot(co[i, 0], co[i, 1] - 5.1454)
        if r < 1e-6:
            continue
        o = Vector((0.0, 5.1454, co[i, 2]))
        d = Vector((co[i, 0], co[i, 1] - 5.1454, 0.0)).normalized()
        hit = tree.ray_cast(o, d)
        if hit[0] is None:
            exposed += 1
            miss.append((i, round(co[i, 2], 1), round(r, 1)))
        elif (hit[0] - o).length < r - 0.05:
            exposed += 1
            miss.append((i, round(co[i, 2], 1), round(r, 1)))
    return {'band_cm': [zlo, zhi], 'skirt_vertices_tested': tested,
            'skirt_exposed_outside_jacket': exposed,
            'worst': sorted(miss, key=lambda t: -t[2])[:5]}


def proportions(arm, co, comp):
    head = np.isin(comp, [2, 3, 6])
    head_top = float(co[head, 2].max())
    chin = float(co[comp == 3, 2].min())
    feet = float(co[:, 2].min())
    height = head_top - feet
    # jacket silhouette across the shoulder shelf (sleeve cap included)
    band = (comp == 0) & (co[:, 2] > 140) & (co[:, 2] < 160) & (np.abs(co[:, 0]) < 38)
    shoulder = float(np.abs(co[band, 0]).max()) * 2
    # anatomical shoulder joints: the pivot the deltoid actually rotates around
    joints = [arm.data.bones[n].head_local for n in ('upperarm_l', 'upperarm_r')]
    shoulder_joint = abs(joints[0].x - joints[1].x)
    head_w = float(co[comp == 3, 0].max() - co[comp == 3, 0].min())
    # landmark stack that the eye reads as "how long is the neck"
    collar_top = float(co[comp == 25, 2].max())     # white stand collar
    bow_top = float(co[comp == 11, 2].max())        # the big pink bow
    shelf = float(co[(comp == 0) & (np.abs(co[:, 0]) > 24) & (np.abs(co[:, 0]) < 30)
                     & (co[:, 2] < 180), 2].max())
    h = head_top - chin
    return {
        'height_cm': round(height, 2),
        'head_cm': round(h, 2),
        'heads_tall': round(height / h, 2),
        'head_width_cm': round(head_w, 2),
        'shoulder_width_cm': round(shoulder, 2),
        'shoulder_over_head': round(shoulder / head_w, 2),
        'shoulder_joint_cm': round(shoulder_joint, 2),
        'shoulder_joint_over_head': round(shoulder_joint / h, 3),
        'chin_z': round(chin, 2), 'collar_top_z': round(collar_top, 2),
        'bow_top_z': round(bow_top, 2), 'shelf_z': round(shelf, 2),
        'chin_to_collar_over_head': round((chin - collar_top) / h, 3),
        'chin_to_bow_over_head': round((chin - bow_top) / h, 3),
        'chin_to_shelf_over_head': round((chin - shelf) / h, 3),
    }


def skin_stats(ob, arm, co, comp):
    names = {g.index: g.name for g in ob.vertex_groups}
    W = [{names[g.group]: g.weight for g in v.groups if g.weight > 1e-7} for v in ob.data.vertices]
    ax = np.abs(co[:, 0]); z = co[:, 2]
    head_leak = 0.0
    n = 0
    for i, d in enumerate(W):
        if ax[i] > 12.0 and z[i] < 168.0 and 'head' in d and comp[i] not in (2, 3, 6, 21, 22, 29, 34):
            head_leak = max(head_leak, d['head']); n += 1
    # negative-y check: nothing but hands should be far from the body axis
    # the visible neck column only: comp 0 (skin) on the body axis
    neck_top = [i for i in range(len(W))
                if ax[i] < 7.5 and 156 < z[i] < 168 and comp[i] == 0]
    neck_chain = sum(1 for i in neck_top
                     if W[i].get('neck_01', 0) + W[i].get('neck_02', 0) > 0.5)
    skull = [i for i in range(len(W)) if comp[i] == 0 and z[i] > 172]
    skull_loose = sum(1 for i in skull if W[i].get('head', 0) < 0.5)
    return {'vertices_with_head_weight_outside_neck': n,
            'max_head_weight_outside_neck': round(head_leak, 4),
            'skull_vertices': len(skull),
            'skull_not_head_driven': skull_loose,
            'neck_band_vertices': len(neck_top),
            'neck_band_using_neck_bones': neck_chain}


def pose_stretch(ob, arm, label, rots):
    """Edge length change in the neck/shoulder band for a diagnostic pose."""
    me = ob.data
    rest = np.array([v.co[:] for v in me.vertices])
    edges = np.array([e.vertices[:] for e in me.edges])
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion()
        pb.location = (0, 0, 0); pb.scale = (1, 1, 1)
    for name, axis, deg in rots:
        pb = arm.pose.bones[name]
        basis = pb.bone.matrix_local.to_quaternion()
        pb.rotation_quaternion = (basis.inverted() @
                                  Quaternion(Vector(axis), math.radians(deg)) @ basis)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    data = ev.to_mesh()
    pos = np.array([v.co[:] for v in data.vertices])
    ev.to_mesh_clear()
    l0 = np.linalg.norm(rest[edges[:, 0]] - rest[edges[:, 1]], axis=1)
    l1 = np.linalg.norm(pos[edges[:, 0]] - pos[edges[:, 1]], axis=1)
    mid = rest[edges].mean(axis=1)
    ax = np.abs(mid[:, 0])
    neck_axis = np.hypot(mid[:, 0], mid[:, 1] - 6.0)
    visible_neck = (neck_axis < 7.5) & (mid[:, 2] > 157) & (mid[:, 2] < 167)
    shoulder = (ax > 10) & (ax < 36) & (mid[:, 2] > 140) & (mid[:, 2] < 162)
    out = {'pose': label}
    for name, sel in (('neck', visible_neck), ('shoulder', shoulder)):
        sel = sel & (l0 > 0.15)
        r = l1[sel] / l0[sel]
        out[name + '_edges'] = int(sel.sum())
        out[name + '_p99'] = round(float(np.percentile(r, 99)), 4)
        out[name + '_max'] = round(float(r.max()), 4)
    # worst offenders regardless of band, to catch real tears
    r_all = l1 / np.maximum(l0, 1e-6)
    big = np.flatnonzero((r_all > 1.6) & (l0 > 0.15))
    out['edges_over_1.6x'] = int(len(big))
    out['worst_rest_cm'] = round(float(l0[r_all.argmax()]), 3)
    return out


def run(path, tag):
    ob, arm, co, comp = load(path)
    rep = {'tag': tag,
           'proportions': proportions(arm, co, comp),
           'layering': layering(ob.data, co, comp),
           'skin': skin_stats(ob, arm, co, comp)}
    poses = [
        ('head-turn', [('head', (0, 0, 1), 45), ('neck_02', (0, 0, 1), 25),
                       ('neck_01', (0, 0, 1), 15)]),
        ('head-nod', [('head', (1, 0, 0), 25), ('neck_02', (1, 0, 0), 10)]),
        ('shoulders-up', [('clavicle_l', (0, 1, 0), 0), ('upperarm_l', (0, 1, 0), -55),
                          ('upperarm_r', (0, 1, 0), 55)]),
    ]
    rep['poses'] = [pose_stretch(ob, arm, *p) for p in poses]
    return rep


v6 = run(V6, 'v6')
v7 = run(V7, 'v7')
out = {'v6': v6, 'v7': v7}
(ROOT / 'verify-v7.json').write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding='utf8')
for k in ('proportions', 'skin'):
    print(k)
    for a, b in zip(v6[k].items(), v7[k].items()):
        print(f"  {a[0]:32s} v6={a[1]:<10} v7={b[1]}")
print('poses')
for a, b in zip(v6['poses'], v7['poses']):
    print(f"  {a['pose']:13s} neck p99 v6={a['neck_p99']:<7} v7={b['neck_p99']:<7} | "
          f"shoulder p99 v6={a['shoulder_p99']:<7} v7={b['shoulder_p99']:<7} | "
          f"edges>1.6x v6={a['edges_over_1.6x']:<5} v7={b['edges_over_1.6x']}")
print('layering: skirt exposed outside the jacket')
for tag in ('v6', 'v7'):
    L = (v6 if tag == 'v6' else v7)['layering']
    print(f"  {tag}: tested={L.get('skirt_vertices_tested')} exposed={L.get('skirt_exposed_outside_jacket')} worst={L.get('worst')[:3]}")
