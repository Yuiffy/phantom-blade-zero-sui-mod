"""Repaint UV-local motifs from reference structure and local original artwork."""
from common import *
from surface import samples,ownership,stroke
import numpy as np,cv2
from PIL import Image

def blend(base,color,alpha):return base*(1-alpha[:,None])+np.asarray(color)*alpha[:,None]
def transform(xz,world,pixels):
 h=cv2.getPerspectiveTransform(np.float32(world),np.float32(pixels));p=np.c_[xz,np.ones(len(xz))]@h.T
 return (p[:,:2]/p[:,2,None]).astype('f4')

def sample_rgb(image,xy):
 return np.concatenate([cv2.remap(image,q[:,0].reshape(-1,1),q[:,1].reshape(-1,1),cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)[:,0,:] for q in np.array_split(xy,max(1,(len(xy)+15999)//16000))])

def main():
 assert_baseline();reports={}
 for outfit in ['jk','jirai']:
  d=np.load(ROOT/f'{outfit}-native.npz');c=np.load(ROOT/f'{outfit}-components.npz')['components'];tri=d['indices'].reshape(-1,3);comp=c[tri[:,0]];mat=d['materials'][tri[:,0]]
  before=np.array(Image.open(ROOT/f'{outfit}-before.png').convert('RGB'));out=before.copy();size=len(out);allowed=np.zeros((size,size),np.uint8);regions=[]
  def paint(name,selected,fn):
   s=samples(d,selected,size);assert s is not None,name
   xx,yy,xyz,normal,face=s;original=before[yy,xx].astype(float);color,take=fn(xyz,normal,original,comp[face])
   assert take.any(),name
   xx=xx[take];yy=yy[take];out[yy,xx]=np.rint(np.clip(color[take],0,255)).astype('u1');allowed[yy,xx]=255
   regions.append(dict(region=name,source_components=sorted(set(comp[selected].tolist())),painted_samples=int(take.sum()),texels=int(len(set((yy.astype('i8')*size+xx).tolist())))))
  if outfit=='jk':
   # Component 23 is the blue armband, isolated from cardigan and hair.
   ids=(c==23)&(d['materials']==0);q=d['positions'][ids];center=np.median(q,axis=0)
   v=np.array([.555,.126,.822]);v/=np.linalg.norm(v)
   n=np.array([-.304,.944,.092]);n-=v*(v@n);n/=np.linalg.norm(n);u=np.cross(n,v);u/=np.linalg.norm(u)
   basis=np.array([u,v,n]);local=(q-center)@basis.T
   write(ROOT/'armband-plane.json',dict(center=center.tolist(),basis=basis.tolist(),bounds=np.percentile(local,[1,99],axis=0).tolist()))
   def emblem(p,norm,col,component):
    local=(p-center)@basis.T
    x=np.arctan2(local[:,0],local[:,2])*6.2;y=local[:,1]
    # The front panel has one continuous embroidery; remove the old ghost ink.
    front=np.ones(len(p),bool)
    shade=np.clip(.93+.025*y-.012*x,.78,1.12)
    color=np.array([49,139,174])[None,:]*shade[:,None]
    xy=np.c_[x/1.3,(y-.55)/1.3]
    outline=[(-2.45,-.55),(-2.65,.35),(-2.5,1.3),(-2.55,2.35),(-1.25,1.75),(-.1,1.8),(1.1,1.8),(2.35,2.5),(2.25,1.25),(2.6,.6),(2.5,-.25),(2.05,-1.2),(1.2,-1.75),(-.1,-1.9),(-1.4,-1.45),(-2.45,-.55)]
    line=stroke(xy,outline,.105,.018)
    # Rounded eyes, a small W mouth, and the shield's pointed lower seam.
    line=np.maximum(line,np.clip((.19-np.linalg.norm(xy-[-1.35,.65],axis=1))/.05,0,1))
    line=np.maximum(line,np.clip((.19-np.linalg.norm(xy-[1.35,.65],axis=1))/.05,0,1))
    line=np.maximum(line,stroke(xy,[(-.8,-.03),(-.42,-.22),(0,.03),(.42,-.22),(.8,-.03)],.11,.018))
    line=np.maximum(line,stroke(xy,[(-2.2,-1.2),(-.75,-2.35),(.3,-2.3),(1.85,-1.75)],.09,.018))
    color=blend(color,[242,238,229],line)
    return color,front
   paint('blue armband cat embroidery',(comp==23)&(mat==0),emblem)
   def checks(p,norm,col,component):
    x,y,z=p.T;take=(norm[:,1]>.18)&(y>1.1)
    shade=np.clip(.91+.025*(z-153)+.015*np.sin(x*1.15),.74,1.12)
    base=np.array([220,73,129])[None,:]*shade[:,None]
    a=(z-153)+.55*x;b=(z-153)-.55*x
    dist=np.minimum(abs((a+1.3)%2.6-1.3),abs((b+1.3)%2.6-1.3))
    line=np.clip((.10-dist)/.065,0,1)*.80
    return blend(base,[248,209,227],line),take
   paint('bow continuous diagonal checks',np.isin(comp,[11,25])&(mat==0),checks)
  else:
   reference=np.array(Image.open(REPO/'private/tripo-bridge-20261115/original-jirai-design.png').convert('RGB'))
   def bow(p,norm,col,component):
    x,y,z=p.T;take=(norm[:,1]>.24)&(y>4.1)
    shade=np.clip(.96+.03*(z-150),.8,1.08)
    result=np.array([233,125,177])[None,:]*shade[:,None];xz=p[:,[0,2]]
    # Piecewise homographies follow each separate fabric panel, preserving
    # the reference's ornament lettering and border rather than inventing text.
    parts=[
     ((component==12)&(x<-.9),[[-8.05,154.5],[-1.65,152.1],[-1.65,149.3],[-8.05,148.4]],[[973,1145],[1059,1194],[1040,1241],[962,1235]]),
     ((component==12)&(x>.9),[[1.65,152.1],[8.05,154.5],[8.05,148.4],[1.65,149.3]],[[1090,1194],[1170,1157],[1174,1252],[1103,1243]]),
     (component==78,[[-1.0,150.7],[-3.0,151.0],[-9.1,146.1],[-7.1,143.9]],[[1035,1241],[1000,1237],[925,1264],[943,1320]]),
     (component==79,[[1.0,150.7],[3.0,151.0],[9.1,146.1],[7.1,143.9]],[[1085,1247],[1101,1247],[1202,1314],[1173,1344]])]
    for selected,world,pixels in parts:
     # The jewel shares white-cloth UV texels. Keep its original pixels.
     selected &= ~((abs(x)<3.0)&(z>148.3)&(z<154.8)&(y>6.2))
     xy=transform(xz[selected],world,pixels)
     sampled=sample_rgb(reference,xy)
     # Exclude white background or skin accidentally included beyond a panel.
     sample_float=sampled.astype(float)
     pink=(sample_float[:,0]-sample_float[:,1]>28)&(sample_float[:,2]-sample_float[:,1]>16);ink=sample_float.mean(1)<110
     base=result[selected];base[pink|ink]=sampled[pink|ink];result[selected]=base
    gem=(component==12)&(abs(x)<3.0)&(z>148.3)&(z<154.8)&(y>6.2)
    take &= ~gem
    return result,take
   paint('bow reference ornaments and lace; shared-UV jewel retained',np.isin(comp,[12,78,79])&(mat==2),bow)
  # Protect every other atlas surface, including those sharing a UV border.
  target=np.isin(comp,[23,11,25])&(mat==0) if outfit=='jk' else np.isin(comp,[12,78,79])&(mat==2)
  # Jirai skin, hair and eyes now use independent atlases; the base albedo
  # still feeds all cloth, shoes and tails. Keep those retained surfaces exact.
  uses=np.isin(mat,[0,10,11,12,13,14,15,16,17]) if outfit=='jk' else np.isin(mat,[2,3,4,5,6,7,10,11])
  protected=ownership(d,uses&~target,size)>0
  conflict=(allowed>0)&protected
  out[conflict]=before[conflict];allowed[conflict]=0
  # Padding fills only unused UV texels, never another protected island.
  used=ownership(d,uses,size)>0
  from scipy.ndimage import distance_transform_edt
  distance,nearest=distance_transform_edt(allowed==0,return_indices=True)
  pad=(distance<=3)&~used
  out[pad]=out[nearest[0][pad],nearest[1][pad]];allowed[pad]=255
  changed=np.any(out!=before,axis=2);assert not np.any(changed&protected)
  assert not np.any(changed&(allowed==0))
  Image.fromarray(out).save(ROOT/f'{outfit}-after.png');Image.fromarray(allowed).save(ROOT/f'{outfit}-edit-mask.png')
  reports[outfit]=dict(source_sha256=sha(ROOT/f'{outfit}-before.png'),output_sha256=sha(ROOT/f'{outfit}-after.png'),size=size,changed_texels=int(changed.sum()),protected_surface_changed_texels=0,protected_border_conflict_texels=int(conflict.sum()),regions=regions)
 write(ROOT/'atlas-report.json',dict(passed=True,outfits=reports,geometry_uv_skinning_physics_unchanged=True,reference_art_remains_private=True,game_runtime_tested=False))
 print('OUTFIT_PATTERNS_AUTHORED',[(k,v['changed_texels']) for k,v in reports.items()])
if __name__=='__main__':main()
