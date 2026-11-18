"""Check source provenance, strict accessory scope and new surface integrity."""
from common import *
import numpy as np
from collections import Counter

def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);old=np.load(PIN/'final-render.npz');sel=np.load(ROOT/'author-selections.npz');report=read(ROOT/'author-report.json')
 assert report['source_native_sha256']==sha(PIN/'final-render.npz') and report['native_sha256']==sha(ROOT/'patched-render.npz')
 ids=np.concatenate([sel['vertices_16'],sel['vertices_17']]);slots=np.concatenate([sel['triangles_16'],sel['triangles_17']]);allowed=np.isin(np.arange(len(d['positions'])),ids)
 for key in ['positions','packed_tangents','normals']:assert np.array_equal(d[key][~allowed],old[key][~allowed]),key
 for key in ['uv','materials','source_index']:assert np.array_equal(d[key],old[key]),key
 oldtri=old['indices'].reshape(-1,3);tri=d['indices'].reshape(-1,3)
 assert np.array_equal(tri[~np.isin(np.arange(len(tri)),slots)],oldtri[~np.isin(np.arange(len(tri)),slots)])
 assert np.all((old['positions'][ids,2]>165)&(old['positions'][ids,2]<170))
 assert np.isfinite(d['positions']).all() and np.isfinite(d['normals']).all()
 groups=[]
 for group in report['groups']:
  m=group['material'];tt=tri[sel[f'triangles_{m}'][:group['new_triangles']]];pp=d['positions'];q=pp[tt]
  cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);area=np.linalg.norm(cross,axis=1)
  assert area.min()>1e-6 and np.all(np.isin(tt,sel[f'vertices_{m}']))
  # Closed strap occupies the first 256 triangles; black decorative bezel
  # is a deliberately supported annulus behind the separate silver heart.
  closed=tt[:256] if m==16 else tt
  edges=Counter(tuple(sorted([int(a),int(b)])) for f in closed for a,b in zip(f,np.roll(f,-1)))
  assert set(edges.values())=={2},(m,Counter(edges.values()))
  groups.append(dict(material=m,closed_surface_triangles=len(closed),minimum_double_area_cm2=float(area.min()),used_vertices=len(np.unique(tt))))
 # Confirm the entire original head, iris, hair, skin and physical cloth parts.
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),accessory_vertices=len(ids),accessory_triangle_slots=len(slots),all_other_geometry_frames_indices_exact=True,all_uvs_materials_exact=True,face_lashes_lip_iris_hair_and_cloth_exact=True,finite_geometry=True,closed_strap_and_silver_heart_manifold=True,groups=groups,game_runtime_tested=False))
 print('CHOKER_GEOMETRY_VERIFIED',final,flush=True)
if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
