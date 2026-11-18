"""Repair expression, procedural surface-owned skin, halo and arm continuity."""
from common import *
import numpy as np,collections,cv2
from PIL import Image

def boundary_loops(d):
 p=d['positions'];tri=d['indices'].reshape(-1,3);tri=tri[d['materials'][tri[:,0]]==0]
 up,inv=np.unique(np.round(p,4),axis=0,return_inverse=True);t=inv[tri]
 edges=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);edges.sort(1);e,n=np.unique(edges,axis=0,return_counts=True)
 g=collections.defaultdict(set)
 for a,b in e[n==1]:g[int(a)].add(int(b));g[int(b)].add(int(a))
 seen=set();loops=[]
 for k in list(g):
  if k in seen:continue
  todo=[k];part=[]
  while todo:
   a=todo.pop()
   if a in seen:continue
   seen.add(a);part.append(a);todo.extend(g[a]-seen)
  q=up[part]
  if q[:,2].min()<137 or q[:,2].max()>157 or abs(q[:,0].mean())<13:continue
  assert all(len(g[a])==2 for a in part)
  order=[k];prev=-1;cur=k
  while True:
   nxt=next(x for x in sorted(g[cur]) if x!=prev)
   if nxt==k:break
   order.append(nxt);prev,cur=cur,nxt
   assert len(order)<=len(part)
  assert len(order)==len(part)
  ids=np.array([next(int(i) for i in np.where((inv==a)&(d['materials']==0))[0]) for a in order])
  loops.append(ids)
 return loops

def main():
 assert_baseline();d=np.load(PIN/'final-render.npz');s=np.load(FACE/'surface.npz')
 p=d['positions'].copy();old=p.copy();frames=d['packed_tangents'].copy();tex=d['uv'].copy();tri=d['indices'].reshape(-1,3).copy();mat=d['materials'];src=d['source_index'];c=np.where(src>=0,s['components'][np.maximum(src,0)],-1)
 # Preserve the continuous mouth geometry and repaint a shorter, softer lip line.
 mouth=(mat==0)&(abs(old[:,0]+.35)<2.85)&(old[:,2]>170.35)&(old[:,2]<172.65)&(old[:,1]>-.7)
 # Coherent affine eye deformation includes the orbital skin, attached lash
 # strip and closed sclera. Keep the independent iris a little taller so the
 # upper/lower lids partially frame it rather than exposing a circular disc.
 eye=np.zeros(len(p),bool)
 for cx in [-5.317217,4.614422]:
  dx=abs(old[:,0]-cx)
  region=np.isin(mat,[0,18,19])&(dx<3.7)&(old[:,2]>174.5)&(old[:,2]<180.7)&(old[:,1]>-.3)
  amount=np.clip((180.7-old[:,2])/.8,0,1)*np.clip((old[:,2]-174.5)/.7,0,1)*np.clip((3.7-dx)/.6,0,1)
  factor=np.where(mat==18,.82,.69)
  shift=(177.95+(old[:,2]-177.799362)*factor)-old[:,2]
  p[region,2]+=shift[region]*amount[region]
  xfactor=np.where(mat==18,.97,.87)
  p[region,0]+=(old[region,0]-cx)*(xfactor[region]-1)*amount[region]
  eye|=region
 # Remove pale detached lower-lash lumps; the coherent lid supplies the edge.
 lower=np.isin(c,[125,126,128,136]);p[lower,1]=-1.0;eye|=lower
 # Halo: fit both actual native meshes, use JK's plane and roundness instead
 # of preserving the narrow, nearly vertical ellipse from the source image.
 ids=np.where(mat==8)[0];q=old[ids];center=(q.min(0)+q.max(0))/2
 _,a=np.linalg.eigh(np.cov(q.T));jk=np.load(PAT/'jk-native.npz');jq=jk['positions'][(jk['materials']==1)&(jk['positions'][:,2]>190)]
 _,b=np.linalg.eigh(np.cov(jq.T))
 if np.linalg.det(a)<0:a[:,0]*=-1
 if np.linalg.det(b)<0:b[:,0]*=-1
 local=(q-center)@a;scale=np.array([1.,2.20,.90]);target_center=np.array([-7.,-5.5,210.8])
 p[ids]=target_center+(local*scale)@b.T
 normal=unit(frames[ids,4:7].view('i1').astype(float)/127@a/scale@b.T)
 tangent=unit(frames[ids,:3].view('i1').astype(float)/127@a*scale@b.T)
 tangent=unit(tangent-normal*np.sum(tangent*normal,axis=1,keepdims=True))
 frames[ids,4:7]=np.rint(normal*127).astype('i1').view('u1');frames[ids,:3]=np.rint(tangent*127).astype('i1').view('u1')
 # Reuse buried old iris highlight fragments in the same Skin section. Their
 # triangle/vertex counts stay fixed; copy actual boundary skin weights later.
 reserve=np.isin(c,[131,135,139,141]);vid=np.where(reserve)[0];slots=np.where(reserve[tri].all(1))[0]
 assert not np.any(reserve[tri].any(1)&~reserve[tri].all(1))
 loops=boundary_loops(d);assert len(loops)==4
 copies=[];newfaces=[];bridges=[];used=0
 _,weld=np.unique(np.round(old,4),axis=0,return_inverse=True);source_edges={}
 for face in d['indices'].reshape(-1,3)[mat[d['indices'].reshape(-1,3)[:,0]]==0]:
  ff=weld[face]
  for aa_,bb_ in zip(ff,np.roll(ff,-1)):source_edges[tuple(sorted((int(aa_),int(bb_))))]=int(aa_)<int(bb_)
 for sign in [-1,1]:
  rings=[v for v in loops if np.sign(old[v,0].mean())==sign];assert len(rings)==2
  rings.sort(key=lambda v:old[v,2].mean(),reverse=True);upper,lower=rings
  axis=unit(old[lower].mean(0)-old[upper].mean(0));u=unit(np.cross(axis,[0,0,1]));v=np.cross(axis,u)
  def angles(ring):
   q=old[ring]-old[ring].mean(0)
   if np.sum(np.cross(q,np.roll(q,-1,axis=0))@axis)<0:ring=ring[::-1];q=q[::-1]
   theta=np.arctan2(q@v,q@u);start=int(np.argmin(abs(theta)));ring=np.roll(ring,-start);q=old[ring]
   lengths=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1);arc=np.r_[0,np.cumsum(lengths[:-1])]/lengths.sum()*2*np.pi
   return ring,arc
  upper,aa=angles(upper);lower,bb=angles(lower)
  ru=vid[used:used+len(upper)];used+=len(upper);rl=vid[used:used+len(lower)];used+=len(lower)
  for arow,brow in [(ru,upper),(rl,lower)]:
   p[arow]=old[brow];frames[arow]=d['packed_tangents'][brow];copies.extend(zip(arow.tolist(),brow.tolist()))
  # Merge cumulative arc samples without changing either boundary order.
  i=j=0;part=[]
  while i<len(ru) or j<len(rl):
   na=aa[(i+1)%len(ru)]+(2*np.pi if i+1>=len(ru) else 0) if i<len(ru) else np.inf
   nb=bb[(j+1)%len(rl)]+(2*np.pi if j+1>=len(rl) else 0) if j<len(rl) else np.inf
   if na<nb:part.append([ru[i%len(ru)],rl[j%len(rl)],ru[(i+1)%len(ru)]]);i+=1
   else:part.append([ru[i%len(ru)],rl[j%len(rl)],rl[(j+1)%len(rl)]]);j+=1
  part=np.array(part);cross=np.cross(p[part[:,1]]-p[part[:,0]],p[part[:,2]]-p[part[:,0]])
  edge=tuple(sorted((int(weld[upper[0]]),int(weld[upper[1]]))))
  original_forward=source_edges[edge]==(int(weld[upper[0]])<int(weld[upper[1]]))
  candidate_forward=next(a==ru[0] and b==ru[1] for ff in part for a,b in zip(ff,np.roll(ff,-1)) if {int(a),int(b)}=={int(ru[0]),int(ru[1])})
  if candidate_forward==original_forward:part=part[:,[0,2,1]]
  newfaces.extend(part.tolist());bridges.append(dict(side=sign,upper_vertices=len(ru),lower_vertices=len(rl),triangles=len(part),upper_original=upper.tolist(),lower_original=lower.tolist(),new_vertices=np.r_[ru,rl].tolist()))
 assert len(newfaces)<=len(slots) and used<=len(vid)
 tri[slots[:len(newfaces)]]=newfaces;tri[slots[len(newfaces):]]=vid[-1]
 p[vid[used:]]=p[vid[0]]
 # Cut away jagged eye skin and stitch a replacement to the actual head
 # boundary. Shared seam vertices prevent floating surfaces and cracks.
 from connected_lids import rebuild
 rim_mask=np.isin(c,[125,126,128,136])
 ni=np.where(eye&~rim_mask&~reserve)[0];n=d['normals'][ni].copy();factor=np.where(mat[ni]==18,.82,.69);n[:,2]/=factor;n[:,0]/=np.where(mat[ni]==18,.97,.87);n=unit(n)
 tangent=frames[ni,:3].view('i1').astype(float)/127;tangent=unit(tangent-n*np.sum(tangent*n,axis=1,keepdims=True))
 frames[ni,4:7]=np.rint(n*127).astype('i1').view('u1');frames[ni,:3]=np.rint(tangent*127).astype('i1').view('u1')
 rim_ids,rim_slots,rim_faces,rim_used,eye_seams=rebuild(d,c,p,frames,tri,copies,eye)
 count=0;mouth_faces=np.empty((0,3),int)
 # Replace baked patches with a continuous head chart and a uniform body tile.
 # Their transition lies below facial patterns; UV1 and other materials stay fixed.
 skin=mat==0;head=skin&(p[:,2]>166)
 tex[skin,0]=[.90,.90]
 tex[head,0,0]=(128+(p[head,0]+12)/24*3840)/8191
 tex[head,0,1]=(128+(193-p[head,2])/27*3840)/8191
 assert np.all((tex[skin,0]>0)&(tex[skin,0]<1))
 im=np.array(Image.open(FACE/'T_Jirai_Base.png').convert('RGB'));out=np.empty_like(im);out[:]=[247,225,224]
 for start in range(64,4032,256):
  end=min(start+256,4032);yy,xx=np.mgrid[start:end,64:4032];x=(xx-128)/3840*24-12;z=193-(yy-128)/3840*27
  color=np.zeros((*x.shape,3),np.float32)+np.array([247,225,224],np.float32)
  blush=np.exp(-((abs(x+.35)-5.7)/2.1)**2-((z-174.8)/1.30)**2)*.18
  color=color*(1-blush[:,:,None])+np.array([244,172,182])*blush[:,:,None]
  for cx in [-5.317217,4.614422]:
   dx=x-cx;outward=dx*(-1 if cx<0 else 1)
   lid=177.95+np.sqrt(np.clip(1-(dx/2.55)**2,0,1))+.075*outward
   line=np.exp(-((z-lid-.055)/.115)**4)*np.clip((2.72-abs(dx))/.30,0,1)
   color=color*(1-line[:,:,None])+np.array([62,38,43])*line[:,:,None]
   brow=np.exp(-((z-181.9)/.06)**4)*np.clip((2.6-abs(dx))/.5,0,1)
   color=color*(1-brow[:,:,None])+np.array([107,72,78])*brow[:,:,None]
  curve=171.64+.035*(x+.35)**2
  lip=np.exp(-((z-curve)/.075)**2)*np.clip((1.80-abs(x+.35))/.48,0,1)*.62
  color=color*(1-lip[:,:,None])+np.array([190,116,126])*lip[:,:,None]
  out[start:end,64:4032]=np.rint(color).clip(0,255).astype('u1')
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png')
 # Keep the established mouth frames exact.
 mi=np.where(mouth)[0];frames[mi]=d['packed_tangents'][mi]
 tx=ty=64;size=3968
 fields={k:d[k] for k in d.files};fields.update(positions=p.astype('<f4'),indices=tri.ravel(),packed_tangents=frames,normals=frames[:,4:7].view('i1').astype(float)/127,uv=tex)
 np.savez_compressed(ROOT/'patched-render.npz',**fields)
 np.savez_compressed(ROOT/'author-selections.npz',eye=eye,head=head,mouth=mouth,halo=ids,reserve=np.r_[vid,rim_ids],slots=np.r_[slots,rim_slots],weight_copies=np.array(copies),bridge_triangles=np.array(newfaces),mouth_triangles=mouth_faces,rim_triangles=rim_faces,eye_seams=np.array(eye_seams))
 write(ROOT/'author-report.json',dict(passed=True,source_native_sha256=sha(PIN/'final-render.npz'),native_sha256=sha(ROOT/'patched-render.npz'),atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),head_uv_vertices=int(head.sum()),mouth_geometry_preserved_vertices=int(mouth.sum()),mouth_backing_triangles=count,skin_uv_vertices=int(skin.sum()),skin_chart='continuous planar head chart, uniform body tile; chart transitions below face patterns',eyelid_patch_triangles=len(rim_faces),eyelid_patch_vertices=len(rim_used),eyelid_seam_vertices=len(eye_seams),replaced_eye_triangle_slots=len(rim_slots),inactive_eye_triangle_slots=len(rim_slots)-len(rim_faces),halo_vertices=len(ids),halo_plane_from_jk_native=True,halo_in_plane_scale=[2.2,.9],reserve_vertices=len(vid),reserve_triangles=len(slots),bridge_vertices=used,bridge_triangles=len(newfaces),bridges=bridges,face_tile=[tx,ty,size,size],game_runtime_tested=False))
 write(ROOT/'atlas-report.json',dict(source_sha256=sha(FACE/'T_Jirai_Base.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),changed_pixels=int(np.any(out!=im,axis=2).sum()),face_surface_projection=True))
 print('POLISH_AUTHORED',used,len(newfaces))
if __name__=='__main__':main()
