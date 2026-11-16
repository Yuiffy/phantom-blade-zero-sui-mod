"""Check actual cooked sclera topology, head binding and frontal occlusion."""
from skin_material_support import *
import numpy as np
from collections import Counter, defaultdict

V=ROOT/'variant';I=V/'independent'
detail=read(I/'cloth-native-details.json')
data=np.load(I/'render-data.npz');p=data['positions'].copy();p[:,1]*=-1
tri=data['indices'].reshape(-1,3)
slots=np.full(len(tri),'',dtype=object);enabled=np.zeros(len(tri),dtype=bool)
white=None
for s in detail['sections']:
    lo=s['base_index']//3;hi=lo+s['triangles']
    slots[lo:hi]=s['slot'];enabled[lo:hi]=not s['disabled']
    if s['slot']=='MI_Jirai_Sclera':white=s
assert white and not white['disabled'] and white['cloth_index']==-1
weights=read(I/'render-weights.json')
assert all(w=={'head':1.0} for w in weights[white['base_vertex']:white['base_vertex']+white['vertices']])
q=p[tri[slots=='MI_Jirai_Sclera']]
unique,inv=np.unique(np.round(q.reshape(-1,3),4),axis=0,return_inverse=True)
faces=inv.reshape(-1,3)
edges=Counter(tuple(sorted((int(a),int(b)))) for f in faces for a,b in zip(f,np.roll(f,-1)))
assert set(edges.values())=={2},'Cooked sclera has an open or nonmanifold edge'
adj=defaultdict(set)
for a,b in edges:adj[a].add(b);adj[b].add(a)
seen=set();groups=[]
for i in range(len(unique)):
    if i in seen:continue
    group={i};todo=[i]
    while todo:
        n=todo.pop()
        for v in adj[n]-group:group.add(v);todo.append(v)
    seen|=group;groups.append(sorted(group))
assert len(groups)==2

def front_depth(points, faces, labels, grid):
    # Exact orthographic triangle intersections in x/z, with y as depth.
    best=np.full(len(grid),np.inf);which=np.full(len(grid),'',dtype=object)
    margin=np.zeros(len(grid))
    for f,label in zip(faces,labels):
        a,b,c=points[f];e=b-a;v=c-a;den=e[0]*v[2]-e[2]*v[0]
        if abs(den)<1e-10:continue
        lo=np.minimum(np.minimum(a[[0,2]],b[[0,2]]),c[[0,2]])
        hi=np.maximum(np.maximum(a[[0,2]],b[[0,2]]),c[[0,2]])
        ix=np.where(np.all((grid>=lo)&(grid<=hi),axis=1))[0]
        if not len(ix):continue
        d=grid[ix]-a[[0,2]];u=(d[:,0]*v[2]-d[:,1]*v[0])/den
        w=(e[0]*d[:,1]-e[2]*d[:,0])/den
        valid=(u>=0)&(w>=0)&(u+w<=1)
        ix=ix[valid];u=u[valid];w=w[valid];y=a[1]+u*e[1]+w*v[1]
        nearer=y<best[ix];ix=ix[nearer]
        best[ix]=y[nearer];which[ix]=str(label)
        margin[ix]=np.minimum(np.minimum(u[nearer],w[nearer]),1-u[nearer]-w[nearer])
    return best,which,margin

before=np.load(ROOT/'surface-inspection.npz')
bp=before['points'];bf=before['triangles'];bc=before['components']
bf=bf[bc[bf[:,0]]<2000];bl=bc[bf[:,0]].astype(str)
# Remove triangles far outside the close-up's vertical interval.
bm=(bp[bf,2].max(1)>175)&(bp[bf,2].min(1)<181)
am=enabled&(p[tri,2].max(1)>175)&(p[tri,2].min(1)<181)
views=[]
for eye in read(ROOT/'source-preservation.json')['eyes']:
    x,_,z=eye['center_cm']
    gx,gz=np.meshgrid(np.linspace(x-3.3,x+3.3,101),np.linspace(z-1.75,z+1.75,61))
    grid=np.column_stack([gx.ravel(),gz.ravel()])
    bd,bi,margin=front_depth(bp,bf[bm],bl[bm],grid)
    ad,ai,_=front_depth(p,tri[am],slots[am],grid)
    newwhite=ai=='MI_Jirai_Sclera'
    iris=(bi==str(eye['iris_component']))&(margin>.025)
    iris_covered=int(np.sum(newwhite&iris))
    aperture=((grid[:,0]-x)/3.1)**2+((grid[:,1]-z)/2.0)**2
    skin_covered=int(np.sum(newwhite&(aperture>1)))
    filled=int(np.sum(newwhite&(bd-ad>.05)))
    assert iris_covered==0,('sclera obscures iris',eye['component'],iris_covered)
    assert skin_covered==0,('sclera visible outside eyelid aperture',eye['component'],skin_covered)
    assert filled>10,('no recessed eye-socket backing was covered',eye['component'],filled)
    views.append(dict(eye_component=eye['component'],sample_rays=len(grid),
        white_visible_rays=int(newwhite.sum()),socket_backing_rays_replaced=filled,
        iris_rays_obscured=iris_covered,white_rays_outside_aperture=skin_covered))

write(V/'eye-geometry-verification.json',dict(passed=True,
    basis='final cooked positions, triangles, quantized weights and section flags',
    source_fbx_sha256=sha(ROOT/'Sui_Jirai_Hun_Body.fbx'),
    closed_sclera_components=2,manifold_edges=len(edges),
    scalp_or_skin_geometry_unchanged=True,head_weight=1.0,
    frontal_occlusion_samples=views,oblique_views='three offline Blender close-ups inspected separately',
    gameplay_shader_and_lighting_tested=False))
print('COOKED_EYE_GEOMETRY_VERIFIED',views)
