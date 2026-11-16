"""Reconstruct this cooked single-influence cloth mapping from actual solver output."""
import json,numpy as np,base64
from pathlib import Path
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v1'
detail=json.loads((W/'independent/cloth-native-details.json').read_text());d=np.load(W/'independent/render-data.npz');rest=d['positions'];indices=d['indices'].reshape(-1,3)
sim=json.loads((W/'simulation-60hz.json').read_text());frames=[]
for frame in sim['frames']:
 p=rest.copy()
 for section in detail['sections']:
  if section['cloth_index']<0:continue
  asset=next(a for a in frame['assets'] if a['asset_index']==section['cloth_index'])
  q=np.array(asset['component_positions']);n=np.array(asset['component_normals']);m=section['cloth_maps'][0];source=np.array(m['source']);bary=np.array(m['position']);alpha=1-source[:,3]/65535
  b=np.column_stack([bary[:,:2],1-bary[:,:2].sum(axis=1)])
  # Exact position part of the installed single-influence cloth skinning formula;
  # component/world scale is one in this preview test.
  reconstructed=((q[source[:,:3]]+n[source[:,:3]]*bary[:,3,None,None])*b[:,:,None]).sum(axis=1)
  lo=section['base_vertex'];hi=lo+section['vertices'];p[lo:hi]=rest[lo:hi]*(1-alpha[:,None])+reconstructed*alpha[:,None]
 assert np.isfinite(p).all()
 frames.append(p)
frames=np.array(frames);peak=int(np.argmax(np.linalg.norm(frames-rest,axis=2).max(axis=1)));first=float(np.linalg.norm(frames[0]-rest,axis=1).max())
assert first<.3,('initial cloth reconstruction mismatch',first)
doc=json.loads((W/'independent/body-uassetapi.json').read_text(encoding='utf-8-sig'));raw=base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])
uvspan=detail['uv_span'];size=uvspan['bytes']//uvspan['count'];assert uvspan['count']==len(rest) and size in [4,8]
uv=np.frombuffer(raw,dtype='<f2' if size==4 else '<f4',count=len(rest)*2,offset=uvspan['offset']).reshape(-1,2).astype('f4');uv[:,1]=1-uv[:,1]
faces=[];mats=[];motion={}
for s in detail['sections']:
 if s['disabled']:continue
 faces.extend(indices[s['base_index']//3:s['base_index']//3+s['triangles']]);mats.extend([s['material']]*s['triangles'])
 if s['cloth_index']>=0:
  lo=s['base_vertex'];hi=lo+s['vertices'];motion[s['slot']]=float(np.linalg.norm(frames[:,lo:hi]-rest[lo:hi],axis=2).max())
np.savez_compressed(W/'preview-deformation.npz',positions=frames[peak],rest=rest,indices=np.array(faces),materials=np.array(mats),uv=uv)
samples=list(range(6,len(frames),2))
np.savez_compressed(W/'preview-motion-sequence.npz',frames=frames[samples],steps=np.array([sim['frames'][i]['step'] for i in samples]),dt=sim['dt'],indices=np.array(faces),materials=np.array(mats),uv=uv)
(W/'render-deformation-review.json').write_text(json.dumps({'basis':'actual-offline-Chaos-output-and-cooked-single-influence-mapping','initial_reconstruction_max_error_cm':first,'peak_sample_step':sim['frames'][peak]['step'],'render_surface_max_displacements_cm':motion,'not_a_game_animation':True},indent=2));print(json.dumps(motion,indent=2))
