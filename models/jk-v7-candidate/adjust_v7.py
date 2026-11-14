"""v7: post-bind shape and skin repair for the Sui JK / Hun model.

Runs on the v6 bound blend. Changes rest geometry only (no new bones, no new
physics, no pose baked into the asset) plus surgical weight repair:

* raise the head assembly and stretch the neck band so the neck is not sunk
  into the shoulders (v6 lowered the head 3.5 cm without lengthening the neck)
* drop and pull in the shoulder line so the trapezius slopes instead of the
  jacket forming a flat shelf
* lower/narrow the bow tie so the front of the neck is visible
* tuck the skirt waist inside the jacket hem (the skirt was wider than the
  jacket at the hem, so the pleat sawtooth poked through)
* extend the jacket hem slightly over the skirt waist
* repair skin weights: head weight is stripped from collar/shoulder vertices,
  the neck gets a neck_01/neck_02/head gradient, the jacket hem is made
  pelvis-driven instead of thigh/finger driven
"""
import bpy, json, hashlib, math
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parent
SRC = ROOT.parent / 'jk-v6-candidate' / 'sui-jk-hun-bound.blend'

# ---- parameters (cm) -------------------------------------------------------
P = dict(
    head_rise=2.6, head_ramp=(148.0, 163.0), neck_halfwidth=(8.0, 12.0),
    bow_lift=0.9, collar_base=147.0, collar_scale_z=0.88, collar_scale_x=0.96,
    shoulder_from=14.0, shoulder_to=24.0, shoulder_scale=0.88,
    shoulder_drop=1.6, shoulder_fade=(158.0, 166.0),
    bow_narrow=0.84,
    skirt_tuck=0.22, skirt_tuck_win=(99.0, 112.0),
    hem_target=102.5, hem_top=121.0, hem_flare=1.4,
)
HEAD_COMPS = {2, 3, 6, 21, 22, 29, 31, 34, 36, 40, 41, 47, 51}
STRAP_COMPS = {15, 32, 35}          # cross-body strap over the shoulder
NECK_TOP = 174.0


def sstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3.0 - 2.0 * x)


def load():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    ob = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
    me = ob.data
    n = len(me.vertices)
    co = np.array([v.co[:] for v in me.vertices], dtype=float)
    comp = np.array([me.attributes['source_component'].data[i].value for i in range(n)])
    return ob, arm, co, comp


def deform(co, comp):
    z = co[:, 2].copy()

    # 1. head assembly up; the neck stretches only inside the collar band and
    # becomes rigid with the jaw at z>=163 so the chin/neck junction cannot fold
    head = np.isin(comp, list(HEAD_COMPS))
    ramp = sstep((z - P['head_ramp'][0]) / (P['head_ramp'][1] - P['head_ramp'][0]))
    lat = 1.0 - sstep((np.abs(co[:, 0]) - P['neck_halfwidth'][0]) /
                      (P['neck_halfwidth'][1] - P['neck_halfwidth'][0]))
    dz = P['head_rise'] * ramp * lat
    dz[head] = P['head_rise']
    co[:, 2] += dz
    z = co[:, 2].copy()

    # 2. shoulder: squeeze only the outer cap laterally, plus a small shelf drop.
    # The neck, collar, vest V and bow must not move: earlier attempts that
    # shifted z near |x|<16 splayed the collar and surfaced the vest.
    z = co[:, 2].copy()
    ax = np.abs(co[:, 0])
    head = np.isin(comp, list(HEAD_COMPS))
    t = sstep((ax - P['shoulder_from']) / (P['shoulder_to'] - P['shoulder_from']))
    wz = 1.0 - sstep((z - P['shoulder_fade'][0]) /
                     (P['shoulder_fade'][1] - P['shoulder_fade'][0]))
    wz[head] = 0.0
    f = 1.0 + (P['shoulder_scale'] - 1.0) * t * wz
    outer = ax > P['shoulder_from']
    co[outer, 0] = np.sign(co[outer, 0]) * (
        P['shoulder_from'] + (ax[outer] - P['shoulder_from']) * f[outer])
    co[:, 2] -= P['shoulder_drop'] * t * wz * (z > 130.0)

    # 3. bow tie / shirt collar: bow narrowed to the art ratio and lifted to
    #    close the white notch at the throat; the collar band is shortened so it
    #    does not read as two tall wings next to the longer neck
    bow = comp == 11
    co[bow, 0] = -0.6 + (co[bow, 0] + 0.6) * P['bow_narrow']
    co[bow, 2] += P['bow_lift']
    collar = comp == 25
    co[collar, 2] = P['collar_base'] + (co[collar, 2] - P['collar_base']) * P['collar_scale_z']
    co[collar, 0] *= P['collar_scale_x']

    # 4. tuck the skirt waist in so it cannot cross the jacket surface
    sk = comp == 10
    t = sstep((co[:, 2] - P['skirt_tuck_win'][0]) /
              (P['skirt_tuck_win'][1] - P['skirt_tuck_win'][0])) * sk
    f = 1.0 - P['skirt_tuck'] * t
    co[:, 0] = np.where(sk, co[:, 0] * f, co[:, 0])
    co[:, 1] = np.where(sk, 5.1454 + (co[:, 1] - 5.1454) * f, co[:, 1])

    # 5. jacket hem: the measured hem ring sits at z=105.5..109.7 (it dips at
    #    the sides), so 14-18 cm of skirt showed against 7 cm in the art and the
    #    pleat tops were exposed. Lengthen the jacket's lower band down to a
    #    level hem below the pleat tops, stretching rather than crushing it.
    hem = (comp == 0) & (np.abs(co[:, 0]) < 30)
    az = np.arctan2(co[:, 0], co[:, 1] - 5.1454)
    hem_z = 107.6 - 2.1 * np.cos(2.0 * az)        # per-azimuth hem height
    z = co[:, 2]
    target = P['hem_target']
    top = P['hem_top']
    band = hem & (z > hem_z - 0.01) & (z < top)
    s = (top - target) / np.maximum(top - hem_z, 1e-3)
    co[band, 2] = target + (z[band] - hem_z[band]) * s[band]
    # small radial flare so the lengthened hem clears the skirt waist
    flare = P['hem_flare'] * sstep((z[band] - hem_z[band]) / 6.0)
    r = np.hypot(co[band, 0], co[band, 1] - 5.1454)
    sc = (r + flare) / np.maximum(r, 1e-6)
    co[band, 0] *= sc
    co[band, 1] = 5.1454 + (co[band, 1] - 5.1454) * sc
    return co


def weights_fix(ob, co_orig, co_new, comp):
    """Repair skin weights where v6 leaked across body regions."""
    names = {g.index: g.name for g in ob.vertex_groups}
    me = ob.data
    n = len(me.vertices)
    W = [{names[g.group]: float(g.weight) for g in v.groups if g.weight > 1e-7}
         for v in me.vertices]
    x = co_orig[:, 0]
    z = co_orig[:, 2]
    side = np.where(x < 0, 'r', 'l')
    stats = {'head_stripped': 0, 'neck_stripped': 0, 'neck_regraded': 0, 'hem_fixed': 0}

    def renormalise(d):
        s = sum(d.values())
        return {k: v / s for k, v in d.items() if v > 1e-7} if s > 0 else {}

    for i in range(n):
        d = dict(W[i])
        ax = abs(x[i])
        # (a) head weight must never reach the collar, shoulder or back.
        # The strip is faded in over |x| so the trapezius boundary does not
        # become a single hard weight step (that tore edges on head turns).
        # It is also faded OUT above the trapezius: the skull and the sides of
        # the face are comp 0 too, and at |x| 7-12 they sit well inside the head
        # silhouette, so stripping them left the back of the head driven by
        # neck_01 and sheared the scalp on every head turn.
        skull_gate = 1.0 - sstep((z[i] - 158.0) / 6.0)
        if 'head' in d and comp[i] not in HEAD_COMPS and skull_gate > 1e-4:
            frac = skull_gate * max(sstep((ax - 7.0) / 4.5),
                                    sstep((158.0 - z[i]) / 6.0))
            if frac > 1e-4:
                moved = d['head'] * frac
                if frac >= 1.0:
                    d.pop('head')
                    rest = sum(d.values())
                    if rest > 1e-6:
                        for k in d:
                            d[k] += moved * d[k] / rest
                    else:
                        t = sstep((ax - 10.0) / 16.0)
                        clav = 0.15 + 0.50 * t
                        d['spine_05'] = d.get('spine_05', 0.0) + moved * (1.0 - clav)
                        d['clavicle_' + side[i]] = d.get('clavicle_' + side[i], 0.0) + moved * clav
                else:
                    d['head'] -= moved
                    rest = sum(d[k] for k in d if k != 'head')
                    if rest > 1e-6:
                        for k in d:
                            if k != 'head':
                                d[k] += moved * d[k] / rest
                    else:
                        d['neck_01'] = d.get('neck_01', 0.0) + moved
                stats['head_stripped'] += 1
        # (b) neck bones must not drive the shoulder cap (faded, not clipped)
        if ax > 16.0 and z[i] < NECK_TOP:
            frac = sstep((ax - 16.0) / 6.0)
            moved = sum(d.get(k, 0.0) for k in ('neck_01', 'neck_02')) * frac
            if moved > 1e-7:
                for k in ('neck_01', 'neck_02'):
                    if k in d:
                        d[k] -= d[k] * frac
                d['spine_05'] = d.get('spine_05', 0.0) + moved * 0.55
                d['clavicle_' + side[i]] = d.get('clavicle_' + side[i], 0.0) + moved * 0.45
                stats['neck_stripped'] += 1
        # (c) neck chain, blended in so no hard weight boundary is created.
        # The neck mesh only has a handful of loops, so a wide head blend folds
        # the surface. Keep the visible neck rigid with the head and let the
        # hand-off happen inside the collar band.
        blend = (1.0 - sstep((ax - 7.5) / 4.0)) * sstep((z[i] - 150.0) / 5.0)
        if blend > 1e-4 and z[i] <= NECK_TOP and comp[i] == 0:
            t = z[i]
            w_sp = 1.0 - sstep((t - 147.0) / 4.0)
            w_n1 = sstep((t - 147.0) / 4.0) * (1.0 - sstep((t - 151.0) / 3.0))
            w_n2 = sstep((t - 150.0) / 2.5) * (1.0 - sstep((t - 153.0) / 3.0))
            w_hd = sstep((t - 153.0) / 3.0)      # rigid with the head from z=156
            total = w_sp + w_n1 + w_n2 + w_hd
            if total > 1e-6:
                chain = {'spine_05': w_sp / total, 'neck_01': w_n1 / total,
                         'neck_02': w_n2 / total, 'head': w_hd / total}
                mixed = {k: v * (1.0 - blend) for k, v in d.items()}
                for k, v in chain.items():
                    mixed[k] = mixed.get(k, 0.0) + v * blend
                d = mixed
                stats['neck_regraded'] += 1
        # (e) collar and bow follow the neck a little so they stay seated when
        #     the head turns instead of drifting off the neck
        if comp[i] in (11, 25) and z[i] > 147.0:
            follow = 0.55 * sstep((z[i] - 147.0) / 7.0)
            if follow > 1e-4:
                d = {k: v * (1.0 - follow) for k, v in d.items()}
                d['neck_01'] = d.get('neck_01', 0.0) + follow
        # (d) jacket hem belongs to the pelvis/waist, not the thighs or fingers
        if comp[i] == 0 and 97.0 < z[i] < 109.0 and ax < 24.0:
            bad = sum(d.pop(k, 0.0) for k in list(d)
                      if k.startswith(('thigh_', 'hand_', 'lowerarm_')) or
                      any(k.startswith(f'{f}_') for f in
                          ('thumb', 'index', 'middle', 'ring', 'pinky')))
            if bad > 1e-7:
                d['pelvis'] = d.get('pelvis', 0.0) + bad * 0.72
                d['spine_01'] = d.get('spine_01', 0.0) + bad * 0.28
                stats['hem_fixed'] += 1
        d = {k: v for k, v in renormalise(d).items() if v > 1e-4}
        W[i] = renormalise(d)
    return W, stats


def write_weights(ob, W):
    me = ob.data
    keep = sorted({k for row in W for k in row})
    ob.vertex_groups.clear()
    groups = {name: ob.vertex_groups.new(name=name) for name in keep}
    buckets = {name: ([], []) for name in keep}
    for i, row in enumerate(W):
        for name, w in row.items():
            buckets[name][0].append(i)
            buckets[name][1].append(w)
    for name, (idx, wts) in buckets.items():
        g = groups[name]
        for i, w in zip(idx, wts):
            g.add([i], w, 'REPLACE')


def fix_custom_normals(me, co_rest, co_new):
    """Rotate the author's custom split normals with the deformation.

    The mesh keeps authored corner normals; after moving up to 5.6 cm they no
    longer match the surface and read as hard shading edges on the shoulders.
    Each loop's normal is rotated by the minimal rotation that takes its face's
    rest normal to its deformed normal.
    """
    if not me.has_custom_normals:
        return 0
    old = [c.vector.copy() for c in me.corner_normals]
    polys = [(p.loop_start, p.loop_total, list(p.vertices[:3])) for p in me.polygons]
    out = [None] * len(me.loops)
    for start, total, tri in polys:
        a, b, c = tri
        n0 = (Vector(co_rest[b]) - Vector(co_rest[a])).cross(
            Vector(co_rest[c]) - Vector(co_rest[a]))
        n1 = (Vector(co_new[b]) - Vector(co_new[a])).cross(
            Vector(co_new[c]) - Vector(co_new[a]))
        if n0.length < 1e-9 or n1.length < 1e-9:
            for i in range(start, start + total):
                out[i] = old[i]
            continue
        q = n0.normalized().rotation_difference(n1.normalized())
        for i in range(start, start + total):
            out[i] = (q @ old[i]).normalized()
    me.normals_split_custom_set(out)
    return len(out)


def main():
    ob, arm, co0, comp = load()
    me = ob.data
    n = len(co0)
    co = deform(co0.copy(), comp)
    me.vertices.foreach_set('co', co.ravel())
    me.update()
    loops_fixed = fix_custom_normals(me, co0, co)
    W, stats = weights_fix(ob, co0, co, comp)
    write_weights(ob, W)
    me.update()

    report = {
        'source': str(SRC.name),
        'parameters': P,
        'vert_count': n,
        'displacement_max_cm': float(np.linalg.norm(co - co0, axis=1).max()),
        'vertices_moved_gt_0.05cm': int((np.linalg.norm(co - co0, axis=1) > 0.05).sum()),
        'weight_repairs': stats,
        'custom_normals_fixed': loops_fixed,
        'vertices': n, 'triangles': sum(len(p.vertices) - 2 for p in me.polygons),
        'bones': len(arm.data.bones), 'materials': len(me.materials),
    }
    # sanity
    unweighted = sum(1 for v in me.vertices if not v.groups)
    err = max(abs(sum(g.weight for g in v.groups) - 1.0) for v in me.vertices)
    maxinf = max(len(v.groups) for v in me.vertices)
    report.update({'unweighted_vertices': unweighted, 'max_weight_sum_error': err,
                   'max_influences': maxinf})
    assert unweighted == 0 and err < 1e-5 and maxinf <= 8, (unweighted, err, maxinf)

    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.scale_length = 0.01
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.cycles.device = 'CPU'
    blend = ROOT / 'sui-jk-hun-bound-v7.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)

    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = arm
    fbx = ROOT / 'Sui_JK_Hun_Body.fbx'
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False, bake_anim=False, use_mesh_modifiers=False,
        use_armature_deform_only=False, mesh_smooth_type='FACE',
        axis_forward='-Z', axis_up='Y', primary_bone_axis='Y',
        secondary_bone_axis='X', path_mode='STRIP', embed_textures=False)
    report['fbx_sha256'] = hashlib.sha256(fbx.read_bytes()).hexdigest()
    (ROOT / 'v7-report.json').write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding='utf8')
    print('V7 ' + json.dumps({k: v for k, v in report.items() if k != 'parameters'}))


main()
