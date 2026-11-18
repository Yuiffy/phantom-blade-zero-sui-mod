"""Narrow cheek/jaw silhouette with identity constraints around eyes and lips."""
from common import *
import numpy as np

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    if not (ROOT / 'baseline.json').exists():
        expected = read(REPO / 'private/outfit-patterns-v1/installation-receipt.json')['after']
        assert snapshot() == expected
        write(ROOT / 'baseline.json', dict(files=snapshot(), game_runtime_tested=False))
    assert_baseline()
    d = np.load(REPO / 'private/outfit-patterns-v1/jk-native.npz')
    fields = {k: d[k].copy() for k in d.files}
    old = fields['positions'].copy()
    comp = np.load(REPO / 'private/outfit-patterns-v1/jk-components.npz')['components']
    assert sha(SOURCE.with_suffix('.uexp')) == sha(JK / 'final-legacy' / (relative_package(BODY) + '.uexp'))
    x, y, z = old.T
    center = -.4195
    radius = np.abs(x - center)
    # Leave the complete eye opening, lashes, iris and lips on their original
    # vertex positions. Smooth exclusion bands prevent seams at the margins.
    eye = (1 - smooth(179.9, 182.0, z)) * smooth(172.4, 175.4, z)
    eye *= smooth(.0, 1.8, y) * (1 - smooth(9.8, 16.8, radius))
    mouth = (1 - smooth(2.6, 4.4, radius)) * smooth(167.8, 169.4, z) * (1 - smooth(172.5, 173.8, z)) * smooth(1.0, 2.5, y)
    editable = (comp == 0) & (fields['materials'] == 0)
    height = smooth(167.6, 169.1, z) * (1 - smooth(182.0, 186.5, z))
    side = smooth(2.4, 7.0, radius)
    # The reference's strongest difference is the lower cheek and jaw, rather
    # than an overall head/eye scale. Keep upper skull and neck unchanged.
    amount = .055 + .045 * (1 - smooth(172.5, 178.0, z))
    alpha = editable * height * side * (1 - eye) * (1 - mouth)
    new = old.copy()
    new[:, 0] = x - (x - center) * amount * alpha
    # Slightly reduce the inflated lateral cheek volume while preserving the
    # central nose, mouth, chin tip and the complete back of the skull.
    new[:, 1] = y - .08 * alpha * smooth(1.5, 4.5, y) * smooth(172.0, 174.0, z) * (1 - smooth(176.0, 178.0, z))
    fields['positions'] = new.astype('<f4')
    changed = np.any(fields['positions'] != old, axis=1)
    # Derive the normal transform from the smooth spatial deformation Jacobian;
    # this retains the original smooth/custom normals at UV/section splits.
    def deform(q):
        xx, yy, zz = q.T; rr = np.abs(xx - center)
        ee = (1 - smooth(179.9, 182., zz)) * smooth(172.4, 175.4, zz) * smooth(0., 1.8, yy) * (1 - smooth(9.8, 16.8, rr))
        mm = (1 - smooth(2.6, 4.4, rr)) * smooth(167.8, 169.4, zz) * (1 - smooth(172.5, 173.8, zz)) * smooth(1., 2.5, yy)
        aa = editable * smooth(167.6, 169.1, zz) * (1 - smooth(182., 186.5, zz)) * smooth(2.4, 7., rr) * (1 - ee) * (1 - mm)
        out = q.copy(); out[:, 0] -= (xx - center) * (.055 + .045 * (1 - smooth(172.5, 178., zz))) * aa
        out[:, 1] -= .08 * aa * smooth(1.5, 4.5, yy) * smooth(172., 174., zz) * (1 - smooth(176., 178., zz))
        return out
    jac = np.empty((len(old), 3, 3))
    for k in range(3):
        delta = np.zeros(3); delta[k] = .002
        jac[:, :, k] = (deform(old.astype(float) + delta) - deform(old.astype(float) - delta)) / .004
    print('JACOBIAN_MIN',float(np.linalg.det(jac).min())); assert np.linalg.det(jac).min() > .65, 'Folded deformation'
    packed = fields['packed_tangents'].copy()
    normal = packed[:, 4:7].view('i1').astype(float) / 127
    tangent = packed[:, :3].view('i1').astype(float) / 127
    unit = lambda q: q / np.maximum(1e-12, np.linalg.norm(q, axis=1, keepdims=True))
    n = unit(np.linalg.solve(jac.transpose(0, 2, 1), normal[..., None])[..., 0])
    t = np.einsum('nij,nj->ni', jac, tangent)
    t = unit(t - n * np.sum(n * t, axis=1, keepdims=True))
    for cols, vectors in [(slice(0, 3), t), (slice(4, 7), n)]:
        packed[changed, cols] = np.rint(np.clip(vectors[changed], -1, 1) * 127).astype('i1').view('u1')
    fields['packed_tangents'] = packed
    fields['normals'] = packed[:, 4:7].view('i1').astype(float) / 127
    fields['changed'] = changed
    np.savez_compressed(ROOT / 'before.npz', **{k: d[k] for k in d.files})
    np.savez_compressed(ROOT / 'authored.npz', **fields)
    protected_eye = (fields['materials'] == 0) & (z >= 175.4) & (z <= 179.9) & (y >= 1.8) & (radius <= 9.8)
    protected_lip = (comp == 36) | ((comp == 0) & (radius <= 2.6) & (z >= 169.4) & (z <= 172.5) & (y >= 2.5))
    assert np.array_equal(new[protected_eye], old[protected_eye])
    assert np.array_equal(new[protected_lip], old[protected_lip])
    assert np.all(comp[changed] == 0)
    slices = []
    ref = np.load(REPO / 'private/outfit-patterns-v1/jirai-native.npz')
    rc = np.load(REPO / 'private/outfit-patterns-v1/jirai-components.npz')['components']
    for lo, hi in [(169, 171), (172, 175), (175, 177), (180, 183)]:
        mask = (comp == 0) & (z >= lo) & (z < hi) & (y > 0)
        rq = ref['positions']; rm = (rc == 0) & (rq[:, 2] >= lo) & (rq[:, 2] < hi) & (rq[:, 1] > 0)
        width = lambda p, mask: float(np.ptp(p[mask, 0]))
        slices.append(dict(z_cm=[lo, hi],before_cm=width(old, mask),after_cm=width(new, mask),jirai_reference_cm=width(rq, rm)))
    write(ROOT / 'author-report.json', dict(passed=True, changed_vertices=int(changed.sum()), max_displacement_cm=float(np.linalg.norm(new-old,axis=1).max()),
        lower_face_widths=slices, protected_eye_vertices=int(protected_eye.sum()),protected_lip_vertices=int(protected_lip.sum()),
        eyes_and_lips_positions_exact=True, all_other_components_exact=True,uv_indices_weights_cloth_and_textures_untouched=True,
        authored_sha256=sha(ROOT/'authored.npz'), game_runtime_tested=False))
    print('JK_FACE_AUTHORED', json.dumps(slices))

if __name__ == '__main__':
    main()
