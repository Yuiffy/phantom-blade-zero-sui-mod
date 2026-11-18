from common import *
import numpy as np
from scipy.spatial import cKDTree

def main():
 for outfit in ['jk','jirai']:
  if outfit=='jirai':
   src=np.load(REPO/'private/jirai-face-v3/surface.npz');p=src['positions'].copy();c=src['components']
  else:
   src=read(REPO/'models/jk-motion-v4-candidate/source-render-contract.json');p=np.array(src['positions_blender_cm']);c=np.array(src['source_components'])
  p[:,1]*=-1;native=np.load(ROOT/f'{outfit}-native.npz');dist,ids=cKDTree(p).query(native['positions'],workers=1)
  comp=c[ids].copy();comp[dist>.001]=-1
  np.savez_compressed(ROOT/f'{outfit}-components.npz',components=comp,distance=dist)
  print(outfit,'matched',int((comp>=0).sum()),'of',len(comp))
if __name__=='__main__':main()
