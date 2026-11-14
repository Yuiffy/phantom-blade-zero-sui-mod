"""Read selected logical ranges from this build's IoStore v8 containers.

Original game files stay read-only. AES is supplied privately by the user;
Oodle is loaded from the user's local tool installation, never bundled.
"""
from collections import OrderedDict
import ctypes
from pathlib import Path
import struct


class FormatError(ValueError):
    pass


def require(ok, message):
    if not ok:raise FormatError(message)


class Toc:
    def __init__(self,path):
        self.path=Path(path)
        self.data=self.path.read_bytes()
        h=self.data[:144]
        require(len(h)==144 and h[:16]==b'-==--==--==--==-','Not an IoStore container')
        require(h[16]==8,'Only verified IoStore TOC version 8 is supported')
        (header,n,blocks,entry,method_count,name_size,self.block_size,
         _,self.partitions)=struct.unpack_from('<9I',h,20)
        self.flags=h[80]
        seeds=struct.unpack_from('<I',h,84)[0]
        self.partition_size=struct.unpack_from('<Q',h,88)[0]
        overflow=struct.unpack_from('<I',h,96)[0]
        require(header==144 and entry==12 and 0<n<1000000,'Unsupported TOC layout')
        require(0<blocks<10000000 and 0<self.block_size<=1048576,'Invalid block table')
        require(0<self.partitions<=1024 and self.partition_size>0,'Invalid partitions')
        offset=header+n*12
        self.blocks_start=offset+n*10+(seeds+overflow)*4
        self.block_count=blocks
        methods=self.blocks_start+blocks*12
        require(method_count<64 and 0<name_size<=256,'Invalid compression names')
        require(methods+method_count*name_size<=len(self.data),'Truncated TOC')
        self.methods=['None']+[self.data[methods+i*name_size:methods+(i+1)*name_size]
                               .rstrip(b'\0').decode('ascii') for i in range(method_count)]
        self.chunks={}
        for i in range(n):
            cid=self.data[header+i*12:header+(i+1)*12].hex()
            p=offset+i*10
            base=int.from_bytes(self.data[p:p+5],'big')
            size=int.from_bytes(self.data[p+5:p+10],'big')
            require(cid not in self.chunks,'Duplicate chunk ID')
            require(size>0 and (base+size-1)//self.block_size<blocks,'Invalid chunk range')
            self.chunks[cid]=(base,size)

    def chunk(self,cid):
        require(cid in self.chunks,'Expected game chunk is missing')
        return self.chunks[cid]

    def block_info(self,index):
        require(0<=index<self.block_count,'Block outside container')
        a,b=struct.unpack_from('<QI',self.data,self.blocks_start+index*12)
        offset,compressed=a&((1<<40)-1),a>>40
        size,method=b&((1<<24)-1),b>>24
        require(0<compressed<=self.block_size*2 and 0<size<=self.block_size,'Invalid block sizes')
        require(method<len(self.methods),'Unknown compression method')
        return offset,compressed,size,method

    def plain_chunk_position(self,cid):
        """Maker-only: require a contiguous, uncompressed target chunk."""
        require(not self.flags&2,'Target MOD must be unencrypted')
        base,size=self.chunk(cid)
        require(base%self.block_size==0,'Target chunk must start on a logical block boundary')
        start=None;expected=None;remaining=size
        for i in range(base//self.block_size,(base+size-1)//self.block_size+1):
            physical,compressed,decoded,method=self.block_info(i)
            require(method==0 and compressed==decoded==min(remaining,self.block_size),
                    'Target chunk is not the verified plain layout')
            if start is None:start=physical
            if expected is not None:require(physical==expected,'Noncontiguous physical chunk')
            expected=physical+compressed;remaining-=compressed
        require(remaining==0,'Incorrect target chunk length')
        return start,size


class RangeReader(Toc):
    def __init__(self,path,key=None,oodle_dll=None):
        super().__init__(path)
        self.aes=None
        if self.flags&2:
            require(isinstance(key,bytes) and len(key)==32,'This encrypted container needs a private 32-byte AES key')
            try:from Crypto.Cipher import AES
            except ImportError:raise FormatError('Install pycryptodome: python -m pip install pycryptodome') from None
            self.aes=AES.new(key,AES.MODE_ECB)
        self.oodle_dll=Path(oodle_dll).resolve() if oodle_dll else None
        self.dll=None;self.handles={};self.cache=OrderedDict()
        self.physical_bytes=0;self.decoded_bytes=0

    def oodle(self,data,size):
        if self.dll is None:
            require(self.oodle_dll is not None and self.oodle_dll.is_file(),
                    'Pass --oodle-dll pointing to your own oo2core_9_win64.dll')
            self.dll=ctypes.CDLL(str(self.oodle_dll))
            fn=self.dll.OodleLZ_Decompress
            ptr,count,integer=ctypes.c_void_p,ctypes.c_ssize_t,ctypes.c_int
            fn.argtypes=[ptr,count,ptr,count,integer,integer,integer,
                         ptr,count,ptr,ptr,ptr,count,integer]
            fn.restype=count
        source=ctypes.create_string_buffer(data);output=ctypes.create_string_buffer(size)
        n=self.dll.OodleLZ_Decompress(source,len(data),output,size,1,1,0,
                                    None,0,None,None,None,0,3)
        require(n==size,'Oodle decompression failed; check the game build and private key')
        return output.raw

    def block(self,index):
        if index in self.cache:
            self.cache.move_to_end(index);return self.cache[index]
        offset,compressed,size,method=self.block_info(index)
        partition,position=divmod(offset,self.partition_size)
        require(partition<self.partitions,'Partition outside container')
        if partition not in self.handles:
            suffix=f'_s{partition}' if partition else ''
            path=self.path.with_name(self.path.stem+suffix+'.ucas')
            self.handles[partition]=path.open('rb')
        count=(compressed+15)//16*16 if self.aes else compressed
        stream=self.handles[partition];stream.seek(position);data=stream.read(count)
        require(len(data)==count,'Truncated source partition')
        self.physical_bytes+=count
        if self.aes:data=self.aes.decrypt(data)
        if method==0:
            require(compressed==size,'Invalid uncompressed block');result=data[:size]
        elif self.methods[method]=='Oodle':result=self.oodle(data[:compressed],size)
        else:raise FormatError('Unsupported compression: '+self.methods[method])
        self.decoded_bytes+=len(result);self.cache[index]=result
        while len(self.cache)>32:self.cache.popitem(last=False)
        return result

    def read(self,cid,offset,size):
        base,length=self.chunk(cid)
        require(0<=offset and 0<size<=8*1048576 and offset+size<=length,'Invalid requested chunk range')
        begin,end=base+offset,base+offset+size;parts=[]
        for index in range(begin//self.block_size,(end-1)//self.block_size+1):
            block=self.block(index)
            first=max(0,begin-index*self.block_size)
            last=min(len(block),end-index*self.block_size)
            require(last>first,'Truncated logical block')
            parts.append(block[first:last])
        result=b''.join(parts);require(len(result)==size,'Incorrect logical range length')
        return result

    def close(self):
        for stream in self.handles.values():stream.close()
        self.cache.clear()

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
