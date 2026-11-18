"""Author only the render-to-skin blend, after UE's physical-mask rebuild.

Reads the exact supported native layout, edits both copies of each affected
uint16 blend, preserves export sizes and all other bytes, and records hashes.
Independent final-container decoding and deformation gates remain mandatory.
"""
from pathlib import Path
import json,base64,inspect,struct,hashlib
import numpy as np
import decode_cloth_body as D

def apply_mask(document_path,body_path,report_path=None):
 doc=json.loads(document_path.read_text(encoding='utf-8-sig'))
 budget=json.loads((D.R/'binding-report.json').read_text())['render_material_slots']
 code=inspect.getsource(D.decoder.parse).replace('assert count==14',f'assert count=={budget}')
 scope=dict(vars(D.decoder));scope.update(section=D.section,skeletal_materials=D.materials);exec(code,scope)
 pos,_,_,detail=scope['parse'](doc,{'package':'/HuaShira/Mods/SuiPBZ/EscapeOnly/Hun_Body_Simple'},json.loads((D.W/'material-spec.json').read_text()))
 export=next(x for x in doc['Exports'] if x['ObjectName']=='Hun_Body_Simple')
 assert not next((p['Value'] for p in export['Data'] if p['Name']=='bHasVertexColors'),False)
 raw=base64.b64decode(export['Extras']);out=bytearray(raw)
 reader=D.decoder.Reader(raw,detail['decoded_through_offset']);reader.strip();gpu,gpu_span=reader.bulk(D.DT,500000)
 index_dt=np.dtype([('base_vertex','<u4'),('mapping_offset','<u4'),('lod_bias_stride','<u4')]);index,_=reader.array(index_dt,100)
 assert len(index)==len(detail['sections'])==budget
 names,_=D.materials(doc,raw,None,None);wanted={r['slot']:r['render_pin_plane'] for r in D.CLOTH_SPEC if r.get('render_pin_plane')}
 physical=json.loads((D.W/'cloth-details.json').read_text())['assets']
 allowed=set();records=[]
 for section,entry in zip(detail['sections'],index):
  slot=names[section['material']]
  if slot not in wanted:continue
  plane=wanted[slot];n=section['vertices'];lo=section['base_vertex'];q=pos[lo:lo+n];offset=int(entry['mapping_offset'])
  assert section['cloth_index']>=0 and len(section['cloth_map_spans'])==1 and int(entry['lod_bias_stride'])==n and int(entry['base_vertex'])==lo
  span=section['cloth_map_spans'][0];a=np.frombuffer(raw,dtype=D.DT,count=n,offset=span['offset']).copy()
  assert all(np.array_equal(a[k],gpu[k][offset:offset+n]) for k in D.DT.names if k!='padding')
  old=a['source'][:,3].copy();alpha=1-old/65535
  cage=np.array(physical[section['cloth_index']]['positions']);weights=a['position'][:,:3]
  triangle_z=cage[a['source'][:,:3],2]
  projected_z=np.clip((triangle_z*weights).sum(1),triangle_z.min(1),triangle_z.max(1))
  height=np.maximum(q[:,2],projected_z)
  blend=np.clip((plane['z']-height)/plane['falloff'],0,1)
  # The two extrapolated inner vertices cannot reconstruct the rest surface.
  # Bound their contribution by measured zero-time error, without disabling
  # the physically valid upper skirt points needed for high-knee clearance.
  asset=physical[section['cloth_index']];tri=np.array(asset['indices']).reshape(-1,3)
  fn=np.cross(cage[tri[:,1]]-cage[tri[:,0]],cage[tri[:,2]]-cage[tri[:,0]]);fn/=np.maximum(np.linalg.norm(fn,axis=1)[:,None],1e-12);normals=np.zeros_like(cage)
  for corner in range(3):np.add.at(normals,tri[:,corner],fn)
  normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
  ids=a['source'][:,:3];recon=((cage[ids]+normals[ids]*a['position'][:,3,None,None])*weights[:,:,None]).sum(1)
  errors=np.linalg.norm(recon-q,axis=1);limit=np.minimum(1,plane['rest_error_cap_cm']/np.maximum(errors,1e-12))
  blend=np.minimum(blend,limit)
  # Deep interior cap faces belong under the opaque hip/shorts surface.
  # Large positive normal offsets identify these inward backing faces in
  # this supported cage orientation. Keep them on original skinning.
  inner=np.clip((a['position'][:,3]-5)/3,0,1);inner=inner*inner*(3-2*inner)
  upper=np.clip((q[:,2]-115)/3,0,1);upper=upper*upper*(3-2*upper)
  blend*=1-inner*upper
  # Bound visible cloth motion while retaining the authored shape and shorts.
  blend=np.minimum(blend,plane.get('max_simulated_blend',1.0))

  value=np.rint(65535*(1-alpha*blend)).astype('<u2')
  assert np.all(value>=old),'This authoring step may only blend toward original skinning'
  for i,v in enumerate(value):
   for start in [span['offset']+64*i,gpu_span['offset']+64*(offset+i)]:
    at=start+D.DT.fields['source'][1]+6;struct.pack_into('<H',out,at,int(v));allowed.update([at,at+1])
  records.append(dict(slot=slot,vertices=n,changed_vertices=int(np.count_nonzero(value!=old)),pin_z_cm=plane['z'],falloff_cm=plane['falloff']))
 assert {r['slot'] for r in records}==set(wanted)
 changed={i for i,(a,b) in enumerate(zip(raw,out)) if a!=b};assert changed and changed<=allowed and len(out)==len(raw)
 payload_path=body_path.with_suffix('.uexp');payload=payload_path.read_bytes();assert payload.count(raw)==1,'Native export must have one exact byte match'
 start=payload.find(raw);patched=payload[:start]+out+payload[start+len(raw):]
 assert len(patched)==len(payload) and payload[:start]==patched[:start] and payload[start+len(raw):]==patched[start+len(raw):]
 payload_path.write_bytes(patched)
 sha=lambda b:hashlib.sha256(b).hexdigest()
 report=dict(status='render-pin-authored-final-readback-required',fbx_sha256=sha((D.R/'Sui_Jirai_Hun_Body.fbx').read_bytes()),cloth_spec_sha256=sha((D.R/'cloth-spec.json').read_bytes()),patch_script_sha256=sha(Path(__file__).read_bytes()),mask_coordinate='maximum of render rest Z and bounded source projection Z; blend additionally capped by measured zero-time reconstruction error',header_sha256=sha(body_path.read_bytes()),payload_before_sha256=sha(payload),payload_after_sha256=sha(patched),payload_bytes=len(payload),changed_native_bytes=len(changed),only_uint16_render_blends_changed=True,physical_cloth_and_other_exports_exact=True,interior_positive_offset_fade_cm=[5,8],interior_fade_height_cm=[115,118],sections=records,game_runtime_tested=False)
 (report_path or D.W/'render-pin-authoring.json').write_text(json.dumps(report,indent=2))
 print('COOKED_RENDER_PIN_AUTHORED',records)
