"""Fit a closed strap to the actual skin; reuse bounded native accessory slots."""
from common import *
import numpy as np
from scipy.spatial import cKDTree
import importlib.util

spec=importlib.util.spec_from_file_location('native_reader',REPO/'models/jirai-face-v3/patch_native.py')
reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
parse_doc=reader.parse_doc;unpack=reader.unpack

def main():
 assert_baseline()
 old=np.load(PIN/'final-render.npz');d={k:old[k].copy() for k in old.files}
 p=old['positions'];tri=old['indices'].reshape(-1,3);mat=old['materials']
 _,weights,_,detail=parse_doc(read(PIN/'independent/native.json'))
 skin=tri[(mat[tri[:,0]]==0)&(p[tri,2].min(1)<171)&(p[tri,2].max(1)>165)]
 a=p[skin[:,0]].astype(float);e1=p[skin[:,1]]-a;e2=p[skin[:,2]]-a
 center=np.array([-.25,-7.55]);clearances=[]
 def skin_radius(theta,z):
  direction=np.array([np.sin(theta),np.cos(theta),0.]);origin=np.r_[center,z]
  h=np.cross(direction,e2);det=np.sum(e1*h,1);valid=abs(det)>1e-8
  inv=np.zeros(len(det));inv[valid]=1/det[valid]
  q=origin-a;u=np.sum(q*h,1)*inv;cross=np.cross(q,e1);v=np.sum(direction*cross,1)*inv
  dist=np.sum(e2*cross,1)*inv
  hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(dist>.1)
  assert hit.any(),(theta,z)
  radius=float(dist[hit].min());assert 2<radius<6.5,(theta,z,radius)
  return radius
 verts=[];faces=[]
 count=32
 for j in range(4):
  for i in range(count):
   theta=2*np.pi*i/count;z=168.1-1.0*np.cos(theta)+(.39 if j in [0,3] else -.39)
   radius=skin_radius(theta,z)+(.18 if j in [0,1] else .035)
   verts.append([center[0]+radius*np.sin(theta),center[1]+radius*np.cos(theta),z])
 for j in range(4):
  k=(j+1)%4
  for i in range(count):
   nxt=(i+1)%count;faces.extend([[j*count+i,j*count+nxt,k*count+nxt],[j*count+i,k*count+nxt,k*count+i]])
 # Reference heart is slightly to the wearer's left and sits on the front band.
 n=24;tt=np.arange(n)*2*np.pi/n
 heart=np.column_stack([16*np.sin(tt)**3,13*np.cos(tt)-5*np.cos(2*tt)-2*np.cos(3*tt)-np.cos(4*tt)])
 heart[:,0]/=32;heart[:,1]=(heart[:,1]-(heart[:,1].min()+heart[:,1].max())/2)/np.ptp(heart[:,1])
 hx=.30;hz=167.15
 def front_y(x,z):
  # Local front surface of the neck from horizontal ray/triangle intersection.
  origin=np.array([x,-7.55,z]);direction=np.array([0.,1.,0.]);h=np.cross(direction,e2);det=(e1*h).sum(1)
  inv=np.where(abs(det)>1e-8,1/np.where(abs(det)>1e-8,det,1),0);q=origin-a;u=(q*h).sum(1)*inv;cross=np.cross(q,e1);v=(direction*cross).sum(1)*inv;dist=(e2*cross).sum(1)*inv
  hit=(abs(det)>1e-8)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(dist>.1)
  assert hit.any();return float(origin[1]+dist[hit].min())
 y=front_y(hx,hz)+.33
 # Thin black bezel shares the strap section and its existing native shader.
 base=len(verts)
 for scale in [1.,.80]:
  for x,z in heart:verts.append([hx+x*1.92*scale,y,hz+z*1.83*scale])
 for i in range(n):
  j=(i+1)%n;faces.extend([[base+i,base+j,base+n+j],[base+i,base+n+j,base+n+i]])
 strap_p=np.array(verts);strap_t=np.array(faces)
 # Silver heart: outer contour, front bevel, and front/back fan caps.
 hp=[];hf=[]
 for scale,depth in [(1.,.025),(.82,.16)]:
  for x,z in heart:hp.append([hx+x*1.58*scale,y+depth,hz+z*1.49*scale])
 hp.extend([[hx,y+.22,hz],[hx,y+.025,hz]])
 for i in range(n):
  j=(i+1)%n;hf.extend([[i,j,n+j],[i,n+j,n+i],[n+i,n+j,2*n],[j,i,2*n+1]])
 selections={};copies=[];records=[]
 for material,newp,newt in [(16,strap_p,strap_t),(17,np.array(hp),np.array(hf))]:
  slots=np.where((mat[tri[:,0]]==material)&(p[tri,2].min(1)>165))[0]
  ids=np.unique(tri[slots]);selected=np.zeros(len(p),bool);selected[ids]=True
  assert not np.any(selected[tri].any(1)&~np.isin(np.arange(len(tri)),slots))
  assert len(newp)<=len(ids) and len(newt)<=len(slots)
  # Orient normals against native's reversed winding; retain UV constant inputs.
  cross=np.cross(newp[newt[:,1]]-newp[newt[:,0]],newp[newt[:,2]]-newp[newt[:,0]])
  if material==16:
   radial=newp[newt].mean(1)[:,:2]-center
   outer=np.arange(2*count);sign=np.median((cross[outer,:2]*radial[outer]).sum(1))
   if sign>0:newt=newt[:,[0,2,1]]
  else:
   front=np.arange(2,len(newt),4)
   if np.median(cross[front,1])>0:newt=newt[:,[0,2,1]]
  cross=np.cross(newp[newt[:,1]]-newp[newt[:,0]],newp[newt[:,2]]-newp[newt[:,0]])
  normal=np.zeros_like(newp)
  for k in range(3):np.add.at(normal,newt[:,k],-cross)
  normal=unit(normal);assert np.linalg.norm(normal,axis=1).min()>.99
  tangent=unit(np.cross(np.tile([0.,0.,1.],(len(newp),1)),normal))
  bad=np.linalg.norm(tangent,axis=1)<.5;tangent[bad]=[1.,0.,0.]
  d['positions'][ids]=newp[0];d['positions'][ids[:len(newp)]]=newp
  d['indices'].reshape(-1,3)[slots]=ids[0];d['indices'].reshape(-1,3)[slots[:len(newt)]]=ids[newt]
  d['packed_tangents'][ids[:len(newp)],:3]=np.rint(tangent*127).astype('i1').view('u1')
  d['packed_tangents'][ids[:len(newp)],4:7]=np.rint(normal*127).astype('i1').view('u1')
  donor=ids[cKDTree(p[ids]).query(newp)[1]]
  copies.extend(zip(ids[:len(newp)].tolist(),donor.tolist()))
  selections[f'vertices_{material}']=ids;selections[f'triangles_{material}']=slots
  records.append(dict(material=material,old_vertices=len(ids),old_triangles=len(slots),new_vertices=len(newp),new_triangles=len(newt)))
 d['normals']=d['packed_tangents'][:,4:7].view('i1').astype(float)/127
 np.savez_compressed(ROOT/'patched-render.npz',**d)
 np.savez_compressed(ROOT/'author-selections.npz',**selections,weight_copies=np.array(copies))
 write(ROOT/'author-report.json',dict(passed=True,source_native_sha256=sha(PIN/'final-render.npz'),native_sha256=sha(ROOT/'patched-render.npz'),groups=records,closed_strap_segments=count,skin_clearance_outer_cm=.18,skin_clearance_inner_cm=.035,strap_height_cm=.78,heart_width_cm=1.58,heart_height_cm=1.49,original_uvs_exact=True,original_materials_exact=True,game_runtime_tested=False))
 print('CHOKER_AUTHORED',records,flush=True)

if __name__=='__main__':main()
