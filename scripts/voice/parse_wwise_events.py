"""Decode current adult event metadata using local usmap unversioned schemas.

Read-only; emits an explicit error instead of guessing unknown layouts.
"""
import base64
import hashlib
import json
import math
import struct
from pathlib import Path

from paths import ROOT
SCHEMA=None


class Reader:
    def __init__(self,data,names):self.data=data;self.pos=0;self.names=names
    def num(self,fmt):
        n=struct.calcsize('<'+fmt)
        assert self.pos+n<=len(self.data),(self.pos,fmt,len(self.data))
        v=struct.unpack_from('<'+fmt,self.data,self.pos)[0];self.pos+=n;return v
    def default(self,field):
        t=field['type']
        if t in ['Array','Set','Map']:return []
        if t=='Struct':return {}
        if t in ['Name','Str']:return None
        if t=='Bool':return False
        return 0
    def prop(self,f):
        t=f['type']
        if t=='Struct':return self.object(f['struct'])
        if t=='Enum':return self.prop(f['inner'])
        if t in ['Int','UInt32','UInt16','Int16','Int64','UInt64','Int8','Byte','Float','Double','Bool']:
            return self.num({'Int':'i','UInt32':'I','UInt16':'H','Int16':'h','Int64':'q','UInt64':'Q','Int8':'b',
                             'Byte':'B','Float':'f','Double':'d','Bool':'B'}[t])
        if t=='Name':
            i,number=self.num('i'),self.num('i')
            assert 0<=i<len(self.names) and 0<=number<1000,(i,number)
            n=self.names[i]
            return n if number==0 else n+'_'+str(number-1)
        if t in ['Array','Set']:
            if t=='Set':
                removed=self.num('i');assert removed==0,'Nonempty set removal list'
            n=self.num('i');assert 0<=n<100000
            return [self.prop(f['inner']) for _ in range(n)]
        if t=='Map':
            removed=self.num('i');assert removed==0,'Nonempty map removal list'
            n=self.num('i');assert 0<=n<100000
            return [{'key':self.prop(f['key']),'value':self.prop(f['value'])} for _ in range(n)]
        raise ValueError('Unsupported field '+str(f))
    def object(self,name):
        global SCHEMA
        if SCHEMA is None:
            SCHEMA=json.loads((ROOT/'research/wwise-schema.json').read_text(encoding='utf-8'))
        schema=SCHEMA['schemas'][name]
        assert not schema['parent'],'Inherited schema not implemented'
        fields={f['index']:f for f in schema['fields']}
        fragments=[];bits=0
        while True:
            h=self.num('H');skip=h&127;zero=bool(h&128);last=bool(h&256);n=h>>9
            assert n<=127
            fragments.append((skip,zero,n))
            if zero:bits+=n
            if last:break
        size=0 if bits==0 else 1 if bits<=8 else 2 if bits<=16 else ((bits+31)//32)*4
        mask=int.from_bytes(self.data[self.pos:self.pos+size],'little');self.pos+=size
        index=0;bit=0;result={}
        for skip,zero,n in fragments:
            index+=skip
            for _ in range(n):
                assert index in fields,(name,index,list(fields),self.pos)
                f=fields[index];assert f['array_size']==1
                iszero=zero and bool((mask>>bit)&1)
                if zero:bit+=1
                result[f['name']]=self.default(f) if iszero else self.prop(f)
                index+=1
        return result


def fnv(name):
    value=2166136261
    for byte in name.lower().encode('utf-8'):
        value=((value*16777619)^byte)&0xffffffff
    return value


def describe_payload(data,kind,ident):
    if kind=='SoundBanks':
        assert data[:4]==b'BKHD' and struct.unpack_from('<I',data,12)[0]==ident
        assert struct.unpack_from('<I',data,8)[0]==154,'Revalidate the bank layout for a different version'
        position=0;chunks=[];sources=[]
        while position+8<=len(data):
            tag=data[position:position+4];size=struct.unpack_from('<I',data,position+4)[0]
            assert position+8+size<=len(data)
            chunks.append(tag.decode('ascii'))
            if tag==b'HIRC':
                p=position+8;count=struct.unpack_from('<I',data,p)[0];p+=4
                for _ in range(count):
                    ty=data[p];n=struct.unpack_from('<I',data,p+1)[0];body=data[p+5:p+5+n];p+=5+n
                    if ty==2:
                        # wwiser CAkBankMgr__LoadSource layout for bank version 154.
                        assert len(body)>=22
                        sources.append({'object_id':struct.unpack_from('<I',body)[0],
                            'plugin_id':struct.unpack_from('<I',body,4)[0],'stream_type':body[8],
                            'source_id':struct.unpack_from('<I',body,9)[0],
                            'cache_id':struct.unpack_from('<I',body,13)[0],
                            'in_memory_size':struct.unpack_from('<I',body,17)[0]})
                assert p==position+8+size
            position+=8+size
        assert position==len(data)
        return {'format':'Wwise-SoundBank','bank_version':struct.unpack_from('<I',data,8)[0],
                'chunks':chunks,'sound_sources':sources}
    assert data[:4]==b'RIFF' and data[8:12]==b'WAVE'
    assert struct.unpack_from('<I',data,4)[0]+8==len(data)
    position=12;fmt=None;chunks=[]
    while position+8<=len(data):
        tag=data[position:position+4];n=struct.unpack_from('<I',data,position+4)[0]
        assert position+8+n<=len(data)
        chunks.append(tag.decode('ascii'))
        if tag==b'fmt ':fmt=data[position+8:position+8+n]
        # Wwise RIFF chunks here are not word-padded.
        position+=8+n
    assert position==len(data) and fmt is not None
    code,channels,rate,avg,align,bits=struct.unpack_from('<HHIIHH',fmt)
    assert code==0xffff and len(fmt)==66
    samples=struct.unpack_from('<I',fmt,24)[0]
    return {'format':'Wwise-Vorbis','codec_tag':code,'sample_rate':rate,'channels':channels,
            'decoded_samples':samples,'duration_seconds':samples/rate,'chunks':chunks}
