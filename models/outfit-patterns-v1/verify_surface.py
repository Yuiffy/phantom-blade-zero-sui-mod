"""Check edited PNG pixels against native UV ownership and frozen source data."""
from common import *
from surface import ownership
from PIL import Image
import numpy as np,cv2

def main():
 assert_baseline();source=read(ROOT/'sources.json');atlas=read(ROOT/'atlas-report.json');rows={}
 for outfit in ['jk','jirai']:
  assert sha(ROOT/f'{outfit}-native.npz')==source[f'{outfit}_native_sha256']
  assert sha(ROOT/f'{outfit}-before.png')==source[f'{outfit}_atlas_sha256']
  assert sha(ROOT/f'{outfit}-after.png')==atlas['outfits'][outfit]['output_sha256']
  a=np.asarray(Image.open(ROOT/f'{outfit}-before.png'));b=np.asarray(Image.open(ROOT/f'{outfit}-after.png'));assert a.shape==b.shape
  if outfit=='jk':
   original=np.asarray(Image.open(ROOT/'jk-original-4k.png'))
   assert sha(ROOT/'jk-original-4k.png')==source['jk_original_4k_sha256']
   assert np.array_equal(a,original.repeat(2,axis=0).repeat(2,axis=1))
  changed=np.any(a!=b,axis=2);mask=np.asarray(Image.open(ROOT/f'{outfit}-edit-mask.png'))>0;assert not np.any(changed&~mask)
  d=np.load(ROOT/f'{outfit}-native.npz');c=np.load(ROOT/f'{outfit}-components.npz')['components'];tri=d['indices'].reshape(-1,3);comp=c[tri[:,0]];mat=d['materials'][tri[:,0]]
  selected=np.isin(comp,[23,11,25])&(mat==0) if outfit=='jk' else np.isin(comp,[12,78,79])&(mat==2)
  uses=np.isin(mat,[0,10,11,12,13,14,15,16,17]) if outfit=='jk' else np.isin(mat,[2,3,4,5,6,7,10,11])
  protected=ownership(d,uses&~selected,len(a))>0
  assert not np.any(changed&protected),'Other atlas surface changed'
  own=ownership(d,selected,len(a));padded=cv2.dilate(own,np.ones((9,9),np.uint8))>0
  assert not np.any(changed&~padded),'Paint escaped selected UV islands and padding'
  rows[outfit]=dict(source_atlas_sha256=sha(ROOT/f'{outfit}-before.png'),source_native_sha256=sha(ROOT/f'{outfit}-native.npz'),source_component_map_sha256=sha(ROOT/f'{outfit}-components.npz'),output_atlas_sha256=sha(ROOT/f'{outfit}-after.png'),changed_texels=int(changed.sum()),unrelated_surface_changed_texels=0,outside_uv_islands_and_padding_changed_texels=0,native_geometry_uv_weights_cloth_physics_unmodified=True)
 write(ROOT/'surface-verification.json',dict(passed=True,outfits=rows,game_runtime_tested=False))
 print('OUTFIT_PATTERN_SURFACES_VERIFIED')
if __name__=='__main__':main()
