"""Construct a smooth layered heart, raised cross and two beveled hair clips."""
from common import *
import numpy as np,cv2,collections
from PIL import Image
from patch_native import parse_doc,unpack

def main():
 assert_installed_baseline()
 d=np.load(FACE/'native/final-render.npz');source=np.load(FACE/'surface.npz');src=d['source_index']
 selected=(src>=0)&np.isin(source['components'][np.maximum(src,0)],[22,34,132])
 ids=np.where(selected)[0];tri=d['indices'].reshape(-1,3);tm=selected[tri].all(1)
 assert not np.any(selected[tri].any(1)&~tm)
 _,weights,_,detail=parse_doc(read(FACE/'native/final.json'))
 assert all(weights[i]=={'head':1.0} for i in ids)
 assert np.all(d['materials'][ids]==1)
 # A planar badge follows the original accessory plane, avoiding an arbitrary
 # front-facing billboard. All coordinates are native UE centimeters.
 normal=unit(np.array([.77235618,.63438271,.03200808]))
 u=unit(np.cross(normal,[0,0,1]));v=unit(np.cross(u,normal))
 center=np.array([9.09648024,1.35213961,185.58242348])
 angle=np.deg2rad(10);rot=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
 verts=[];norms=[];uv=[];faces=[];groups=[]
 # New UVs occupy one empty tile of the hair material. Other materials keep
 # Face3's texture; retained hair UVs stay fixed, with local deprojection below.
 occupied=np.zeros((8192,8192),np.uint8)
 for t in tri[(d['materials'][tri[:,0]]==1)&~tm]:
  q=d['uv'][t,0].astype(float)*8191
  cv2.fillConvexPoly(occupied,np.rint(q).astype('i4'),255)
 chosen=None
 for yy in range(96,8192-1152,128):
  for xx in range(96,8192-1152,128):
   if not occupied[yy-32:yy+1120,xx-32:xx+1120].any():chosen=(xx,yy);break
  if chosen:break
 assert chosen,'No isolated hair UV tile'
 tx,ty=chosen
 # Pink panel occupies the first 768 square; uniform dark shades have wide
 # padding so half-float UV rounding and mips cannot pull in other colors.
 def texcoord(x,y,color):
  if color=='pink':q=np.array([tx+48+(x/5.9+.5)*704,ty+48+(.5-y/3.9)*704])
  else:q=np.array([tx+920,ty+{'black':112,'edge':400,'back':688}[color]])
  return q/8191
 def add(x,y,z,n,color):
  r=rot@np.array([x,y]);world=center+u*r[0]+v*r[1]+normal*z
  nr=rot@np.array(n[:2]);nw=unit(u*nr[0]+v*nr[1]+normal*n[2])
  verts.append(world);norms.append(nw);uv.append(texcoord(x,y,color));return len(verts)-1
 n=72;t=np.arange(n)*2*np.pi/n
 outline=np.column_stack([16*np.sin(t)**3,13*np.cos(t)-5*np.cos(2*t)-2*np.cos(3*t)-np.cos(4*t)])
 outline[:,0]*=5.9/32
 outline[:,1]=(outline[:,1]-(outline[:,1].max()+outline[:,1].min())/2)*3.9/np.ptp(outline[:,1])
 scallop=1+.018*(1-np.cos(18*t))
 rings=[]
 for scale,depth,color,side in [(.965,-.10,'back',-.6),(1.,.015,'black',1.),(.945,.18,'edge',.25),(.815,.22,'pink',.04)]:
  ring=[]
  for i,(x,y) in enumerate(outline):
   amp=scallop[i] if color!='pink' else 1.
   rad=unit(np.array([x/2.95,y/1.95]))
   nrm=[rad[0]*side,rad[1]*side,1. if color!='back' else -.7]
   ring.append(add(x*scale*amp,y*scale*amp,depth,nrm,color))
  rings.append(ring)
 for a,b in zip(rings[:-1],rings[1:]):
  for i in range(n):
   j=(i+1)%n;faces.extend([[a[i],a[j],b[j]],[a[i],b[j],b[i]]])
 front=add(0,0,.285,[0,0,1],'pink');back=add(0,0,-.10,[0,0,-1],'back')
 for i in range(n):
  j=(i+1)%n;faces.extend([[rings[-1][i],rings[-1][j],front],[rings[0][j],rings[0][i],back]])
 groups.append(dict(name='heart',vertex_end=len(verts),triangle_end=len(faces)))
 def bar(name,cx,cy,length,width,degrees,depth):
  a=np.deg2rad(degrees);axis=np.array([np.cos(a),np.sin(a)]);across=np.array([-axis[1],axis[0]])
  # Eight contour points retain a small bevel at every corner.
  l=length/2;w=width/2;b=min(.045,w*.5)
  points=np.array([[-l+b,-w],[l-b,-w],[l,-w+b],[l,w-b],[l-b,w],[-l+b,w],[-l,w-b],[-l,-w+b]])
  ring=[]
  for scale,z,col,ns in [(1.,depth,'black',.8),(1.,depth+.06,'black',.7),(.86,depth+.11,'edge',.05)]:
   row=[]
   for xx,yy in points:
    q=np.array([cx,cy])+axis*xx*scale+across*yy*scale
    radial=unit(axis*(xx/l)+across*(yy/w));row.append(add(*q,z,[*list(radial*ns),1.],col))
   ring.append(row)
  for arow,brow in zip(ring[:-1],ring[1:]):
   for i in range(8):
    j=(i+1)%8;faces.extend([[arow[i],arow[j],brow[j]],[arow[i],brow[j],brow[i]]])
  f=add(cx,cy,depth+.11,[0,0,1],'black');bk=add(cx,cy,depth,[0,0,-1],'black')
  for i in range(8):
   j=(i+1)%8;faces.extend([[ring[-1][i],ring[-1][j],f],[ring[0][j],ring[0][i],bk]])
  groups.append(dict(name=name,vertex_end=len(verts),triangle_end=len(faces)))
 bar('cross-vertical',0,.02,2.35,.22,90,.34)
 bar('cross-horizontal',0,.38,1.84,.22,0,.345)
 bar('pin-long',-.6,-2.85,3.10,.25,55,.04)
 bar('pin-short',-.6,-2.85,3.20,.24,-10,.0)
 p=np.array(verts);normal_values=np.array(norms);tex=np.array(uv,dtype='<f2');f=np.array(faces,int)
 assert len(p)<=len(ids) and len(f)<=tm.sum()
 # Orient each entire closed solid, rather than choosing triangle winding
 # from radial normals (which can reverse at the heart's concave notch).
 edges=collections.defaultdict(list)
 for i,face in enumerate(f):
  for a,b in zip(face,np.roll(face,-1)):edges[tuple(sorted((int(a),int(b))))].append((i,int(a)<int(b)))
 assert all(len(rows)==2 for rows in edges.values())
 graph=collections.defaultdict(list)
 for (a,sa),(b,sb) in edges.values():graph[a].append((b,sa==sb));graph[b].append((a,sa==sb))
 flip={};components=[]
 for seed in range(len(f)):
  if seed in flip:continue
  flip[seed]=False;pending=[seed];part=[]
  while pending:
   i=pending.pop();part.append(i)
   for j,toggle in graph[i]:
    expected=flip[i]^toggle
    if j in flip:assert flip[j]==expected
    else:flip[j]=expected;pending.append(j)
  components.append(part)
 changed=np.array([flip[i] for i in range(len(f))]);f[changed]=f[changed][:,[0,2,1]]
 # Native winding has opposite handedness to its outward normal vectors.
 for part in components:
  part=np.array(part);q=p[f[part]];volume=np.sum(np.einsum('ij,ij->i',q[:,0],np.cross(q[:,1],q[:,2])))/6
  assert abs(volume)>1e-4
  if volume>0:f[part]=f[part][:,[0,2,1]]
 cross=np.cross(p[f[:,1]]-p[f[:,0]],p[f[:,2]]-p[f[:,0]])
 assert np.min(np.linalg.norm(cross,axis=1))>1e-7
 smooth=np.zeros_like(p)
 for corner in range(3):np.add.at(smooth,f[:,corner],-cross)
 normal_values=unit(smooth)
 assert np.linalg.norm(normal_values,axis=1).min()>.99
 indices=d['indices'].copy().reshape(-1,3);triangle_slots=np.where(tm)[0]
 indices[triangle_slots[:len(f)]]=ids[f];indices[triangle_slots[len(f):]]=ids[0]
 positions=d['positions'].copy();positions[ids]=center-normal*.05;positions[ids[:len(p)]]=p
 frames=d['packed_tangents'].copy();nn=np.tile(normal,(len(ids),1));nn[:len(p)]=normal_values
 tangent=unit(u-nn*np.sum(nn*u,axis=1,keepdims=True))
 frames[ids,:3]=np.rint(tangent*127).astype('i1').view('u1');frames[ids,4:7]=np.rint(nn*127).astype('i1').view('u1')
 texcoord_values=d['uv'].copy();texcoord_values[ids,0]=texcoord(0,0,'black');texcoord_values[ids[:len(p)],0]=tex
 # Paint the isolated new tile and the masked carrier projection only.
 im=np.array(Image.open(FACE/'T_Jirai_Base.png').convert('RGB'));out=im.copy()
 # The old badge was also baked into the carrier hair. Remove that dark
 # projection only on the head-facing hair surface under the original badge,
 # using neighboring atlas hair colors rather than leaving a ghost silhouette.
 carrier=np.zeros((8192,8192),np.uint8);under_pins=carrier.copy()
 basis=np.array([u,v,normal]);local=(d['positions']-center)@basis.T
 for face in tri[(d['materials'][tri[:,0]]==1)&~tm]:
  q3=local[face]
  if q3[:,0].min()>3.7 or q3[:,0].max()<-3.7 or q3[:,1].min()>2.9 or q3[:,1].max()<-4.6 or q3[:,2].max()<-1.25:continue
  if d['normals'][face].mean(0)@normal<.05:continue
  q=d['uv'][face,0].astype(float)*8191;lo=np.floor(q.min(0)).astype(int).clip(0,8191);hi=np.ceil(q.max(0)).astype(int).clip(0,8191)
  a=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(a))<1e-9:continue
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1))
  b=(np.stack([xx,yy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)]);where=(b>=-1e-6).all(-1)
  xyz=(b@q3)[where];ok=(np.abs(xyz[:,0])<3.7)&(xyz[:,1]>-4.6)&(xyz[:,1]<2.9)&(xyz[:,2]>-1.25)&(xyz[:,2]<.25)
  carrier[yy[where][ok],xx[where][ok]]=255
  pin_zone=ok&(xyz[:,1]<-1.75)&(np.abs(xyz[:,0])<3.15)
  under_pins[yy[where][pin_zone],xx[where][pin_zone]]=255
 dark=(((carrier>0)&(im.mean(2)<170))|(under_pins>0)).astype('u1')*255
 dark=cv2.dilate(dark,np.ones((7,7),np.uint8));dark[carrier==0]=0
 filled=cv2.inpaint(im,dark,10,cv2.INPAINT_TELEA)
 out[dark>0]=filled[dark>0]
 out[ty:ty+1088,tx:tx+1088]=[25,23,29]
 yy,xx=np.mgrid[:800,:800];soft=np.exp(-((xx-245)/450)**2-((yy-175)/470)**2)
 panel=np.array([238,111,162])[None,None,:]+soft[:,:,None]*np.array([12,31,24])[None,None,:]
 out[ty:ty+800,tx:tx+800]=np.rint(panel).astype('u1')
 for name,color in [('black',[24,22,29]),('edge',[39,36,46]),('back',[20,19,25])]:
  cy={'black':112,'edge':400,'back':688}[name]
  out[ty+cy-96:ty+cy+96,tx+816:tx+1024]=color
 allowed=np.zeros((8192,8192),bool);allowed[ty:ty+1088,tx:tx+1088]=True;allowed|=dark>0
 assert not np.any(np.any(out!=im,axis=2)&~allowed),'Unrelated hair UVs were repainted'
 Image.fromarray(dark).save(ROOT/'hair-deprojection-mask.png')
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png')
 fields={k:d[k] for k in d.files};fields.update(positions=positions,indices=indices.ravel(),packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127,uv=texcoord_values)
 np.savez_compressed(ROOT/'patched-render.npz',**fields)
 np.savez_compressed(ROOT/'authored-geometry.npz',positions=p,normals=normal_values,uv=tex,triangles=f,selected_vertices=ids,selected_triangles=triangle_slots,basis=np.array([u,v,normal]),center=center)
 write(ROOT/'author-report.json',dict(passed=True,source_components=[22,34,132],old_native_vertices=len(ids),old_triangles=int(tm.sum()),new_vertices=len(p),new_triangles=len(f),inactive_vertex_slots=len(ids)-len(p),inactive_degenerate_triangle_slots=int(tm.sum())-len(f),groups=groups,
  head_weights_exact=True,uv1_exact=True,closed_consistently_oriented_solids=len(components),unrelated_hair_texels_exact=True,carrier_hair_deprojection_texels=int(np.count_nonzero(dark)),texture_sha256=sha(ROOT/'T_Jirai_Base.png'),uv_tile=[tx,ty,1088,1088],
  native_source_sha256=sha(FACE/'native/final-render.npz'),game_runtime_tested=False))
 write(ROOT/'atlas-report.json',dict(source_sha256=sha(FACE/'T_Jirai_Base.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),carrier_hair_deprojection_texels=int(np.count_nonzero(dark)),uv_tile=[tx,ty,1088,1088]))
 print('HAIRPIN_AUTHORED',len(p),len(f),'tile',chosen,'hair repair',np.count_nonzero(dark))
if __name__=='__main__':main()
