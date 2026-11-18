"""Reconstruct quantized LBS and the final uint16 GPU cloth blend."""
from common import *
from native import decode,unpack
import numpy as np
from scipy.spatial.transform import Rotation as Q

def render_settings(stage):
 settings=read(W/stage/'selection.json') if (W/stage/'selection.json').exists() else read(W/'selection.json')
 if (W/stage/'render-settings.json').exists():settings.update(read(W/stage/'render-settings.json'))
 return settings

def projection(doc,settings):
 rest,_,_,detail=decode(doc);section=detail['sections'][14]
 if settings.get('mapping_path'):
  path=Path(settings['mapping_path']);assert sha(path)==settings['mapping_sha256']
  data=read(path);assert np.array_equal(rest[section['base_vertex']:section['base_vertex']+section['vertices']],data.get('original_positions',data['positions']))
  section['cloth_maps'][0]={k:[row[k] for row in data['mapping']] for k in ['position','normal','tangent','source','weight']}
 return section['cloth_maps'][0]

def target_positions(doc,settings):
 p,_,_,d=decode(doc);s=d['sections'][14]
 if settings.get('mapping_path'):
  data=read(settings['mapping_path']);p[s['base_vertex']:s['base_vertex']+s['vertices']]=data['positions']
 return p
def matrices(bones):
 out=[]
 for b in bones:
  a=np.eye(4);a[:3,:3]=Q.from_quat(b['q']).as_matrix();a[:3,3]=b['t'];out.append(out[b['parent']]@a if b['parent']>=0 else a)
 return np.array(out)
def mask(doc,settings,physical=None):
 p,weights,indices,d=decode(doc);s=d['sections'][14];lo=s['base_vertex'];hi=lo+s['vertices'];m=s['cloth_maps'][0]
 p=target_positions(doc,settings);m=projection(doc,settings);a=np.array(m['source']);b=np.array(m['position']);cage=physical or read(W/'baseline-cloth.json')['assets'][2];q=np.array(settings.get('simulation_positions',cage['positions']));tri=np.array(cage['indices']).reshape(-1,3)
 fn=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);fn/=np.maximum(np.linalg.norm(fn,axis=1)[:,None],1e-12);n=np.zeros_like(q)
 for j in range(3):np.add.at(n,tri[:,j],fn)
 n/=np.maximum(np.linalg.norm(n,axis=1)[:,None],1e-12)
 bary=np.column_stack([b[:,:2],1-b[:,:2].sum(1)]);recon=((q[a[:,:3]]+n[a[:,:3]]*b[:,3,None,None])*bary[:,:,None]).sum(1);error=np.linalg.norm(recon-p[lo:hi],axis=1)
 # Match the physical pin line; smoothly free the upper skirt without pulling its waist.
 z=np.maximum(p[lo:hi,2],np.clip((q[a[:,:3],2]*bary).sum(1),q[a[:,:3],2].min(1),q[a[:,:3],2].max(1)))
 alpha=np.clip((settings.get('render_pin_z',settings['pin_z'])-z)/4,0,1)
 alpha=np.minimum(alpha,.22/np.maximum(error,1e-12))
 alpha=np.minimum(alpha,settings.get('render_blend_cap',1.))
 value=np.rint(65535*(1-alpha)).astype('<u2');actual=1-value/65535
 return value,dict(zero_time_mapping_error_cm=float(np.max(error*actual)),alpha_range=[float(actual.min()),float(actual.max())],changed_vertices=int(np.count_nonzero(value!=a[:,3])))
def evaluate(stage,document=None):
 doc=read(document or W/'baseline-body.json');rest,weights,indices,d=decode(doc)
 settings=render_settings(stage);s=d['sections'][14]
 if stage!='baseline' and document is None:
  rest=target_positions(doc,settings)
  s['cloth_maps'][0]=projection(doc,settings);values,_=mask(doc,settings)
  for i,v in enumerate(values):s['cloth_maps'][0]['source'][i][3]=int(v)
 visible_materials=[0,8,9,12,13,14,15,16,17]
 ids=np.concatenate([np.arange(x['base_vertex'],x['base_vertex']+x['vertices']) for x in d['sections'] if x['material'] in visible_materials])
 reverse=np.full(len(rest),-1);reverse[ids]=np.arange(len(ids));p0=rest[ids];uses={};bones=read(W/'reference-bones.json');names=[b['name'] for b in bones];inv=np.linalg.inv(matrices(bones))
 for j,i in enumerate(ids):
  for n,v in weights[i].items():uses.setdefault(names.index(n),[]).append((j,v))
 uses={n:(np.array([j for j,v in row]),np.array([v for j,v in row])) for n,row in uses.items()}
 faces=[];materials=[]
 for section in d['sections']:
  if section['material'] in visible_materials:
   tr=indices[section['base_index']:section['base_index']+3*section['triangles']].reshape(-1,3);faces.extend(reverse[tr]);materials.extend([section['material']]*len(tr))
 selected=(s['base_vertex']<=ids)&(ids<s['base_vertex']+s['vertices']);hem=selected&(p0[:,2]<97)
 all_assets=read(W/stage/'cloth-details.json')['assets'];asset=all_assets[2];q0=np.array(asset['positions']);tr=np.array(asset['indices']).reshape(-1,3)
 edges=np.unique(np.sort(np.concatenate([tr[:,[0,1]],tr[:,[1,2]],tr[:,[2,0]]]),axis=1),axis=0);lens=np.linalg.norm(q0[edges[:,0]]-q0[edges[:,1]],axis=1)
 records=[]
 for profile in ['walk','jog','crouch']:
  for hz in [30,60]:
   path=W/stage/f'{profile}-{hz}.json'
   if not path.exists():continue
   sim=read(path);frames=[];times=[];ratios=[];fixed_errors=[];distance_excess=[];particle_counts={}
   assert sim['bone_names']==names and all(f['simulated_teleport_mode']==0 for f in sim['frames'])
   for f in sim['frames']:
    for cloth in f['assets']:
     bi=cloth['asset_index'];expected=all_assets[bi]
     assert len(cloth['component_positions'])==len(expected['positions'])
     assert np.isfinite(cloth['component_positions']).all() and np.isfinite(cloth['component_normals']).all()
     particle_counts[bi]=len(cloth['component_positions'])
    b=np.array(f['component_bones']);pose=np.repeat(np.eye(4)[None],len(b),axis=0);pose[:,:3,:3]=Q.from_quat(b[:,3:]).as_matrix();pose[:,:3,3]=b[:,:3];transform=pose@inv;p=np.zeros_like(p0)
    for bi,(ix,wt) in uses.items():p[ix]+=(p0[ix]@transform[bi,:3,:3].T+transform[bi,:3,3])*wt[:,None]
    for sec in d['sections']:
     if sec['cloth_index']<0 or sec['material'] not in [12,14,15]:continue
     cloth=next((a for a in f['assets'] if a['asset_index']==sec['cloth_index']),None)
     if cloth is None:continue
     q=np.array(cloth['component_positions']);n=np.array(cloth['component_normals']);m=sec['cloth_maps'][0];ix=np.array(m['source']);bary=np.array(m['position']);alpha=1-ix[:,3]/65535;ba=np.column_stack([bary[:,:2],1-bary[:,:2].sum(1)]);recon=((q[ix[:,:3]]+n[ix[:,:3]]*bary[:,3,None,None])*ba[:,:,None]).sum(1)
     dst=reverse[np.arange(sec['base_vertex'],sec['base_vertex']+sec['vertices'])];p[dst]=p[dst]*(1-alpha[:,None])+recon*alpha[:,None]
     if sec['material']==14:
      ratios.extend((np.linalg.norm(q[edges[:,0]]-q[edges[:,1]],axis=1)/lens).tolist())
      if settings.get('simulation_reference_bone')=='pelvis':
       pelvis=names.index('pelvis');target=q0@transform[pelvis,:3,:3].T+transform[pelvis,:3,3];distance=np.linalg.norm(q-target,axis=1)
       limits=np.array(next(m['values'] for m in asset['maps'] if m['name']=='MaxDistance'))
       fixed_errors.append(float(distance[limits<1e-6].max(initial=0)));distance_excess.append(float(np.maximum(distance-limits,0).max()))
    assert np.isfinite(p).all();frames.append(p.astype('f4'));times.append((f['step']-60)*sim['dt'])
   frames=np.array(frames);times=np.array(times);neutral=frames[np.argmin(abs(times))];dz=frames[:,hem,2]-neutral[hem,2];drift=np.linalg.norm(frames[:,hem]-neutral[hem],axis=2);up95=np.percentile(dz,95,axis=1);upmax=dz.max(1);drift95=np.percentile(drift,95,axis=1);speed=np.zeros(len(times));speed[1:]=np.percentile(np.linalg.norm(np.diff(frames[:,hem],axis=0),axis=2),95,axis=1)/np.diff(times);cycles=[]
   for stop in [3,8,13]:
    quiet=(times>=stop+2.5)&(times<=stop+3+.001);recovered=(up95<=1.5)&(upmax<=3)&(drift95<=3);settled=None
    for ix in np.where((times>=stop)&(times<=stop+3+.001))[0]:
     tail=(times>=times[ix])&(times<=stop+3+.001)
     if recovered[tail].all():settled=max(0,float(times[ix]-stop));break
    row=dict(stop=stop,quiet_up95_cm=float(up95[quiet].max()),quiet_upmax_cm=float(upmax[quiet].max()),quiet_drift95_cm=float(drift95[quiet].max()),quiet_speed95_cm_s=float(speed[quiet].max()),recovery_seconds=settled)
    row['passed']=row['quiet_up95_cm']<=1.5 and row['quiet_upmax_cm']<=3 and row['quiet_drift95_cm']<=3 and row['quiet_speed95_cm_s']<=1 and settled is not None and settled<=2;cycles.append(row)
   row=dict(profile=profile,hz=hz,edge_ratio_min=min(ratios),edge_ratio_max=max(ratios),peak_up95_cm=float(up95[times>=0].max()),cycles=cycles,first_skirt_tick_cm=float(np.linalg.norm(frames[0,selected]-p0[selected],axis=1).max()),sim_sha256=sha(path))
   row.update(fixed_point_error_cm=max(fixed_errors,default=0),max_distance_excess_cm=max(distance_excess,default=0),simulated_asset_particle_counts=particle_counts)
   row['passed']=all(c['passed'] for c in cycles) and min(ratios)>.7 and max(ratios)<1.25 and row['first_skirt_tick_cm']<.5 and row['fixed_point_error_cm']<=.03 and row['max_distance_excess_cm']<=.15 and (profile!='walk' or row['peak_up95_cm']<=6)
   records.append(row);surface=W/stage/f'{profile}-{hz}-surface.npz';arrays=dict(frames=frames,times=times,rest=p0,ids=ids,faces=np.array(faces),materials=np.array(materials));same=False
   if surface.exists():
    with np.load(surface) as previous:same=set(previous.files)==set(arrays) and all(np.array_equal(previous[k],v) for k,v in arrays.items())
   if not same:np.savez_compressed(surface,**arrays)
   print(stage,profile,hz,'PASS' if row['passed'] else 'FAIL','edges',round(min(ratios),3),round(max(ratios),3),'quiet',round(max(c['quiet_upmax_cm'] for c in cycles),3),flush=True)
 write(W/stage/'evaluation.json',dict(passed=len(records)==6 and all(r['passed'] for r in records),records=records,basis='final quantized LBS and cloth mapping on continuous synthetic motion',game_runtime_tested=False,document_sha256=sha(document or W/'baseline-body.json')))
if __name__=='__main__':evaluate(sys.argv[1],Path(sys.argv[2]) if len(sys.argv)>2 else None)
