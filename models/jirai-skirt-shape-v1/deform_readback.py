"""Reconstruct this cooked single-influence cloth mapping from actual solver output."""
import json,numpy as np,base64,sys
from pathlib import Path
CODE=Path(__file__).resolve().parent;R=CODE.parents[1]/'private/jirai-skirt-shape-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=R/'variant'
detail=json.loads((W/'independent/cloth-native-details.json').read_text());d=np.load(W/'independent/render-data.npz');rest=d['positions'];indices=d['indices'].reshape(-1,3)
test=sys.argv[1] if len(sys.argv)>1 else 'foreaft'
assert test in ['60hz','30hz','foreaft']
sim=json.loads((W/('simulation-'+test+'.json')).read_text());frames=[]
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
frames=np.array(frames);peak=int(np.argmax(np.linalg.norm(frames-rest,axis=2).max(axis=1)));first_simulated=float(np.linalg.norm(frames[0]-rest,axis=1).max())
# Step 0 already includes a real 1/60 s gravity tick. Separate that intended
# movement from the zero-time mapping error instead of mislabeling motion as
# a binding mismatch (v2 deliberately increases gravity and freedom).
doc_phys=json.loads((W/'independent/json/ProjectPBZ/Plugins/HuaShira/Content/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple.json').read_text())
mesh_phys=next(e for e in doc_phys if e['Type']=='SkeletalMesh')['Properties']['MeshClothingAssets']
rest_errors=[]
for section in detail['sections']:
 if section['cloth_index']<0:continue
 ref=mesh_phys[section['cloth_index']];asset=doc_phys[int(ref['ObjectPath'].rsplit('.',1)[1])]['Properties']['LodData'][0]['PhysicalMeshData']
 q=np.array([[v[k] for k in ['X','Y','Z']] for v in asset['Vertices']]);tri=np.array(asset['Indices']).reshape(-1,3)
 # ClothingMeshUtils::ComputeAveragedNormals sums unit triangle normals,
 # rather than using the imported render normals stored in PhysicalMeshData.
 # Its cross-product order has the opposite sign to the GPU solver output.
 fn=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);fn/=np.maximum(np.linalg.norm(fn,axis=1)[:,None],1e-12);n=np.zeros_like(q)
 for j in range(3):np.add.at(n,tri[:,j],fn)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
 mapping=section['cloth_maps'][0];source=np.array(mapping['source']);bary=np.array(mapping['position']);alpha=1-source[:,3]/65535;b=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)])
 p=((q[source[:,:3]]+n[source[:,:3]]*bary[:,3,None,None])*b[:,:,None]).sum(1);lo=section['base_vertex'];hi=lo+section['vertices']
 rest_errors.append(float(np.linalg.norm((p-rest[lo:hi])*alpha[:,None],axis=1).max()))
first=max(rest_errors)
assert first<.3,('zero-time cloth reconstruction mismatch',first)
assert first_simulated<.5,('excessive movement in the first 1/60 s tick',first_simulated)
doc=json.loads((W/'independent/body-uassetapi.json').read_text(encoding='utf-8-sig'));raw=base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])
uvspan=detail['uv_span'];size=uvspan['bytes']//uvspan['count'];channels=uvspan['count']//len(rest);assert uvspan['count']==len(rest)*channels and 1<=channels<=8 and size in [4,8]
uv=np.frombuffer(raw,dtype='<f2' if size==4 else '<f4',count=uvspan['count']*2,offset=uvspan['offset']).reshape(len(rest),channels,2)[:,0].astype('f4');uv[:,1]=1-uv[:,1]
faces=[];mats=[];motion={}
for s in detail['sections']:
 if s['disabled']:continue
 faces.extend(indices[s['base_index']//3:s['base_index']//3+s['triangles']]);mats.extend([s['material']]*s['triangles'])
 if s['cloth_index']>=0:
  lo=s['base_vertex'];hi=lo+s['vertices'];motion[s['slot']]=float(np.linalg.norm(frames[:,lo:hi]-rest[lo:hi],axis=2).max())
np.savez_compressed(W/'preview-deformation.npz',positions=frames[peak],rest=rest,indices=np.array(faces),materials=np.array(mats),uv=uv)
idle=next(i for i,f in enumerate(sim['frames']) if f['step']==60)
np.savez_compressed(W/'preview-idle.npz',positions=frames[idle],rest=rest,indices=np.array(faces),materials=np.array(mats),uv=uv)
samples=list(range(6,len(frames)))
np.savez_compressed(W/'preview-motion-sequence.npz',frames=frames[samples],steps=np.array([sim['frames'][i]['step'] for i in samples]),dt=sim['dt'],indices=np.array(faces),materials=np.array(mats),uv=uv)
(W/'render-deformation-review.json').write_text(json.dumps({'basis':'actual-offline-Chaos-output-and-cooked-single-influence-mapping','test':test,'initial_reconstruction_max_error_cm':first,'zero_time_rest_mapping_measured_separately':True,'first_simulated_tick_max_displacement_cm':first_simulated,'peak_sample_step':sim['frames'][peak]['step'],'render_surface_max_displacements_cm':motion,'not_a_game_animation':True},indent=2));print(json.dumps(motion,indent=2))
