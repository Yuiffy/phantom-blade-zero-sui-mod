"""Repaint source-owned calf texels from a continuous 3D cylindrical pattern."""
from pathlib import Path
import json, hashlib
import cv2
import numpy as np
from PIL import Image

R=Path(__file__).resolve().parents[2]; W=R/'private/fishnet-v1'
SOURCE=R/'private/skin-eyes-v1/variant/textures/T_Jirai_Base.png'
d=np.load(W/'surface.npz'); p=d['positions']; c=d['components']; uv=d['uv']
lv=d['loop_vertices']; tris=d['loop_triangles']; verts=lv[tris]
src=np.array(Image.open(SOURCE).convert('RGB')); H,T=src.shape[:2]
assert H==T==4096

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def smooth(t):t=np.clip(t,0,1);return t*t*(3-2*t)

def raster(size,side=-1,zlo=28,zhi=60):
    for loops,vi in zip(tris,verts):
        pts=p[vi]
        if not np.all(c[vi]==5) or not np.all(pts[:,0]*side>0) or pts[:,2].max()<zlo or pts[:,2].min()>zhi:continue
        # Texel centers: pixel i samples UV (i+.5)/size.
        q=uv[loops]*size-.5;q[:,1]=size-1-q[:,1]
        lo=np.floor(q.min(0)).astype(int).clip(0,size-1);hi=np.ceil(q.max(0)).astype(int).clip(0,size-1)
        A=np.column_stack([q[0]-q[2],q[1]-q[2]])
        if abs(np.linalg.det(A))<1e-9:continue
        xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
        b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(A).T;b=np.dstack([b,1-b.sum(-1)])
        inside=(b>=-1e-6).all(-1)
        yield xx[inside],yy[inside],(b@pts)[inside],np.linalg.inv(A),pts

# The same continuous coordinate is evaluated on both sides of every UV seam.
# Smooth the leg's center/radius along its axis, avoiding per-face net changes.
left=p[(c==5)&(p[:,0]<0)]
surface=p[verts[(c[verts]==5).all(1)&(p[verts][:,:,0]<0).all(1)]]
sections=[]
for z in np.linspace(29.8,56,100):
    points=[]
    for tri in surface:
        for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            if (a[2]<=z<b[2]) or (b[2]<=z<a[2]):points.append(a+(b-a)*((z-a[2])/(b[2]-a[2])))
    q=np.array(points);lo=q[:,:2].min(0);hi=q[:,:2].max(0)
    sections.append([z,*((lo+hi)/2),*((hi-lo)/2)])
sections=np.array(sections); fits=[np.polyfit((sections[:,0]-42)/14,sections[:,i],3) for i in range(1,5)]

def coord(xyz):
    z=xyz[:,2];cx,cy,rx,ry=[np.polyval(f,(z-42)/14) for f in fits]
    dx=(xyz[:,0]-cx)/rx;dy=(xyz[:,1]-cy)/ry
    theta=np.arctan2(dy,dx)
    return theta,z,rx,ry

def ring_basis(theta):
    return np.column_stack([np.ones(len(theta)),np.cos(theta),np.sin(theta),np.cos(2*theta),np.sin(2*theta)])

# Lower garter follows a tilted ring. Stop the net inside that ring rather
# than at a horizontal plane, preserving the bare gap between both garters.
def fit_hem(component):
    garter=p[c==component];th,z,_,_=coord(garter);angles=[];heights=[]
    for k in range(16):
        a=(k/16*2-1)*np.pi;b=((k+1)/16*2-1)*np.pi
        zz=z[(th>=a)&(th<b)]
        if len(zz):angles.append((a+b)/2);heights.append(np.quantile(zz,.15))
    return np.linalg.lstsq(ring_basis(np.array(angles)),heights,rcond=None)[0]
hem=fit_hem(27);upper_hem=fit_hem(63)

def basis(xyz):
    theta,z,rx,ry=coord(xyz); zz=(z-42)/14
    return np.column_stack([np.ones(len(z)),zz,zz*zz,np.cos(theta),np.sin(theta),np.cos(2*theta),np.sin(2*theta),zz*np.cos(theta),zz*np.sin(theta)])

samples=[]; colors=[]
for x,y,xyz,_,_ in raster(4096,zlo=29.5,zhi=53):
    rgb=src[y,x]; ok=(xyz[:,2]>30)&(xyz[:,2]<52)&(rgb.min(1)>165)&((rgb.max(1)-rgb.min(1))<70)
    samples.append(xyz[ok]);colors.append(rgb[ok])
xyz=np.concatenate(samples);rgb=np.concatenate(colors).astype(float);B=basis(xyz)
assert len(xyz)>20000
donor_count=len(xyz)
coeff=[]
for channel in range(3):
    fit=np.linalg.lstsq(B,rgb[:,channel],rcond=None)[0]
    # A robust smooth skin field rejects blurred dark line edges.
    for _ in range(6):
        residual=rgb[:,channel]-B@fit;weight=np.clip(4/np.maximum(np.abs(residual),.01),0,1)
        weight*=np.where(residual<0,.35,1.)
        fit=np.linalg.lstsq(B*weight[:,None],rgb[:,channel]*weight,rcond=None)[0]
    coeff.append(fit)
coeff=np.array(coeff).T

def paint(xyz):
    theta,z,rx,ry=coord(xyz)
    radius=np.sqrt((rx*np.sin(theta))**2+(ry*np.cos(theta))**2)
    s=10*theta/(2*np.pi);v=(z-31)/4.8
    # Convert phase distance to cm normal to each strand, so thread width
    # stays consistent around the elliptical calf and through UV islands.
    grad=np.sqrt((10/(2*np.pi*radius))**2+(1/4.8)**2)
    a=np.abs((s+v+.5)%1-.5)/grad
    b=np.abs((s-v+.5)%1-.5)/grad
    dist=np.minimum(a,b)
    coverage=1-smooth((dist-(.085/2-.012))/.024)
    top=ring_basis(theta)@hem+.65
    coverage*=1-smooth((z-top)/.25)
    skin=np.clip(basis(xyz)@coeff,0,255)
    thread=np.tile([43.,38.,44.],(len(xyz),1))
    return skin*(1-coverage[:,None])+thread*coverage[:,None]

SIZE=8192
base=np.array(Image.fromarray(src).resize((SIZE,SIZE),Image.Resampling.BILINEAR))
out=base.copy(); mask=np.zeros((SIZE,SIZE),np.uint8)
for x,y,xyz,inv,pts in raster(SIZE):
    # Lower/upper transitions are hidden under the cuff and the garter.
    theta,z,_,_=coord(xyz)
    # Also clear the original baked garter shadow/projection in the bare gap.
    # Finish under the upper physical ring, where the transition is occluded.
    repair_top=ring_basis(theta)@upper_hem+.9
    alpha=smooth((xyz[:,2]-29.5)/.7)*smooth((repair_top-xyz[:,2])/.4)
    ok=alpha>0;x=x[ok];y=y[ok];xyz=xyz[ok];alpha=alpha[ok]
    if not len(x):continue
    color=np.zeros((len(x),3))
    # 4x4 subpixel integration in UV space; no post-sharpened dark fringes.
    for dx in [-.375,-.125,.125,.375]:
        for dy in [-.375,-.125,.125,.375]:
            db=inv@np.array([dx,dy]);dp=db[0]*(pts[0]-pts[2])+db[1]*(pts[1]-pts[2])
            color+=paint(xyz+dp)/16
    out[y,x]=np.rint(base[y,x]*(1-alpha[:,None])+color*alpha[:,None]).clip(0,255).astype(np.uint8)
    mask[y,x]=255

# Protect all occupied surfaces when padding newly authored seams.
occupied=np.zeros((SIZE,SIZE),np.uint8)
for loops,vi in zip(tris,verts):
    pts=p[vi]
    # Do not protect old padding belonging to the calf itself. Adjacent
    # non-target UV islands remain protected, including the other leg.
    if np.all(c[vi]==5) and np.all(pts[:,0]<0) and pts[:,2].max()>29.5 and pts[:,2].min()<59.5:continue
    q=uv[loops]*SIZE-.5;q[:,1]=SIZE-1-q[:,1]
    cv2.fillConvexPoly(occupied,np.rint(q).astype(np.int32),255)
# Crop before the distance transform; the calf islands span most of the atlas,
# but the operation remains bounded to this 8K texture.
edge=(mask>0).astype(np.uint8)
distance,labels=cv2.distanceTransformWithLabels(1-edge,cv2.DIST_L2,5,labelType=cv2.DIST_LABEL_PIXEL)
seeds=out[edge>0];pad=(distance<=10)&(occupied==0)&(labels>0)&(mask==0)
out[pad]=seeds[labels[pad]-1];mask[pad]=255
assert np.array_equal(out[mask==0],base[mask==0])
Image.fromarray(out).save(W/'T_Jirai_Base.png')
Image.fromarray(mask).save(W/'changed-mask.png')

# Rectified views reveal joins/spacing without baked lighting or UV distortion.
for name,im in [('before',src),('after',out)]:
    height=650;width=1050;preview=np.zeros((height,width,3),np.uint8)
    accum=np.zeros((height,width,3),float);count=np.zeros((height,width),np.int32)
    for x,y,xyz,_,_ in raster(im.shape[0],zlo=30,zhi=53):
        theta,z,_,_=coord(xyz);xx=np.clip(((theta+np.pi)/(2*np.pi)*(width-1)).astype(int),0,width-1)
        yy=np.clip(((53-z)/23*(height-1)).astype(int),0,height-1)
        np.add.at(accum,(yy,xx),im[y,x]);np.add.at(count,(yy,xx),1)
    valid=count>0;preview[valid]=np.rint(accum[valid]/count[valid,None]).astype(np.uint8)
    preview=cv2.inpaint(preview,(~valid).astype(np.uint8)*255,3,cv2.INPAINT_TELEA)
    Image.fromarray(preview).save(W/('unwrap-'+name+'.png'))

report=dict(source=str(SOURCE),source_sha256=sha(SOURCE),output_sha256=sha(W/'T_Jirai_Base.png'),
    source_size=4096,output_size=SIZE,target_component=5,target_side='negative X calf',
    z_range=[29.5,59.5],pattern_circumference_periods=10,vertical_period_cm=4.8,thread_width_cm=.085,
    supersamples_per_texel=16,skin_donor_samples=donor_count,changed_pixels=int((mask>0).sum()),
    source_bilinear_reconstruction_preserved_outside_mask=True,geometry_uv_weights_unchanged=True,
    purpose='Continuous 3D regular net replaces irregular baked strands; 8K doubles calf texel density to ~20 px/cm',
    center_radius_polynomials=[f.tolist() for f in fits],skin_coefficients=coeff.tolist(),
    top_boundary='net inside lower garter; skin cleanup ends under upper garter; bare gap preserved',
    garter_hem_coefficients=hem.tolist(),upper_garter_hem_coefficients=upper_hem.tolist())
(W/'atlas-report.json').write_text(json.dumps(report,indent=2))
print('FISHNET_ATLAS_AUTHORED',report['changed_pixels'],flush=True)
