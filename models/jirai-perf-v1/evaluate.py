"""Apply the R8 skirt recovery limits and measure all three guides."""
import json
import hashlib
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from measure import repo, root

variant = repo / 'private/jirai-skirt-shape-v1/variant'
independent = variant / 'independent'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def matrices(translations, rotations):
    matrices = np.tile(np.eye(4), (len(translations), 1, 1))
    matrices[:, :3, 3] = translations
    matrices[:, :3, :3] = Rotation.from_quat(rotations).as_matrix()
    return matrices


def skin_groups(weights, names):
    groups = {}
    for index, row in enumerate(weights):
        for name, weight in row.items():
            groups.setdefault(names.index(name.lower()), []).append((index, weight))
    return [(bone, np.array([i for i, _ in items]), np.array([w for _, w in items])[:, None])
            for bone, items in groups.items()]


def skinned(rest, groups, transforms):
    out = np.zeros_like(rest, dtype=float)
    for bone, indices, weights in groups:
        matrix = transforms[bone]
        out[indices] += (rest[indices] @ matrix[:3, :3].T + matrix[:3, 3]) * weights
    return out


def evaluate(settings):
    # ChinClean1's renderer and R8 share the skirt, validated separately at packaging.
    sections = read(independent / 'cloth-native-details.json')['sections']
    section = next(s for s in sections if s['slot'] == 'MI_Jirai_Skirt')
    lo = section['base_vertex']
    span = slice(lo, lo + section['vertices'])
    hem = np.load(variant / 'recovery/articulation-jog-recover-hem.npz')['hem']
    rest = np.load(independent / 'render-data.npz')['positions'][span][hem]
    bones = read(variant / 'import-report.json')['actual_reference_bones']
    names = [b['name'].lower() for b in bones]
    ref = matrices([b['t'] for b in bones], [b['q'] for b in bones])
    for i, bone in enumerate(bones):
        if bone['parent'] >= 0:
            ref[i] = ref[bone['parent']] @ ref[i]
    inverse = np.linalg.inv(ref)
    weights = read(independent / 'render-weights.json')[span]
    groups = skin_groups([row for row, keep in zip(weights, hem) if keep], names)
    mapping = section['cloth_maps'][0]
    ix = np.array(mapping['source'])[hem]
    bary = np.array(mapping['position'])[hem]
    coeff = np.column_stack([bary[:, :2], 1-bary[:, :2].sum(axis=1)])
    alpha = 1 - ix[:, 3:4]/65535
    guide_data = read(variant / 'cloth-details.json')['assets']
    mesh_doc = read(next((independent / 'json').rglob('Hun_Body_Simple.json')))
    guides = []
    for asset in guide_data:
        props = next(e['Properties'] for e in mesh_doc if e['Name'] == asset['name'])
        physical = props['LodData'][0]['PhysicalMeshData']
        positions = np.array(asset['positions'])
        tri = np.array(asset['indices']).reshape(-1, 3)
        edges = np.unique(np.sort(np.concatenate([tri[:, [0,1]], tri[:, [1,2]], tri[:, [2,0]]]), axis=1), axis=0)
        lengths = np.linalg.norm(np.diff(positions[edges],axis=1)[:,0],axis=1)
        weights = []
        for row in physical['BoneData']:
            pairs = {}
            for k in range(row['NumInfluences']):
                suffix = f'[{k}]' if k else ''
                pairs[props['UsedBoneNames'][row['BoneIndices'+suffix]]] = row['BoneWeights'+suffix]
            weights.append(pairs)
        distances = np.array(next(m['Value']['Values'] for m in physical['WeightMaps'] if m['Key']=='1'))
        guides.append((positions, skin_groups(weights, names), distances, edges[lengths>1e-5], lengths[lengths>1e-5]))
    records = []
    for path in sorted(root.glob(f'quality-*-{settings}-*.json')):
        data = read(path)
        assert data['solver'] == list(map(int, settings.split('x')))
        times, visible, stats = [], [], [[] for _ in guides]
        for frame in data['frames']:
            pose = np.array(frame['component_bones'])
            transforms = matrices(pose[:, :3], pose[:, 3:]) @ inverse
            for i, (points, groups_i, distance, edges, lengths) in enumerate(guides):
                result = next(x for x in frame['assets'] if x['asset_index']==i)
                q = np.array(result['component_positions'])
                delta = np.linalg.norm(q - skinned(points, groups_i, transforms),axis=1)
                ratios = np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/lengths
                stats[i].append([ratios.min(), ratios.max(), delta[distance==0].max(), (delta-distance).max()])
                if i == section['cloth_index']:
                    normals = np.array(result['component_normals'])
                    samples = q[ix[:,:3]] + normals[ix[:,:3]] * bary[:,3,None,None]
                    visible.append(skinned(rest, groups, transforms)*(1-alpha) + (samples*coeff[:,:,None]).sum(1)*alpha)
            times.append((frame['step']-60)*data['dt'])
        t = np.array(times)
        p = np.array(visible)
        offset = p - p[np.argmin(abs(t))]
        up = np.percentile(offset[:,:,2],95,axis=1)
        peak = offset[:,:,2].max(1)
        drift = np.percentile(np.linalg.norm(offset,axis=2),95,axis=1)
        speed = np.r_[0,np.percentile(np.linalg.norm(np.diff(p,axis=0),axis=2),95,axis=1)/np.diff(t)]
        limits = (up<=1.5) & (peak<=3) & (drift<=3)
        cycles = []
        for stop in [3,8,13]:
            quiet = (t>=stop+2.5)&(t<=stop+3.001)
            settled = next((float(t[i]-stop) for i in np.where((t>=stop)&(t<=stop+3.001))[0]
                            if limits[(t>=t[i])&(t<=stop+3.001)].all()), None)
            cycles.append(dict(recovery_seconds=settled, quiet_local_up_cm=float(peak[quiet].max()),
                               quiet_speed_cm_s=float(speed[quiet].max()), passed=bool(limits[quiet].all()
                               and speed[quiet].max()<=1 and settled is not None and settled<=2)))
        physical = []
        for stat in stats:
            a = np.array(stat)
            physical.append(dict(min_edge=a[:,0].min(),max_edge=a[:,1].max(),pin_cm=a[:,2].max(),
                                 excess_cm=a[:,3].max(),passed=bool(a[:,0].min()>.70 and a[:,1].max()<1.25
                                 and a[:,2].max()<.03 and a[:,3].max()<.15)))
        passed = all(c['passed'] for c in cycles+physical) and (data['profile']!='walk-recover' or up[t>=0].max()<=6)
        records.append(dict(file=path.name,sha256=sha(path),cycles=cycles,guides=physical,
                            peak_p95_up_cm=float(up[t>=0].max()),passed=bool(passed)))
    assert len(records)==6
    report = dict(settings=settings,passed=all(r['passed'] for r in records),records=records)
    (root / f'quality-report-{settings}.json').write_text(json.dumps(report,indent=2))
    for r in records:
        print(r['file'],r['passed'],[(c['recovery_seconds'],round(c['quiet_local_up_cm'],2)) for c in r['cycles']])
    return report


if __name__ == '__main__':
    assert evaluate(sys.argv[1])['passed']
