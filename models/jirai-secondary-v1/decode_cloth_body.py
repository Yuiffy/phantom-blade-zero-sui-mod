"""Independent bounded reader for this exact UE 5.7 one-LOD cloth cook."""
from pathlib import Path
import sys,json,inspect,base64,struct,numpy as np,hashlib
from scipy.spatial import cKDTree
from itertools import permutations,product,groupby
CODE=Path(__file__).resolve().parent;R=CODE.parents[1]/'private/jirai-secondary-v1';PBZ=Path('D:/workspace/myrepo/ai-video-workflow/outputs/phantom-blade-zero-sui');W=R/'variant';sys.path.insert(0,str(PBZ/'tools'))
import read_cooked_skin_weights as decoder
from read_cooked_model import import_path
DT=np.dtype([('position','<f4',4),('normal','<f4',4),('tangent','<f4',4),('source','<u2',4),('weight','<f4'),('padding','<u4')]);assert DT.itemsize==64
CLOTH_SPEC=json.loads((R/'cloth-spec.json').read_text());CLOTH_COUNT=len(CLOTH_SPEC)
def section(rd):
 begin=rd.pos;g,strip=rd.strip();material=rd.num('H');base_index,triangles=rd.num('2I');recompute=rd.boolean();channel=rd.num('B');assert channel<=4
 shadow=rd.boolean();raytracing=rd.boolean();base_vertex=rd.num('I');n=rd.num('i');assert 0<=n<=1
 maps=[]
 for _ in range(n):
  m,_=rd.array(DT,500000);assert np.isfinite(m['position']).all() and np.isfinite(m['normal']).all() and np.isfinite(m['tangent']).all() and np.isfinite(m['weight']).all()
  maps.append({k:m[k].tolist() for k in DT.names if k!='padding'})
 bone_map,bone_span=rd.array('<u2',1200);vertices,influences=rd.num('2i');assert 0<vertices<100000 and 1<=influences<=12
 cloth_index=rd.num('h');guid=rd.take(16);cloth_lod=rd.num('i');duplicates=[]
 if not strip&1:
  _,span=rd.array('<u4');duplicates.append(span);_,span=rd.array(np.dtype([('length','<u4'),('index','<u4')]));duplicates.append(span)
 disabled=rd.boolean()
 if cloth_index<0:assert guid==bytes(16) and cloth_lod==-1 and not any(m['position'] for m in maps)
 else:assert 0<=cloth_index<CLOTH_COUNT and cloth_lod==0 and len(maps)==1 and len(maps[0]['position'])==vertices
 return {'offset':begin,'end':rd.pos,'material':material,'base_index':base_index,'triangles':triangles,'base_vertex':base_vertex,'vertices':vertices,'max_influences':influences,'bone_map':bone_map.tolist(),'bone_map_span':bone_span,'duplicate_spans':duplicates,'recompute_tangents':recompute,'cast_shadow':shadow,'raytracing_visible':raytracing,'disabled':disabled,'cloth_index':cloth_index,'cloth_guid_raw':guid.hex(),'cloth_maps':maps}
def materials(doc,raw,target,spec):
 n=struct.unpack_from('<i',raw,58)[0];assert n==json.loads((R/'binding-report.json').read_text())['render_material_slots'];rows=[]
 aliases={s['mask']['sim_slot']:'MI_Jirai_Hair' for s in CLOTH_SPEC}
 for i in range(n):
  ref,idx,num=struct.unpack_from('<3i',raw,62+44*i);name=doc['NameMap'][idx]+('_'+str(num-1) if num else '');interface=aliases.get(name,name)
  expected='/HuaShira/Mods/SuiPBZ/Materials/'+interface+'.'+interface
  assert import_path(doc,ref)==expected,(name,import_path(doc,ref));rows.append(name)
 return rows,62+44*n
def main():
 doc=json.loads((W/'independent/body-uassetapi.json').read_text(encoding='utf-8-sig'));spec=json.loads((W/'material-spec.json').read_text())
 budget=json.loads((R/'binding-report.json').read_text())['render_material_slots']
 code=inspect.getsource(decoder.parse).replace('assert count==14',f'assert count=={budget}');scope=dict(vars(decoder));scope.update(section=section,skeletal_materials=materials);exec(code,scope)
 target={'package':'/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'}
 pos,weights,indices,detail=scope['parse'](doc,target,spec)
 assert detail['reference_bones']==264 and detail['triangles']==json.loads((W/'source-spec.json').read_text())['expected_triangles']
 assert sum(s['triangles'] for s in detail['sections'] if not s['disabled'])==json.loads((R/'binding-report.json').read_text())['visible_triangles']
 assert sum(s['disabled'] for s in detail['sections'])==CLOTH_COUNT
 authored=json.loads((W/'cloth-details.json').read_text());assets=authored['assets']
 raw=base64.b64decode(next(x for x in doc['Exports'] if x['ObjectName']=='Hun_Body_Simple')['Extras'])
 # Continue from the decoded fixed skin-weight lookup into the actual GPU
 # cloth stream, using this installed engine's SerializeStreamedData order.
 export=next(x for x in doc['Exports'] if x['ObjectName']=='Hun_Body_Simple')
 has_colors=next((p['Value'] for p in export['Data'] if p['Name']=='bHasVertexColors'),False)
 assert not has_colors,'This exact source contract has no vertex color stream'
 rd=decoder.Reader(raw,detail['decoded_through_offset']);rd.strip();gpu,gpu_span=rd.bulk(DT,500000)
 map_dt=np.dtype([('base_vertex','<u4'),('mapping_offset','<u4'),('lod_bias_stride','<u4')]);gpu_index,index_span=rd.array(map_dt,100)
 bound=[s for s in detail['sections'] if s['cloth_index']>=0]
 assert len(gpu_index)==len(detail['sections'])==json.loads((R/'binding-report.json').read_text())['render_material_slots'] and len(bound)==CLOTH_COUNT
 for s,idx in zip(detail['sections'],gpu_index):
  if s['cloth_index']<0:
   assert tuple(idx)==(0,0,0)
   continue
  assert int(idx['base_vertex'])==s['base_vertex']
  lo=int(idx['mapping_offset']);hi=lo+s['vertices'];assert 0<=lo<hi<=len(gpu)
  assert int(idx['lod_bias_stride'])==s['vertices']
  for key in ['position','normal','tangent','source','weight']:
   assert np.array_equal(gpu[key][lo:hi],np.array(s['cloth_maps'][0][key],dtype=gpu.dtype.fields[key][0].base)),('GPU cloth mapping mismatch',s['material'],key)
 detail.update(gpu_cloth_mapping_span=gpu_span,gpu_cloth_index_span=index_span,gpu_cloth_records=len(gpu),gpu_cloth_decoded_end=rd.pos)
 names,_=materials(doc,base64.b64decode(next(x for x in doc['Exports'] if x['ObjectName']=='Hun_Body_Simple')['Extras']),target,spec)
 for s in detail['sections']:
  s['slot']=names[s['material']]
  assert s['disabled']==s['slot'].endswith('Sim')
  if s['cloth_index']>=0:
   assert not s['disabled'];a=assets[s['cloth_index']];data=s['cloth_maps'][0]
   assert np.max(np.array(data['source'])[:,:3])<len(a['positions'])
   assert np.max(np.abs(np.array(data['weight'])-1))<1e-6
   assert np.max(np.abs(np.array(data['position'])[:,:3].sum(axis=1)-1))<1e-4
 # Original and cage positions remain on their own input surfaces; use exact
 # UE float quantization as the acceptance criterion for stored skin weights.
 source=json.loads((R/'source-render-contract.json').read_text());points=np.array(source['positions_blender_cm']);points[:,1]*=-1
 candidates=cKDTree(points).query_ball_point(pos,.001,workers=1)
 denominator=detail['weight_denominator']
 def quant(row):
  items=sorted([(k,int(np.float32(np.float32(v)*np.float32(65535))+np.float32(.5))) for k,v in row.items()],key=lambda x:-x[1]);items=[(k,v) for k,v in items if v]
  total=sum(v for k,v in items);carry=0;norm=[]
  for k,v in items:scaled=v*65535+carry;n=scaled//total;carry=scaled-n*total;norm.append((k,n))
  norm.sort(key=lambda x:-x[1])
  if denominator==65535:return {k:v/65535 for k,v in norm if v}
  q={k:v>>8 for k,v in norm if v>>8};q[next(iter(q))]+=255-sum(q.values());return {k:v/255 for k,v in q.items()}
 # UE's weight-only sort leaves equal integer weights with unspecified order.
 # Integer normalization carries its remainder forward, so tied influences
 # can exchange one quantization unit. Enumerate only those exact tie orders.
 quant_cache={}
 def quant_matches(row,actual):
  key=tuple(row.items())
  if key not in quant_cache:
   ordered=sorted(row,key=lambda k:-int(np.float32(np.float32(row[k])*np.float32(65535))+np.float32(.5)))
   groups=[list(g) for _,g in groupby(ordered,key=lambda k:int(np.float32(np.float32(row[k])*np.float32(65535))+np.float32(.5)))]
   assert max(map(len,groups),default=0)<=4,'unexpected large tie group'
   quant_cache[key]=[quant({k:row[k] for g in order for k in g}) for order in product(*[list(permutations(g)) for g in groups])]
  return actual in quant_cache[key]
 maxerr=0
 for i,c in enumerate(candidates):
  assert c,('source position',i)
  assert any(quant_matches(source['influences'][j],weights[i]) for j in c),('source weights',i,weights[i],[source['influences'][j] for j in c])
  maxerr=max(maxerr,min(float(np.linalg.norm(points[j]-pos[i])) for j in c))
 (W/'independent/cloth-native-details.json').write_text(json.dumps(detail))
 np.savez_compressed(W/'independent/render-data.npz',positions=pos,indices=indices)
 (W/'independent/render-weights.json').write_text(json.dumps(weights))
 summary={'status':'native-section-GPU-cloth-mapping-and-skin-readback-passed','visible_triangles':json.loads((R/'binding-report.json').read_text())['visible_triangles'],'all_triangles_including_disabled_cages':detail['triangles'],'disabled_cage_sections':CLOTH_COUNT,'wing_render_sections':sum(s.get('slot') in ['MI_Jirai_WingL','MI_Jirai_WingR'] and s['cloth_index']>=0 for s in detail['sections']),'source_position_max_error_cm':maxerr,'quantized_weights_exact':True,'cooked_gpu_cloth_mapping_decoded':True,'game_runtime_tested':False}
 (W/'cloth-native-verification.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
if __name__=='__main__':main()
