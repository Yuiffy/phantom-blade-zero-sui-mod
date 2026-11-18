"""Decode this candidate's dense RawGPU BC1 VT tiles from independent readback.

This intentionally fails on other formats/layouts instead of treating the
observed per-mip dense Morton layout as a general Unreal texture decoder.
"""
from common import *
from PIL import Image
import numpy as np,cv2

def morton(x,y):
 result=0
 for bit in range(7):result|=((x>>bit)&1)<<(2*bit);result|=((y>>bit)&1)<<(2*bit+1)
 return result

def decode(tag):
 before=tag=='before';package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_LashLip1' if before else PACKAGE
 meta=(FACE if before else ROOT)/'independent/final'/(relative_package(package)+'.json');texture,=read(meta);v=texture['VTData']
 bulkpath=(FACE/'installed-legacy' if before else ROOT/'resolved-legacy')/(relative_package(package)+'.ubulk');bulk=bulkpath.read_bytes()
 assert v['NumLayers']==1 and v['LayerTypes']==['PF_DXT1'] and v['TileSize']==128 and v['TileBorderSize']==2
 assert v['TileDataOffsetPerLayer']==[8712] and all(c['CodecType']==['RawGPU'] for c in v['Chunks'])
 dest=ROOT/('cooked-'+tag);dest.mkdir(exist_ok=True);rows=[]
 for mip in range(7):
  row=v['TileOffsetData'][mip];assert row['Addresses']==row['Offsets']==[0] and row['MaxAddress']==row['Width']*row['Height']
  width=max(1,v['Width']>>mip);height=max(1,v['Height']>>mip);out=np.zeros((row['Height']*128,row['Width']*128,3),np.uint8)
  chunk=v['Chunks'][v['ChunkIndexPerMip'][mip]];start=int(chunk['BulkData']['OffsetInFile'],16)+v['BaseOffsetPerMip'][mip]
  for y in range(row['Height']):
   for x in range(row['Width']):
    at=start+morton(x,y)*8712;assert at+8712<=len(bulk)
    tile=np.array(Image.frombytes('RGBA',(132,132),bulk[at:at+8712],'bcn',1))[:,:,:3];out[y*128:y*128+128,x*128:x*128+128]=tile[2:130,2:130]
  out=out[:height,:width];path=dest/f'mip{mip}.png';Image.fromarray(out).save(path);rows.append(dict(mip=mip,width=width,height=height,png_sha256=sha(path)))
 source=np.array(Image.open((FACE if before else ROOT)/'T_Jirai_Base.png').convert('RGB'));top=np.array(Image.open(dest/'mip0.png').convert('RGB'));mae=float(np.abs(top.astype(float)-source).mean());assert mae<4
 write(ROOT/('vt-decoding-'+tag+'.json'),dict(passed=True,source_metadata_sha256=sha(meta),bulk_sha256=sha(bulkpath),mips=rows,top_mip_source_rgb_mae=mae,decoder='Pillow BC1; observed dense Morton tile offsets with 2px border removed',format_specific=True))
 print('VT_INDEPENDENTLY_DECODED',tag,mae,flush=True)

def projection(d):
 p=d['positions'];t=d['indices'].reshape(-1,3);uv=d['uv'][:,0].astype(float);m=d['materials'];center=p[t].mean(1);faces=t[(m[t[:,0]]==0)&(center[:,2]>167)&(center[:,2]<174)&(center[:,1]>0)]
 width,height=1200,600;depth=np.full((height,width),-np.inf);uvmap=np.zeros((height,width,2),np.float32)
 for f in faces:
  q=np.column_stack([(p[f,0]+10)/20*(width-1),(174-p[f,2])/7*(height-1)]);low=np.floor(q.min(0)).astype(int).clip(0,[width-1,height-1]);high=np.ceil(q.max(0)).astype(int).clip(0,[width-1,height-1]);a=np.column_stack([q[0]-q[2],q[1]-q[2]])
  if abs(np.linalg.det(a))<1e-6:continue
  gx,gy=np.meshgrid(np.arange(low[0],high[0]+1),np.arange(low[1],high[1]+1));b=(np.stack([gx,gy],-1)-q[2])@np.linalg.inv(a).T;b=np.dstack([b,1-b.sum(-1)]);ok=(b>=-1e-5).all(-1);x=gx[ok];y=gy[ok];b=b[ok];h=b@p[f,1];take=h>depth[y,x];x=x[take];y=y[take];b=b[take];depth[y,x]=h[take];uvmap[y,x]=b@uv[f]
 return uvmap,np.isfinite(depth)

def verify():
 reports={};canvas=Image.new('RGB',(1200,900),'white')
 xx,zz=np.meshgrid(np.linspace(-10,10,1200),np.linspace(174,167,600));roi=(xx>-4.1)&(xx<-2.)&(zz>168.8)&(zz<170.3)
 for col,tag in enumerate(['before','after']):
  d=np.load(PIN/'final-render.npz' if tag=='before' else ROOT/'final-render.npz');uv,valid=projection(d);images=[];rows=[]
  for mip in range(7):
   im=np.array(Image.open(ROOT/('cooked-'+tag)/f'mip{mip}.png').convert('RGB'));xy=uv*(im.shape[0]-1);out=cv2.remap(im,xy[:,:,0],xy[:,:,1],cv2.INTER_LINEAR);out[~valid]=255;images.append(out)
   Image.fromarray(out).save(ROOT/f'chin-{tag}-mip{mip}.png')
   delta=np.linalg.norm(out.astype(float)-images[0],axis=2)[roi&valid];rows.append(dict(mip=mip,reported_chin_patch_delta_rgb_p95=float(np.percentile(delta,95)),reported_chin_patch_delta_rgb_max=float(delta.max())))
  for row,mip in enumerate([0,4,5]):canvas.paste(Image.fromarray(images[mip]).resize((600,300)),(col*600,row*300))
  reports[tag]=rows
 old={r['mip']:r for r in reports['before']};new={r['mip']:r for r in reports['after']}
 assert old[4]['reported_chin_patch_delta_rgb_p95']>10 and old[5]['reported_chin_patch_delta_rgb_p95']>10,'Failed to reproduce reported block'
 for mip in [4,5]:assert new[mip]['reported_chin_patch_delta_rgb_p95']<5 and new[mip]['reported_chin_patch_delta_rgb_max']<8,(mip,new[mip])
 canvas.save(ROOT/'cooked-chin-before-after.jpg',quality=96)
 write(ROOT/'mip-verification.json',dict(passed=True,reported_block_reproduced_in_old_cooked_mips=[4,5],improved_in_new_cooked_mips=[4,5],reported_patch_world_bounds_cm=dict(x=[-4.1,-2.],z=[168.8,170.3]),metrics=reports,actual_game_shader_not_reproduced=True,game_runtime_tested=False))
 print('COOKED_CHIN_MIP_VERIFIED',flush=True)

if __name__=='__main__':
 if sys.argv[1:]==['verify']:verify()
 else:decode(sys.argv[1])
