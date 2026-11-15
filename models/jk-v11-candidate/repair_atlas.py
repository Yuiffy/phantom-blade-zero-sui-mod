"""Reference-led stocking and skirt polish on final v10, in surface space."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='2'
import numpy as np,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
from scipy.spatial import cKDTree
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parent;SRC=ROOT.parent/'tripo-refine-v10/textures/sui-jk-albedo-v10.png'
D=np.load(ROOT/'atlas-provenance.npz');co,faces,uv,comp,mi=[D[k] for k in ['co','faces','uv','comp','mi']]
rgb=np.array(Image.open(SRC).convert('RGB'));original=rgb.copy();H,W=rgb.shape[:2];fc=co[faces].mean(axis=1);c=comp[faces[:,0]];reports=[]
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def surface(mask):
 canvas=Image.new('I',(W,H),0);draw=ImageDraw.Draw(canvas)
 for i in np.flatnonzero(mask&(mi==0)):draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in uv[i]],fill=int(i)+1)
 own=np.asarray(canvas);yy,xx=np.nonzero(own);fi=own[yy,xx]-1;tri=uv[fi];q=np.column_stack(((xx+.5)/W,1-(yy+.5)/H));v0=tri[:,1]-tri[:,0];v1=tri[:,2]-tri[:,0];v2=q-tri[:,0];den=v0[:,0]*v1[:,1]-v0[:,1]*v1[:,0];den=np.where(abs(den)<1e-12,1,den)
 b=(v2[:,0]*v1[:,1]-v2[:,1]*v1[:,0])/den;d=(v0[:,0]*v2[:,1]-v0[:,1]*v2[:,0])/den;p=co[faces[fi,0]]*(1-b-d)[:,None]+co[faces[fi,1]]*b[:,None]+co[faces[fi,2]]*d[:,None]
 return yy,xx,p
def fill_skin(p,col):
 good=(col[:,0]>150)&(col[:,1]>col[:,0]*.70)&(col[:,2]>col[:,0]*.72)&(p[:,2]>90)&(p[:,2]<101)
 assert good.sum()>100
 q=(p-np.mean(p,axis=0))/20;X=np.column_stack((np.ones(len(p)),q[:,0],q[:,1],q[:,2],q[:,0]**2,q[:,1]**2,q[:,0]*q[:,1]));fitgood=good.copy()
 for _ in range(4):
  coef=np.linalg.lstsq(X[fitgood],col[fitgood],rcond=None)[0];res=np.linalg.norm(X@coef-col,axis=1);fitgood=good&(res<max(6,np.quantile(res[fitgood],.82)))
 return np.clip(X@coef,col[good].min(axis=0)-5,col[good].max(axis=0)+5)
def blend(a,b,alpha):return a*(1-alpha[:,None])+b*alpha[:,None]
# Remove all non-navy chromatic stains on pleats, including low-saturation
# pink that the older R>B*.9 detector missed. White hem piping is protected.
yy,xx,p=surface(c==10);col=rgb[yy,xx].astype(float)
white=(col.min(axis=1)>125)&((col.max(axis=1)-col.min(axis=1))<50)
clean=(col[:,2]>col[:,0]*1.38)&(col[:,2]>col[:,1]*1.20)&(col.mean(axis=1)<110)
bad=~white&((col[:,0]>col[:,2]*.72)|(col[:,1]>col[:,2]*.80))
assert clean.sum()>200 and bad.sum()>100
dist,ix=cKDTree(p[clean]).query(p[bad],k=24,workers=1);wt=1/np.maximum(dist,.12)**2;wt/=wt.sum(axis=1,keepdims=True);fill=(col[clean][ix]*wt[:,:,None]).sum(axis=1)
col[bad]=fill;rgb[yy,xx]=np.clip(np.round(col),0,255).astype('uint8')
remaining=(~white)&((col[:,0]>col[:,2]*.72)|(col[:,1]>col[:,2]*.80))
reports.append({'region':'skirt full circumference pink stain removal','repaired_pixels':int(bad.sum()),'white_piping_pixels_unchanged':int(white.sum()),'remaining_non_navy_nonwhite_pixels_by_same_detector':int(remaining.sum())})
for side,label in [(-1,'cat stocking'),(1,'wing stocking')]:
 yy,xx,p=surface((c==1)&(fc[:,0]*side>2)&(fc[:,2]>74)&(fc[:,2]<104));old=rgb[yy,xx].astype(float);z=p[:,2]
 skin=fill_skin(p,old)
 # No baked ornament fragments remain in fabric. The broad circumferential
 # lighting varies smoothly; fine cloth relief is handled by surface normals.
 fabric=np.tile([70.,56.,68.],(len(p),1))*np.clip(1+.014*(p[:,1]-3)[:,None],.88,1.14)
 if side<0:
  center=-12.55-.018*(z-85);u=p[:,0]-center
  front=smooth((5-p[:,1])/3)
  ears=np.maximum(np.maximum(0,1-abs(u-3.10)/1.2),np.maximum(0,1-abs(u+3.10)/1.2))*2.55
  top=85.65+ears*front
 else:
  center=11+.06*(z-84);top=np.full(len(p),85.8)
 stock=smooth((top-z)/.12+.5);col=blend(skin,fabric,stock)
 # Matching reference: two clean pointed ears and a flat, small ink face,
 # rather than the old raised beads and their projected shadows.
 if side<0:
  def ink(alpha):
   nonlocal_dummy=None
   return blend(col,np.tile([21.,17.,24.],(len(p),1)),alpha*front*stock)
  eye=np.zeros(len(p))
  for xeye in [-1.10,1.10]:
   r=np.sqrt(((u-xeye)/.245)**2+((z-84.25)/.28)**2);eye=np.maximum(eye,smooth((1-r)/.22))
  # Symmetric short omega mouth made of two connected curved strokes.
  curve=83.59+.24*(np.abs(u)/.48-1)**2
  mouth=smooth((.095-abs(z-curve))/.055)*smooth((.59-abs(u))/.10)
  nose=smooth((.12-np.sqrt(u*u+(z-83.99)**2))/.05)
  col=ink(np.maximum(np.maximum(eye,mouth),nose))
 else:
  band=smooth((z-78.5)/.12)*smooth((81.4-z)/.12)
  pink=np.tile([201.,48.,110.],(len(p),1))*np.clip(1+.014*(p[:,1]-3)[:,None],.88,1.14)
  col=blend(col,pink,band)
  strap=smooth((.8-abs(p[:,0]-center))/.12)*smooth((1-p[:,1])/.5)*smooth((z-81.25)/.14)
  col=blend(col,np.tile([207.,56.,118.],(len(p),1)),strap)
 # Soft lower join: keep the existing lower belts/buckle and unaffected leg.
 alpha=smooth((z-77.0)/1.0)*smooth((103-z)/1.0)
 if side>0:alpha*=smooth((z-77.8)/.8)
 rgb[yy,xx]=np.clip(np.round(blend(old,col,alpha)),0,255).astype('uint8')
 reports.append({'region':label,'repainted_pixels':int((alpha>0).sum()),'method':'surface-coordinate antialiased stocking edge, clean fabric and skin; face follows reference on stocking surface'})
# Six-pixel gutters into unoccupied atlas space only.
owner=Image.new('1',(W,H),0);draw=ImageDraw.Draw(owner)
for tri in uv[mi==0]:draw.polygon([(float(u*W-.5),float((1-v)*H-.5)) for u,v in tri],fill=1)
changed=np.any(rgb!=original,axis=2);dist,nearest=distance_transform_edt(~changed,return_indices=True);pad=(dist<=6)&~np.array(owner).astype(bool)&~changed;rgb[pad]=rgb[nearest[0][pad],nearest[1][pad]]
yy,xx,_=surface((fc[:,2]>165)|np.isin(c,[4,5]));assert not np.any(rgb[yy,xx]!=original[yy,xx]),'unrelated head or hand atlas changed'
OUT=ROOT/'textures/sui-jk-albedo-v11.png';OUT.parent.mkdir(exist_ok=True);Image.fromarray(rgb).save(OUT)
changed=np.any(rgb!=original,axis=2);Image.fromarray((changed*255).astype('uint8')).save(ROOT/'atlas-repair-mask.png')
report={'input_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(OUT.read_bytes()).hexdigest(),'size':[W,H],'changed_pixels':int(changed.sum()),'unrelated_head_hands_protected':True,'gutter_pixels':int(pad.sum()),'regions':reports}
(ROOT/'atlas-repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
