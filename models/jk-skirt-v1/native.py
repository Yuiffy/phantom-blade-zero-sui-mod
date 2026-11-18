"""Bounded JK5 native decoder, including both stored copies of GPU mapping."""
from common import *
import base64,struct,inspect,importlib.util,numpy as np
import read_cooked_skin_weights as decoder
source=P/'models/new-outfit-20261114/tripo-motion-v5/decode_cloth_body.py'
spec=importlib.util.spec_from_file_location('jk_original_decoder',source);old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
DT=old.DT
def section(rd):
 begin=rd.pos;g,strip=rd.strip();material=rd.num('H');base_index,triangles=rd.num('2I');recompute=rd.boolean();channel=rd.num('B');assert channel<=4
 shadow=rd.boolean();raytracing=rd.boolean();base_vertex=rd.num('I');n=rd.num('i');assert 0<=n<=1
 maps=[];spans=[]
 for _ in range(n):
  m,span=rd.array(DT,500000);spans.append(span);assert np.isfinite(m['position']).all() and np.isfinite(m['normal']).all() and np.isfinite(m['tangent']).all() and np.isfinite(m['weight']).all()
  maps.append({k:m[k].tolist() for k in DT.names if k!='padding'})
 bone_map,bone_span=rd.array('<u2',1200);vertices,influences=rd.num('2i');assert 0<vertices<100000 and 1<=influences<=12
 cloth_index=rd.num('h');guid=rd.take(16);cloth_lod=rd.num('i');duplicates=[]
 if not strip&1:
  _,span=rd.array('<u4');duplicates.append(span);_,span=rd.array(np.dtype([('length','<u4'),('index','<u4')]));duplicates.append(span)
 disabled=rd.boolean()
 if cloth_index<0:assert guid==bytes(16) and cloth_lod==-1 and not any(m['position'] for m in maps)
 else:assert 0<=cloth_index<5 and cloth_lod==0 and len(maps)==1 and len(maps[0]['position'])==vertices
 return {'offset':begin,'end':rd.pos,'material':material,'base_index':base_index,'triangles':triangles,'base_vertex':base_vertex,'vertices':vertices,'max_influences':influences,'bone_map':bone_map.tolist(),'bone_map_span':bone_span,'duplicate_spans':duplicates,'recompute_tangents':recompute,'cast_shadow':shadow,'raytracing_visible':raytracing,'disabled':disabled,'cloth_index':cloth_index,'cloth_guid_raw':guid.hex(),'cloth_maps':maps,'cloth_map_spans':spans}

def unpack(doc):return base64.b64decode(next(e for e in doc['Exports'] if e['ObjectName']=='Hun_Body_Simple')['Extras'])
def decode(doc):
 code=inspect.getsource(decoder.parse).replace('assert count==14','assert count==24');scope=dict(vars(decoder));scope.update(section=section,skeletal_materials=old.materials);exec(code,scope)
 p,w,i,d=scope['parse'](doc,{'package':BODY},read(P/'variants/jk-motion-v5/material-spec.json'))
 raw=unpack(doc);rd=decoder.Reader(raw,d['decoded_through_offset']);rd.strip();gpu,span=rd.bulk(DT,500000);ix,ispan=rd.array(np.dtype([('base_vertex','<u4'),('mapping_offset','<u4'),('lod_bias_stride','<u4')]),100)
 assert len(ix)==24
 for s,x in zip(d['sections'],ix):
  if s['cloth_index']<0:assert tuple(x)==(0,0,0);continue
  assert x['base_vertex']==s['base_vertex'] and x['lod_bias_stride']==s['vertices'];lo=int(x['mapping_offset']);s['gpu_mapping_offset']=lo
  for key in ['position','normal','tangent','source','weight']:
   assert np.array_equal(gpu[key][lo:lo+s['vertices']],np.array(s['cloth_maps'][0][key],dtype=gpu.dtype.fields[key][0].base))
 d.update(gpu_cloth_mapping_span=span,gpu_cloth_index_span=ispan)
 return p,w,i,d
