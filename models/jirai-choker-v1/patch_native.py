"""Patch only selected accessory buffer records and donor skin weights."""
from common import *
from author import parse_doc,unpack
import numpy as np,shutil

def main():
 assert_baseline();d=np.load(ROOT/'patched-render.npz');old=np.load(PIN/'final-render.npz');sel=np.load(ROOT/'author-selections.npz')
 doc=read(PIN/'independent/native.json');p,w,t,detail=parse_doc(doc);raw=unpack(doc)
 assert np.array_equal(p,old['positions']) and np.array_equal(t,old['indices'])
 source=PIN/'legacy'/(relative_package(BODY)+'.uasset');target=ROOT/'legacy'/(relative_package(BODY)+'.uasset');target.parent.mkdir(parents=True,exist_ok=True)
 assert sha(source.with_suffix('.uexp'))==sha(PIN/'resolved-legacy'/(relative_package(BODY)+'.uexp'))
 for ext in ['.uasset','.uexp','.ubulk','.uptnl']:
  if source.with_suffix(ext).exists():shutil.copy2(source.with_suffix(ext),target.with_suffix(ext))
 edited=bytearray(raw);allowed=np.zeros(len(raw),bool);counts={}
 for key,span,stride in [('positions',detail['position_span'],12),('packed_tangents',detail['tangent_span'],8),('indices',detail['index_span'],4)]:
  arr=d[key];prior=old[key];changed=np.any(arr!=prior,axis=1) if arr.ndim==2 else arr!=prior;bs=arr.tobytes();assert len(bs)==span['bytes'];counts[key]=int(changed.sum())
  for i in np.where(changed)[0]:
   start=span['offset']+int(i)*stride;edited[start:start+stride]=bs[int(i)*stride:(int(i)+1)*stride];allowed[start:start+stride]=True
 span=detail['weight_span']
 for dst,src in sel['weight_copies']:
  assert d['materials'][dst]==d['materials'][src] and d['materials'][dst] in [16,17]
  start=span['offset']+int(dst)*8;donor=span['offset']+int(src)*8;edited[start:start+8]=raw[donor:donor+8];allowed[start:start+8]=True
 actual=np.frombuffer(raw,'u1')!=np.frombuffer(edited,'u1');assert actual.any() and np.all(allowed[actual])
 payload=source.with_suffix('.uexp').read_bytes();assert payload.count(raw)==1;start=payload.index(raw)
 target.with_suffix('.uexp').write_bytes(payload[:start]+edited+payload[start+len(raw):]);assert sha(source)==sha(target)
 np.savez_compressed(ROOT/'allowed-bytes.npz',mask=allowed)
 write(ROOT/'native-patch.json',dict(passed=True,changed_native_bytes=int(actual.sum()),changed_records=counts,weight_copied_vertices=len(sel['weight_copies']),original_weights_elsewhere_exact=True,all_uvs_exact=True,skeleton_sections_cloth_physics_exact=True,source_header_sha256=sha(source),output_payload_sha256=sha(target.with_suffix('.uexp'))))
 print('CHOKER_NATIVE_PATCHED',int(actual.sum()))
if __name__=='__main__':main()
