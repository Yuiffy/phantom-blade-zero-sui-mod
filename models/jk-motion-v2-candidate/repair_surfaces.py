"""Rebuild skin/fabric albedo and response from surface coordinates, never screen pixels."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1';os.environ['OMP_NUM_THREADS']='2'
from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
R=Path(__file__).resolve().parent;W=R.parents[2]/'variants/jk-motion-v2'
SRC=R.with_name('tripo-refine-v11')/'textures/sui-jk-albedo-v11.png'
d=np.load(R/'surface.npz');co,faces,uv,comp,mi=[d[k] for k in ['co','faces','uv','comp','mi']]
fc=co[faces].mean(1);c=comp[faces[:,0]]
rgb=np.array(Image.open(SRC).convert('RGB'));old=rgb.copy();H,WIDTH=rgb.shape[:2]
skin_alpha=np.zeros((H,WIDTH),dtype='float32');hand_mask=np.zeros((H,WIDTH),bool)
def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
def blend(a,b,t):return a*(1-t[:,None])+b*t[:,None]
def surface(mask):
 im=Image.new('I',(WIDTH,H));draw=ImageDraw.Draw(im)
 for i in np.flatnonzero(mask):draw.polygon([(float(u*WIDTH-.5),float((1-v)*H-.5)) for u,v in uv[i]],fill=int(i)+1)
 owner=np.array(im);yy,xx=np.nonzero(owner);fi=owner[yy,xx]-1;tri=uv[fi];q=np.column_stack(((xx+.5)/WIDTH,1-(yy+.5)/H))
 a=tri[:,1]-tri[:,0];b=tri[:,2]-tri[:,0];v=q-tri[:,0];den=a[:,0]*b[:,1]-a[:,1]*b[:,0];den=np.where(abs(den)<1e-12,1,den)
 s=(v[:,0]*b[:,1]-v[:,1]*b[:,0])/den;t=(a[:,0]*v[:,1]-a[:,1]*v[:,0])/den
 p=co[faces[fi,0]]*(1-s-t)[:,None]+co[faces[fi,1]]*s[:,None]+co[faces[fi,2]]*t[:,None]
 return yy,xx,p
reports=[]
# One continuous fabric base through the top. The previous v11 repair ended at
# z=77, leaving a dark top band and a separate, overbright patch of upper skin.
for side,label in [(-1,'cat stocking'),(1,'wing stocking')]:
 yy,xx,p=surface((c==1)&(fc[:,0]*side>0)&(fc[:,2]>58));z=p[:,2];col=old[yy,xx].astype(float)
 fabric=np.tile([79.,70.,73.],(len(p),1))
 # Albedo contains only very restrained color variation; lighting/occlusion
 # belongs to the game. This removes the circumferential baked lighting bands.
 fabric*=np.clip(1+.0015*(p[:,1]-5)[:,None],.985,1.015)
 skin=np.tile([242.,208.,204.],(len(p),1))
 if side<0:
  center=-12.55-.018*(z-85);u=p[:,0]-center;front=smooth((5-p[:,1])/3)
  ears=np.maximum(np.maximum(0,1-abs(u-3.1)/1.2),np.maximum(0,1-abs(u+3.1)/1.2))*2.55
  top=85.65+ears*front
 else: center=11+.06*(z-84);top=np.full(len(p),85.8)
 stock=smooth((top-z)/.12+.5);target=blend(skin,fabric,stock)
 if side<0:
  eye=np.zeros(len(p))
  for xeye in [-1.1,1.1]:
   radius=np.sqrt(((u-xeye)/.245)**2+((z-84.25)/.28)**2);eye=np.maximum(eye,smooth((1-radius)/.22))
  curve=83.59+.24*(abs(u)/.48-1)**2
  mouth=smooth((.095-abs(z-curve))/.055)*smooth((.59-abs(u))/.10)
  nose=smooth((.12-np.sqrt(u*u+(z-83.99)**2))/.05)
  target=blend(target,np.tile([21.,17.,24.],(len(p),1)),np.maximum(np.maximum(eye,mouth),nose)*front*stock)
 else:
  # Keep the two intended pink bands and buckle below z=78.4, and redraw the
  # upper band/vertical strap continuously with the existing v11 design.
  band=smooth((z-78.5)/.12)*smooth((81.4-z)/.12)
  target=blend(target,np.tile([201.,48.,110.],(len(p),1)),band)
  strap=smooth((.8-abs(p[:,0]-center))/.12)*smooth((1-p[:,1])/.5)*smooth((z-81.25)/.14)
  target=blend(target,np.tile([207.,56.,118.],(len(p),1)),strap)
 alpha=smooth((z-(60 if side<0 else 78.15))/(6 if side<0 else .25))
 if side>0:
  # Below the upper pink band only desaturate the exposed fabric, preserving
  # original buckle, band edges and printed holes by chroma/brightness guards.
  lower=(z<78.4)&(z>59)&(col[:,0]<125)&(col[:,1]>col[:,0]*.66)&(col[:,2]<col[:,0]*1.14)
  lower_alpha=smooth((z-59)/6)*lower
  col=blend(col,fabric,lower_alpha)
 rgb[yy,xx]=np.clip(np.round(blend(col,target,alpha)),0,255).astype('uint8')
 skin_alpha[yy,xx]=(1-stock).astype('float32')
 reports.append({'region':label,'surface_pixels':len(p),'continuous_fabric_rgb':[79,70,73],'exposed_skin_rgb':[242,208,204],'pink_strap_and_reference_details_preserved':True})
# Remove generated hard baked creases, cuff-colored stains and dark palm
# patches from both complete hand UV islands, including their sides/fingers.
yy,xx,p=surface(np.isin(c,[4,5]));target=np.tile([242.,208.,204.],(len(p),1))
# A small warm variation stays below 2 RGB values, with no shadow painted in.
warm=np.exp(-((p[:,2]-105)/4)**2)*.9;target[:,0]+=warm;target[:,2]-=warm*.35
rgb[yy,xx]=np.clip(np.round(target),0,255).astype('uint8');skin_alpha[yy,xx]=1;hand_mask[yy,xx]=True
reports.append({'region':'both complete hands and palms','pixels':len(p),'roughness':.60,'baked_occlusion_removed':True,'geometry_and_weights_unchanged':True})
# Correct response maps on the same UV islands. Keep the existing materials,
# package names and native parent shader to avoid changing the proven ABI.
spec=json.loads((W/'material-spec.json').read_text());out=R/'textures';out.mkdir(exist_ok=True)
Image.fromarray(rgb).save(out/'sui-jk-albedo-v2.png')
for name in ['T_JK_ARM_Base','T_JK_ARM_Stockings']:
 row=next(t for t in spec['textures'] if t['name']==name);base=np.array(Image.open(row['path']).convert('RGBA'))[0,0]
 arm=np.broadcast_to(base,(H,WIDTH,4)).copy();alpha=hand_mask.astype(float) if name=='T_JK_ARM_Base' else skin_alpha
 arm[:,:,1]=np.round(base[1]*(1-alpha)+153*alpha).astype('uint8')
 Image.fromarray(arm).save(out/(name+'.png'))
# Pad edited pixels only into unoccupied textured UV gutters. Flat-color gold
# and charm slots deliberately use overlapping UVs and must be excluded.
owner=Image.new('1',(WIDTH,H));draw=ImageDraw.Draw(owner)
for tri in uv[np.isin(mi,[0,10,11,12,13,14,15,16,17])]:draw.polygon([(float(u*WIDTH-.5),float((1-v)*H-.5)) for u,v in tri],fill=1)
changed=np.any(rgb!=old,axis=2);dist,nearest=distance_transform_edt(~changed,return_indices=True);pad=(dist<=6)&~np.asarray(owner).astype(bool)&~changed
rgb[pad]=rgb[nearest[0][pad],nearest[1][pad]];Image.fromarray(rgb).save(out/'sui-jk-albedo-v2.png')
# No face, hair, clothing, bag or charm albedo is repainted.
protected=np.isin(c,[2,3,6,7,10,11,12,13,14,15,20,21,22,23,25,32,34,35,36,38,39])&np.isin(mi,[0,10,11,12,13,14,15,16])
yy,xx,_=surface(protected);assert not np.any(rgb[yy,xx]!=old[yy,xx]),'unrelated atlas island changed'
for row in spec['textures']:
 if row['name']=='T_JK_Base':path=out/'sui-jk-albedo-v2.png'
 elif row['name'] in ['T_JK_ARM_Base','T_JK_ARM_Stockings']:path=out/(row['name']+'.png')
 else:path=Path(row['path'])
 row['path']=str(path);row['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
(W/'material-spec.json').write_text(json.dumps(spec,indent=2))
report={'status':'surface-albedo-and-response-repaired','input_sha256':hashlib.sha256(SRC.read_bytes()).hexdigest(),'output_sha256':hashlib.sha256((out/'sui-jk-albedo-v2.png').read_bytes()).hexdigest(),'changed_pixels':int(np.any(rgb!=old,axis=2).sum()),'unrelated_textured_islands_unchanged':True,'regions':reports,'gutter_pixels':int(pad.sum())}
(R/'surface-repair.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
