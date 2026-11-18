"""User-selected source combination; no eyelid or mouth-shape redesign."""
from common import *
import numpy as np, cv2
from PIL import Image

def main():
 assert_baseline()
 face2=REPO/'private/jirai-face-v2';polish=REPO/'private/jirai-polish-v1'
 a=np.load(FACE/'native/baseline-render.npz');b=np.load(PIN/'final-render.npz');c=np.load(polish/'final-render.npz');s=np.load(polish/'author-selections.npz');report=read(polish/'author-report.json')
 d={k:b[k].copy() for k in b.files};mat=b['materials'];skin=mat==0;halo=mat==8
 # Restore every Skin position/UV/frame and triangle from Face2 before adding
 # only the independently verified arm bridges from the rejected candidate.
 for key in ['positions','packed_tangents','uv']:d[key][skin]=a[key][skin]
 tri=d['indices'].reshape(-1,3);at=a['indices'].reshape(-1,3)
 skin_slots=np.where(mat[at[:,0]]==0)[0];assert np.array_equal(tri[skin_slots],at[skin_slots])
 tri[skin_slots]=at[skin_slots]
 for key in ['positions','packed_tangents']:d[key][halo]=c[key][halo]
 src=b['source_index'];surf=np.load(FACE/'surface.npz');comp=np.where(src>=0,surf['components'][np.maximum(src,0)],-1)
 reserve=np.where(skin&np.isin(comp,[131,135,139,141]))[0]
 slots=np.where(np.isin(tri,reserve).all(1))[0];assert len(reserve)==194 and len(slots)==88
 bridge_ids=np.array([i for row in report['bridges'] for i in row['new_vertices']])
 copies=np.array([(int(dst),int(source)) for dst,source in s['weight_copies'] if dst in set(bridge_ids.tolist())],dtype=int)
 assert len(copies)==len(bridge_ids)==67
 for key in ['positions','packed_tangents']:d[key][reserve]=c[key][reserve]
 tri[slots]=c['indices'].reshape(-1,3)[slots]
 # The Face2 albedo has no black texels in the visible mouth. The original
 # small lip facets instead carry normals pointing away from the face. Clean
 # only their shading, preserving every vertex, UV, triangle and lip pigment.
 p=a['positions'];mouth=skin&(abs(p[:,0]+.35)<2.7)&(p[:,2]>170.6)&(p[:,2]<172.45)&(p[:,1]>2.5)
 ids=np.where(mouth)[0];old=d['packed_tangents'][ids];n=old[:,4:7].view('i1').astype(float)/127
 target=unit(np.column_stack([.18*(p[ids,0]+.35),np.ones(len(ids)),np.full(len(ids),-.22)]))
 blend=np.clip((2.7-abs(p[ids,0]+.35))/.35,0,1)*np.clip((p[ids,2]-170.6)/.25,0,1)*np.clip((172.45-p[ids,2])/.25,0,1)
 n=unit(n*(1-blend[:,None])+target*blend[:,None]);tangent=old[:,:3].view('i1').astype(float)/127
 tangent=unit(tangent-n*np.sum(tangent*n,axis=1,keepdims=True))
 d['packed_tangents'][ids,4:7]=np.rint(n*127).astype('i1').view('u1');d['packed_tangents'][ids,:3]=np.rint(tangent*127).astype('i1').view('u1')
 # Find an unused Skin albedo region. A local constant tile cannot spill
 # across the atlas as an interpolated arm UV triangle otherwise would.
 im=np.array(Image.open(face2/'T_Jirai_Base.png').convert('RGB'));out=im.copy();occupied=np.zeros((8192,8192),np.uint8)
 for f in tri[mat[tri[:,0]]==0]:
  if np.isin(f,reserve).any():continue
  q=np.rint(d['uv'][f,0].astype(float)*8191).astype('i4');cv2.fillConvexPoly(occupied,q,255)
 distance=cv2.distanceTransform(255-occupied,cv2.DIST_L2,5);distance[:32]=0;distance[-32:]=0;distance[:,:32]=0;distance[:,-32:]=0
 y,x=np.unravel_index(np.argmax(distance),distance.shape);assert distance[y,x]>12
 donors=np.array([source for _,source in copies]);uv=np.rint(a['uv'][donors,0].astype(float)*8191).astype(int).clip(0,8191)
 color=np.rint(np.median(im[uv[:,1],uv[:,0]],axis=0)).astype('u1');assert color.min()>170
 out[y-8:y+9,x-8:x+9]=color;assert not occupied[y-8:y+9,x-8:x+9].any()
 d['uv'][reserve,0]=np.array([x/8191,y/8191],dtype=d['uv'].dtype)
 d['normals']=d['packed_tangents'][:,4:7].view('i1').astype(float)/127
 Image.fromarray(out).save(ROOT/'T_Jirai_Base.png');np.savez_compressed(ROOT/'patched-render.npz',**d)
 np.savez_compressed(ROOT/'author-selections.npz',reserve=reserve,slots=slots,bridge_ids=bridge_ids,weight_copies=copies,bridge_triangles=s['bridge_triangles'],mouth_shading=ids,halo=np.where(halo)[0])
 write(ROOT/'author-report.json',dict(passed=True,native_sha256=sha(ROOT/'patched-render.npz'),atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),face2_native_sha256=sha(FACE/'native/baseline-render.npz'),face3_native_sha256=sha(PIN/'final-render.npz'),polish_native_sha256=sha(polish/'final-render.npz'),face2_geometry_restored=True,eye_socket_unmodified=True,mouth_geometry_unmodified=True,mouth_albedo_unmodified=True,mouth_shading_vertices=len(ids),bridge_vertices=len(bridge_ids),bridge_triangles=len(s['bridge_triangles']),bridges=report['bridges'],arm_tile_xy=[int(x),int(y)],arm_tile_rgb=color.tolist(),game_runtime_tested=False))
 write(ROOT/'atlas-report.json',dict(source_sha256=sha(face2/'T_Jirai_Base.png'),output_sha256=sha(ROOT/'T_Jirai_Base.png'),changed_pixels=int(np.any(out!=im,2).sum()),face2_all_original_skin_texels_exact=True,only_unused_arm_tile_added=True))
 print('HYBRID_AUTHORED',len(ids),color.tolist(),flush=True)

if __name__=='__main__':main()
