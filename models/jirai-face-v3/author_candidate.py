"""Keep topology/UV/weights; make iris and closed white one coherent surface."""
from pathlib import Path
import bpy, json, math
import numpy as np

R = Path(__file__).resolve().parents[2]
W = R / 'private/jirai-face-v3'; W.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(R / 'private/skin-eyes-v1/sui-jirai-motion.blend'))
o = next(x for x in bpy.context.scene.objects if x.type == 'MESH')
m = o.data; m.calc_loop_triangles()
old = np.array([v.co[:] for v in m.vertices]); new = old.copy()
c = np.array([v.value for v in m.attributes['source_component'].data])
uv = np.array([v.uv[:] for v in m.uv_layers.active.data])
lv = np.array([v.vertex_index for v in m.loops])
lt = np.array([t.loops[:] for t in m.loop_triangles]); mt = np.array([t.material_index for t in m.loop_triangles])
weights = [[(g.group, g.weight) for g in v.groups] for v in m.vertices]
# Sample the original surface-owned albedo for bounded lash selection.
sampled=np.load(W/'source-colors.npz')
vc=np.full((len(old),3),255.0)
face_ids=np.where((c==0)|(c==19))[0]
assert face_ids.max()<len(sampled['positions'])
assert np.max(np.abs(sampled['positions'][face_ids]-old[face_ids]))<1e-5
vc[face_ids]=sampled['colors'][face_ids]

def eye_front(x, z, cx):
    sign = 1 if cx < 0 else -1
    q = ((x-cx)/3.1)**2 + ((z-177.799362)/2.0)**2
    return -.9 - 1.4*np.sqrt(np.maximum(0, 1-q)) - .30*sign*(x-cx)

for iris, white, cx in [(51, 950, -5.317217), (52, 951, 4.614422)]:
    ids = np.where(c == white)[0]
    q = old[ids]
    # Exact affine deformation of the existing closed ellipsoid, including
    # its back hemisphere. Preserve its manifold topology and rigid weights.
    sign = 1 if cx < 0 else -1
    new[ids, 1] = -.9 + (q[:, 1]-1.28)*(1.4/2.30) - .30*sign*(q[:, 0]-cx)
    ids = np.where(c == iris)[0]; q = old[ids]
    # Preserve a small real thickness where the original disc has front/back
    # duplicate XZ positions; avoid turning them into coplanar z-fighting.
    xz = np.round(q[:, [0, 2]], 4)
    near = np.max(np.abs(xz[:, None] - xz[None]), axis=2) < .015
    min_y = np.min(np.where(near, q[None, :, 1], np.inf), axis=1)
    nx=(q[:,0]-cx)/1.67;nz=(q[:,2]-177.799362)/1.89;r=np.sqrt(nx*nx+nz*nz)
    target_r=np.where(r>.9,.9+.1*np.tanh((r-.9)/.1),r)
    radial=np.divide(target_r,r,out=np.ones_like(r),where=r>1e-8)
    new[ids, 0] = cx + (q[:, 0]-cx)*.97*radial
    new[ids, 2] = 177.799362+(q[:,2]-177.799362)*radial
    new[ids, 1] = eye_front(new[ids, 0], new[ids, 2], cx) - .14 + .08*(q[:, 1]-min_y)
    # Source mesh contains chunky, faceted solid highlight fragments. Hide
    # them beneath the coherent iris; the new albedo supplies crisp glints.
    for cid in ([131, 139] if iris == 51 else [135, 141]):
        ids2 = np.where(c == cid)[0]
        new[ids2, 1] = eye_front(old[ids2, 0], old[ids2, 2], cx) + .18

# Fine separate eyebrows remain behind the bangs rather than painted on it.
for cid in [101, 102]:
    ids = np.where(c == cid)[0]
    mid = (old[ids, 2].max() + old[ids, 2].min()) / 2
    new[ids, 2] = mid + (old[ids, 2]-mid)*.25

# Reduce the small lower lash clumps without changing the eye opening.
for cid in [125, 126, 128, 136]:
    ids = np.where(c == cid)[0]; q = old[ids]
    new[ids, 0] = q[:, 0].mean() + (q[:, 0]-q[:, 0].mean())*.72
    new[ids, 2] = q[:, 2].max() + (q[:, 2]-q[:, 2].max())*.65
    new[ids, 1] = q[:, 1].mean() + (q[:, 1]-q[:, 1].mean())*.35

# The connected head's raised upper-lash strip sits in front of the iris.
# Smooth only this bounded strip's depth, preserving its opening silhouette.
ids = np.where((c == 0) & (old[:, 2] > 178.35) & (old[:, 2] < 180.1)
    & (np.abs(old[:, 0]+.3514) > 2.6) & (np.abs(old[:, 0]+.3514) < 8.6) & (old[:, 1] < -.5))[0]
for i in ids:
    q = old[i]; cx = -5.317217 if q[0] < -.35 else 4.614422
    # Feather in depth so surrounding skin/temple vertices remain continuous.
    a = np.clip((180.1-q[2])/.8, 0, 1)*np.clip((q[2]-178.35)/.35, 0, 1)
    target = eye_front(q[0], min(q[2], 179.3), cx)-.18
    new[i, 1] = q[1]*(1-a*.55)+target*a*.55

# Narrow the actual dark upper-lash geometry, including the outer clumps.
ids = np.where((c == 0) & (old[:,2]>178) & (old[:,2]<180.2)
    & (np.abs(old[:,0]+.3514)>2.6) & (np.abs(old[:,0]+.3514)<8.8)
    & (old[:,1]<-.5) & (vc.mean(1)<175))[0]
for i in ids:
    q=old[i]; cx=-5.317217 if q[0]<-.35 else 4.614422
    a=float(np.clip((180-vc[i].mean())/65,0,1))
    outward=(q[0]-cx)*(-1 if cx<0 else 1)
    upper=178.91+.10*outward-.08*((q[0]-cx)/3)**2
    new[i,2]=q[2]*(1-a)+(upper+(q[2]-upper)*.30)*a

# The source connected head also contains solid colored fragments inside the
# original iris silhouette. Recess those under the actual eye surface; they
# otherwise appear as white polygon clumps along the lower iris edge.
for cx,sign in [(-5.317217,1),(4.614422,-1)]:
    dx=(old[:,0]-cx)*sign;dz=old[:,2]-177.799362
    inner=((dx/1.78)**2+(dz/1.92)**2<1.12)&(old[:,2]>176.05)&(old[:,2]<178.62)
    aperture=(dx/2.65)**2+(dz/1.55)**2
    nasal=(dx>1.55)&(dx<2.55)&(aperture<.89)
    ids=np.where((c==0)&(old[:,1]<.8)&(inner|nasal))[0]
    surface=eye_front(old[ids,0],old[ids,2],cx)+.16
    blend=np.where(inner[ids],1.,np.clip((.96-aperture[ids])/.22,0,1))
    new[ids,1]+=np.maximum(0,surface-new[ids,1])*blend

# Taper the existing lowest fringe tips slightly, retaining all UVs/indices.
ids=np.where((c==19)&(old[:,2]<181.0))[0]
a=np.clip((181-old[ids,2])/1.7,0,1)
new[ids,2]+=.16*np.sin(old[ids,0]*4.5)*a

# Close the small jagged mouth seam rather than leaving holes between lips.
# Shape the connected lip boundary and inner backing onto a shallow smile.
for cid in [0,56]:
    ids=np.where((c==cid)&(np.abs(old[:,0]+.35)<2.6)&(old[:,2]>170.6)&(old[:,2]<172.45)&(old[:,1]<-.5))[0]
    x=old[ids,0]+.35; curve=171.65+.085*x*x
    blend=np.clip((1.35-np.abs(old[ids,2]-curve))/.25,0,1)*np.clip((2.6-np.abs(x))/.3,0,1)
    new[ids,2]=old[ids,2]*(1-blend)+(curve+(old[ids,2]-curve)*.18)*blend
ids=np.where(c==56)[0];x=old[ids,0]+.35;curve=171.65+.085*x*x
# Use the original closed inner-mouth surface as a shallow lip backing.
new[ids,2]=curve+(old[ids,2]-171.65)*.25
new[ids,1]=-4.20+.16*x*x+.04*(old[ids,1]+4)
# Smooth the shallow mouth surface into the surrounding skin to remove the
# bright raised ridge left by the source lip geometry.
ids=np.where(np.isin(c,[0,56])&(np.abs(old[:,0]+.35)<2.7)&(old[:,2]>170.6)&(old[:,2]<172.45)&(old[:,1]<-.5))[0]
x=new[ids,0]+.35;z=new[ids,2]
blend=np.clip((2.7-np.abs(x))/.45,0,1)*np.clip((1.05-np.abs(z-171.65))/.40,0,1)
target=-4.10+.15*x*x-.25*(z-171.65)
target+=np.where(c[ids]==56,.22,np.maximum(0,old[ids,1]+3.3)*.65)
new[ids,1]=new[ids,1]*(1-blend)+target*blend

for i, v in enumerate(m.vertices): v.co = new[i]
m.update(); m.calc_loop_triangles()
assert len(m.vertices) == len(old) and np.array_equal(lv, np.array([v.vertex_index for v in m.loops]))
assert np.array_equal(uv, np.array([v.uv[:] for v in m.uv_layers.active.data]))
assert weights == [[(g.group, g.weight) for g in v.groups] for v in m.vertices]
changed = np.linalg.norm(new-old, axis=1) > 1e-6
assert np.all(old[changed, 2] > 170.6)
assert set(c[changed]) <= {0, 19, 51, 52, 56, 101, 102, 125, 126, 128, 131, 135, 136, 139, 141, 950, 951}
np.savez_compressed(W / 'surface.npz', old_positions=old, positions=new, components=c,
    uv=uv, loop_vertices=lv, loop_triangles=lt, materials=mt, changed=changed)
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'candidate.blend'), compress=True)
(W / 'geometry-report.json').write_text(json.dumps(dict(changed_vertices=int(changed.sum()),
    components=sorted(map(int, set(c[changed]))), topology_uv_weights_exact=True,
    body_cloth_positions_exact=True, eye_equation='sheared ellipsoid center Y=-0.9, radii=(3.1,1.4,2.0), shear +/-0.30',
    game_runtime_tested=False), indent=2))
print('FACE3_GEOMETRY_AUTHORED', int(changed.sum()))
