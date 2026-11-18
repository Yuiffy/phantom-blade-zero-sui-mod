"""Regression gates for the actual native eye depth, UVs and unrelated surfaces."""
from common import *
import numpy as np
from PIL import Image

def raster(p,tri,material,w=900,h=360):
    lower=np.array([-9.5,175.5]);extent=np.array([18.3,6.0])
    uv=(p[:,[0,2]]-lower)/extent*np.array([w-1,h-1])
    depth=np.full((h,w),-np.inf);owner=np.full((h,w),-1,int)
    iris=np.full_like(depth,-np.inf);white=np.full_like(depth,-np.inf)
    for t in tri:
        mat=int(material[t[0]])
        if mat not in [0,1,18,19] or p[t,2].max()<175.5 or p[t,2].min()>181.5:continue
        q=uv[t];lo=np.floor(q.min(0)).astype(int).clip(0,[w-1,h-1]);hi=np.ceil(q.max(0)).astype(int).clip(0,[w-1,h-1])
        a=np.column_stack([q[0]-q[2],q[1]-q[2]])
        if abs(np.linalg.det(a))<1e-9:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)])
        inside=(b>=-1e-6).all(-1);xx=xx[inside];yy=yy[inside];z=(b@p[t,1])[inside]
        take=z>depth[yy,xx];depth[yy[take],xx[take]]=z[take];owner[yy[take],xx[take]]=mat
        if mat in [18,19]:
            plane=iris if mat==18 else white
            plane[yy,xx]=np.maximum(plane[yy,xx],z)
    xx,zz=np.meshgrid(np.linspace(lower[0],lower[0]+extent[0],w),np.linspace(lower[1],lower[1]+extent[1],h))
    return depth,owner,iris,white,xx,zz

def verify(final=True):
    path=ROOT/('native/final-render.npz' if final else 'native/patched-render.npz')
    d=np.load(path);p=d['positions'];tri=d['indices'].reshape(-1,3);mat=d['materials']
    depth,owner,iris,white,x,z=raster(p,tri,mat)
    rows=[]
    for cx,sign in [(-5.317217,1),(4.614422,-1)]:
        ellipse=((x-cx)/(1.67*.97))**2+((z-177.799362)/1.89)**2
        inner=(ellipse<.90)&(z<178.55)&(z>176.2)&np.isfinite(iris)
        covered=inner&(owner==19)
        assert not covered.any(),('White clumps still cover the iris',cx,int(covered.sum()))
        visible=inner&(owner==18)
        assert visible.sum()>3000
        assert np.min(iris[visible]-white[visible])>.01
        def sample(xp,zp):
            col=round((xp+9.5)/18.3*(depth.shape[1]-1));row=round((zp-175.5)/6*(depth.shape[0]-1))
            return float(depth[row,col]),int(owner[row,col])
        a=sample(cx+sign*1.48,177.8);b=sample(cx+sign*1.85,177.8)
        assert a[1]==18 and b[1]==19,(a,b)
        step=abs(a[0]-b[0]);assert step<.30,('Iris/white depth discontinuity',step)
        rows.append(dict(center_x_cm=cx,visible_iris_interior_rays=int(visible.sum()),sclera_occluding_iris_rays=int(covered.sum()),
            min_iris_front_clearance_cm=float(np.min(iris[visible]-white[visible])),nasal_boundary_depth_step_cm=step))
    # Verify the two-channel native UV buffer: only iris UV0 may differ.
    from patch_native import unpack
    before=unpack(read(ROOT/'native/source.json'));detail=read(ROOT/'native/details.json');s=detail['uv_span']
    dt='<f2' if s['bytes']//s['count']==4 else '<f4'
    old=np.frombuffer(before,dt,count=s['count']*2,offset=s['offset']).reshape(len(p),2,2)
    assert np.array_equal(d['uv'][:,1],old[:,1])
    assert np.array_equal(d['uv'][mat!=18,0],old[mat!=18,0])
    # Round-trip planar half-float UVs should deviate by less than one texel
    # at 1024, including the pupil and highlights.
    source=np.load(ROOT/'surface.npz');src=source['positions'];c=source['components'];mapping=d['source_index']
    errors=[]
    for i in np.where(mat==18)[0]:
        j=mapping[i];cx=-5.317217 if c[j]==51 else 4.614422
        want=np.array([(src[j,0]-cx)/(1.67*.97)*.5+.5,.5-(src[j,2]-177.799362)/1.89*.5])
        errors.append(np.max(np.abs(d['uv'][i,0]-want))*1024)
    assert max(errors)<.5
    colors=np.array([[246,215,215],[220,220,230],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[0,0,0],[210,50,45],[241,239,235]])
    image=np.zeros((*owner.shape,3),np.uint8);ok=owner>=0;image[ok]=colors[owner[ok]]
    Image.fromarray(image[::-1]).save(ROOT/'native/eye-ownership.png')
    report=dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),eyes=rows,
        unchanged_uv1=True,only_iris_uv0_changed=True,max_iris_uv_rounding_error_pixels_1024=float(max(errors)),game_runtime_tested=False)
    write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),report)
    print('FACE3_GEOMETRY_VERIFIED',json.dumps(rows))

if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
