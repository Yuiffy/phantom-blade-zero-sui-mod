"""Confirm UV-only scope and exact preservation of accepted facial geometry."""
from common import *
import numpy as np,cv2
from PIL import Image

def verify(final=True):
 path=ROOT/('final-render.npz' if final else 'patched-render.npz');d=np.load(path);old=np.load(PIN/'final-render.npz');sel=np.load(ROOT/'author-selections.npz');r=read(ROOT/'author-report.json')
 assert r['native_sha256']==sha(ROOT/'patched-render.npz') and r['atlas_sha256']==sha(ROOT/'T_Jirai_Base.png')
 for key in old.files:
  if key!='uv':assert np.array_equal(d[key],old[key]),key
 ids=sel['uv_vertices'];keep=np.ones(len(d['positions']),bool);keep[ids]=False
 assert np.array_equal(d['uv'][keep],old['uv'][keep]) and np.array_equal(d['uv'][:,1],old['uv'][:,1]) and np.all(d['materials'][ids]==0)
 # Existing iris, sclera, hair, and the approved lash UV charts stay exact.
 for material in [1,8,18,19]:assert np.array_equal(d['uv'][d['materials']==material],old['uv'][old['materials']==material])
 p=d['positions'];assert np.all(p[ids,2]<176.6) and np.all(p[ids,2]>167.7)
 atlas=np.array(Image.open(ROOT/'T_Jirai_Base.png').convert('RGB'));src=np.array(Image.open(FACE/'T_Jirai_Base.png').convert('RGB'));scope=np.array(Image.open(ROOT/'atlas-scope.png'));changed=np.any(atlas!=src,2);assert not np.any(changed&(scope==0))
 occ=np.zeros((8192,8192),np.uint8);t=d['indices'].reshape(-1,3)
 for f in t[d['materials'][t[:,0]]==0]:cv2.fillConvexPoly(occ,np.rint(old['uv'][f,0].astype(float)*8191).astype('i4'),255)
 assert not np.any(changed&(occ>0))
 constants={}
 for name in ['T_Jirai_FlatNormal','T_Jirai_ARM_Skin','T_SkinEyes_SCMT']:
  a=np.array(Image.open(REPO/'private/skin-eyes-v1/variant/textures'/(name+'.png')));assert np.all(a==a[0,0]);constants[name]=a[0,0].tolist()
 for row in r['islands']:
  assert row['gutter_pixels']==48
 write(ROOT/('geometry-verification.json' if final else 'geometry-preflight.json'),dict(passed=True,final_container_readback=final,native_render_sha256=sha(path),source_atlas_sha256=sha(ROOT/'T_Jirai_Base.png'),relocated_islands=16,uv_vertices=len(ids),all_positions_frames_indices_weights_uv1_exact=True,eye_socket_lashes_iris_sclera_shape_exact=True,upper_lash_uv_charts_exact=True,old_occupied_skin_texels_exact=True,minimum_chart_gutter_pixels=48,uniform_other_skin_inputs=constants,game_runtime_tested=False))
 print('CHIN_GEOMETRY_VERIFIED',final,flush=True)

if __name__=='__main__':verify(sys.argv[1:]!=['preflight'])
