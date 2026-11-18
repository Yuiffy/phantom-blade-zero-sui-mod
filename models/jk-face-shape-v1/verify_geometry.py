"""Check the independently decoded native head, seams and feature exclusions."""
from common import *
import numpy as np

def main():
    a=np.load(ROOT/'before.npz');b=np.load(ROOT/'final.npz')
    c=np.load(REPO/'private/outfit-patterns-v1/jk-components.npz')['components']
    old=a['positions'];new=b['positions'];changed=np.any(old!=new,axis=1)
    assert np.array_equal(changed,b['changed'])
    assert np.all(c[changed]==0) and np.all(old[changed,2]>167.6)
    for key in ['indices','uv','materials']:
        assert np.array_equal(a[key],b[key]),key
    assert np.array_equal(a['packed_tangents'][~changed],b['packed_tangents'][~changed])
    assert np.array_equal(a['packed_tangents'][:,[3,7]],b['packed_tangents'][:,[3,7]])
    radius=np.abs(old[:,0]+.4195)
    eye=(a['materials']==0)&(old[:,2]>=175.4)&(old[:,2]<=179.9)&(old[:,1]>=1.8)&(radius<=9.8)
    lips=(c==36)|((c==0)&(radius<=2.6)&(old[:,2]>=169.4)&(old[:,2]<=172.5)&(old[:,1]>=2.5))
    for mask in [eye,lips,c!=0]:
        assert np.array_equal(old[mask],new[mask])
        assert np.array_equal(a['packed_tangents'][mask],b['packed_tangents'][mask])
    tri=a['indices'].reshape(-1,3);tri=tri[np.any(changed[tri],axis=1)]
    fn=lambda p:np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]])
    f0,f1=fn(old),fn(new);size=np.linalg.norm(f0,axis=1);valid=size>1e-6
    cos=np.sum(f0[valid]*f1[valid],axis=1)/(size[valid]*np.linalg.norm(f1[valid],axis=1))
    assert cos.min()>.90,'Unexpected local fold or large triangle rotation'
    edge=np.unique(np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1),axis=0)
    oldlen=np.linalg.norm(old[edge[:,0]]-old[edge[:,1]],axis=1);newlen=np.linalg.norm(new[edge[:,0]]-new[edge[:,1]],axis=1)
    ratio=newlen[oldlen>1e-5]/oldlen[oldlen>1e-5]
    assert ratio.min()>.65 and ratio.max()<1.4
    # Shared source positions must still coincide at native UV/normal splits.
    _,ids=np.unique(old,axis=0,return_inverse=True)
    displacements=new-old;spread=0.
    for axis in range(3):
        lo=np.full(ids.max()+1,np.inf);hi=np.full_like(lo,-np.inf)
        np.minimum.at(lo,ids,displacements[:,axis]);np.maximum.at(hi,ids,displacements[:,axis]);spread=max(spread,float((hi-lo).max()))
    assert spread<1e-5,'An originally coincident native seam split opened'
    author=read(ROOT/'author-report.json')
    write(ROOT/'geometry-verification.json',dict(passed=True,native_sha256=sha(ROOT/'final.npz'),changed_vertices=int(changed.sum()),protected_eye_vertices=int(eye.sum()),protected_lip_vertices=int(lips.sum()),
        eyes_lips_and_other_components_positions_and_frames_exact=True,native_uv_indices_and_handedness_exact=True,no_triangle_flips=True,min_triangle_normal_dot=float(cos.min()),edge_ratio=[float(ratio.min()),float(ratio.max())],max_seam_spread_cm=spread,
        lower_face_widths=author['lower_face_widths'],max_displacement_cm=float(np.linalg.norm(new-old,axis=1).max()),game_runtime_tested=False))
    print('JK_FACE_GEOMETRY_VERIFIED',int(changed.sum()),float(cos.min()),ratio.min(),ratio.max())

if __name__=='__main__':main()
