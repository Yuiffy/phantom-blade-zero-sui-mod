"""Independent original native layout/hash readers."""
import base64
import hashlib
from parse_wwise_events import Reader

def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
    return h.hexdigest()


def export(j,name):
    return next(e for e in j['Exports'] if e['ObjectName'].lower()==name.lower())


def library_layout(j,name):
    ex=export(j,name);raw=base64.b64decode(ex['Extras'])
    r=Reader(raw,j['NameMap'])
    assert r.object('WwiseAssetLibraryCookedData')=={}
    native=raw[r.pos:r.pos+16];r.pos+=16;n=r.num('i')
    files=[r.object('WwisePackagedFile') for _ in range(n)]
    used=[]
    for f in files:
        f['resource_indices']=[]
        for _ in range(2 if f['PrefetchSize'] else 1):
            padding=r.num('i')
            if padding:
                idx=r.num('i');used.append(idx)
                assert j['DataResources'][idx]['SerialSize']==padding
            idx=r.num('i');used.append(idx);f['resource_indices'].append(idx)
    assert r.pos==len(raw) and used==list(range(len(j['DataResources'])))
    return {'native':native.hex(),'files':files,'indices':used}
