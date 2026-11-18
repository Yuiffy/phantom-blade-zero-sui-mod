"""Preserve original guide vertices, pin weights and end caps on coarser rings."""
import numpy as np
from measure import common, prior, root


def reduce_rings(asset, sectors):
    p = np.array(asset['positions'])
    levels = np.unique(p[:, 2].round(3))[::-1]
    rings, caps, points, indices = [], [], [], []
    for z in levels[::2]:
        ids = np.flatnonzero(p[:,2].round(3) == z)
        xy = p[ids,:2]
        center = (xy.max(0) + xy.min(0))/2
        normalized = (xy-center) / np.ptp(xy,axis=0)
        cap = np.linalg.norm(normalized,axis=1)<.04
        ring = ids[~cap]
        angles = np.arctan2(normalized[~cap,1],normalized[~cap,0])
        selected=[]
        for theta in np.arange(sectors)*2*np.pi/sectors:
            selected.append(ring[np.argmin(abs(np.angle(np.exp(1j*(angles-theta)))))])
        assert len(set(selected))==sectors
        rings.append(list(range(len(points),len(points)+sectors)))
        points.extend(p[selected].tolist())
        if cap.any():
            assert sum(cap)==1
            caps.append((len(rings)-1,len(points)))
            points.append(p[ids[cap][0]].tolist())
    for upper,lower in zip(rings,rings[1:]):
        for i in range(sectors):
            j=(i+1)%sectors
            indices.extend([upper[i],lower[i],upper[j],upper[j],lower[i],lower[j]])
    for level,tip in caps:
        ring=rings[level]
        for i in range(sectors):
            j=(i+1)%sectors
            indices.extend([tip,ring[i],ring[j]] if level==0 else [tip,ring[j],ring[i]])
    assert len(levels)%2 == 1
    return dict(positions=points,indices=indices)


if __name__=='__main__':
    assets=common.read(prior/'coarse64-12x3-delivery/cloth-details.json')['assets']
    for index,sectors in [(1,12),(3,16),(4,12)]:
        a=assets[index]
        common.write(root/'guides'/(a['name']+'.json'),reduce_rings(a,sectors))
