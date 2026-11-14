"""Build-26367565 bank/encoding helpers; no historical v1/v2 main."""
import math
import os
import struct
import subprocess
from pathlib import Path
import numpy as np
from paths import ROOT, TOOLS
from ue_pipeline import game_pids
from build_snort_experiment import chunks, sha, wave_samples
from parse_wwise_events import describe_payload
WORK=ROOT/'variants/reviewed-natural-voice-v4'
ASSET_DIR=Path('ProjectPBZ/Content/Wwise/Events/VO/Int/Hun/Battle')
ENV=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1',
         RAYON_NUM_THREADS='1', GOMAXPROCS='1')
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'BELOW_NORMAL_PRIORITY_CLASS',0)

def run(label, args, cwd=None):
    assert not game_pids(), 'Defer codec/packaging while PBZ is running'
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=ENV,
                            stdin=subprocess.DEVNULL, capture_output=True, creationflags=FLAGS)
    log = result.stdout+b'\n'+result.stderr
    (WORK/'logs'/(label+'.log')).write_bytes(log)
    assert result.returncode==0 and b'panicked' not in log.lower() and b'failed to convert' not in log.lower(), label
    return log.decode('utf-8',errors='replace')


def traverse(cooked):
    for language in cooked['EventLanguageMap']:
        assert not language['value'].get('SwitchContainerLeaves')
        for kind in ['SoundBanks','Media']:
            for item in language['value'].get(kind,[]):
                yield language['key']['LanguageName'],kind,item


def patch_bank(data, ident, replacements):
    before = describe_payload(data,'SoundBanks',ident)
    out = bytearray(data)
    patches=[]
    p=0
    while p<len(data):
        tag,size=struct.unpack_from('<4sI',data,p)
        if tag==b'HIRC':
            n=struct.unpack_from('<I',data,p+8)[0]
            q=p+12
            for _ in range(n):
                ty,length=struct.unpack_from('<BI',data,q);body=q+5
                if ty==2:
                    plugin=struct.unpack_from('<I',data,body+4)[0]
                    media=struct.unpack_from('<I',data,body+9)[0]
                    if media in replacements:
                        assert plugin==0x00040001 and data[body+8]==0
                        old=struct.unpack_from('<I',data,body+17)[0]
                        size_new=len(replacements[media])
                        struct.pack_into('<I',out,body+17,size_new)
                        patches.append({'media_id':media,'offset':body+17,'old_size':old,'new_size':size_new})
                q=body+length
            assert q==p+8+size
        p+=8+size
    assert p==len(data)
    assert {p['media_id'] for p in patches}==set(replacements)
    allowed={p['offset']+i for p in patches for i in range(4)}
    assert all(i in allowed for i,(a,b) in enumerate(zip(data,out)) if a!=b)
    after=describe_payload(bytes(out),'SoundBanks',ident)
    for a,b in zip(before['sound_sources'],after['sound_sources']):
        assert {k:v for k,v in a.items() if k!='in_memory_size'}=={k:v for k,v in b.items() if k!='in_memory_size'}
        assert b['in_memory_size']==(len(replacements[a['source_id']]) if a['source_id'] in replacements else a['in_memory_size'])
    return bytes(out),patches


def encode(voice):
    source=ROOT/voice['output'];assert sha(source.read_bytes())==voice['quality']['sha256']
    assert voice['kind'] in ['original-recording','original-recording-cut']
    wem=WORK/'encoded'/(voice['id']+'.wem')
    run('encode-'+voice['id'],[ROOT/'research/wav2wem-release/wav2wem.exe','-jobs','1','-q','8','-o',wem,source])
    data=wem.read_bytes();riff=chunks(data)
    fmt=riff[b'fmt ']
    assert len(fmt)==66 and struct.unpack_from('<HHI',fmt)==(0xffff,1,48000)
    decoded=wem.with_suffix('.decoded.wav')
    run('decode-'+voice['id'],[ROOT/'research/vgmstream/vgmstream-cli.exe','-i','-o',decoded,wem])
    a,b=wave_samples(source),wave_samples(decoded)
    assert len(a)==len(b)==struct.unpack_from('<I',fmt,24)[0]
    snr=10*math.log10(float(np.sum(a*a))/float(np.sum((a-b)**2)))
    corr=float(np.sum(a*b)/math.sqrt(float(np.sum(a*a)*np.sum(b*b))))
    assert snr>18 and corr>.98,(voice['id'],snr,corr)
    return data,{'candidate':voice['id'],'source':voice['output'],'source_sha256':sha(source.read_bytes()),
                 'wem_sha256':sha(data),'duration_seconds':len(a)/48000,'samples':len(a),
                 'decode_snr_db':snr,'decode_correlation':corr,'review':voice['review']}
