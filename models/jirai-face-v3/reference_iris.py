"""Bake supplied original iris color into an isolated local candidate texture."""
from common import *
import numpy as np,cv2
from PIL import Image
base=np.array(Image.open(ROOT/'T_Face3_Iris.png').convert('RGB')).astype(float)
source=REPO/'private/tripo-bridge-20261115/original-jirai-design.png'
im=np.array(Image.open(source).convert('RGB'))
eye=np.array([[927.,824.],[1135.,770.]])
delta=eye[1]-eye[0];scale=220/np.linalg.norm(delta);theta=-np.arctan2(delta[1],delta[0])
mat=scale*np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
offset=np.array([140,340])-mat@eye[0]
y,x=np.meshgrid(np.linspace(1,-1,1024),np.linspace(-1,1,1024),indexing='ij')
ref=np.stack([141+34*x,340-35*y],axis=-1)
q=(ref-offset)@np.linalg.inv(mat).T
sample=cv2.remap(im,q[:,:,0].astype('f4'),q[:,:,1].astype('f4'),cv2.INTER_CUBIC,borderMode=cv2.BORDER_REPLICATE).astype(float)
r=np.sqrt(x*x+y*y)
red=(sample[:,:,0]>sample[:,:,1]*1.16)&(sample[:,:,0]>sample[:,:,2]*1.05)
glint=(sample.min(2)>207)&(r<.86)&(y>-.6)
weight=np.clip((.98-r)/.10,0,1)*.94*(red|glint)
out=np.rint(base*(1-weight[:,:,None])+sample*weight[:,:,None]).clip(0,255).astype('u1')
Image.fromarray(out).save(ROOT/'T_Face3_Iris_Reference.png')
write(ROOT/'iris-reference-provenance.json',dict(source=str(source),source_sha256=sha(source),
    output_sha256=sha(ROOT/'T_Face3_Iris_Reference.png'),method='Similarity-align supplied illustration; sample iris region, blend only iris chroma/catchlights onto closed-disc fallback.',
    original_reference_pixels_private=True,generative_editing=False,game_runtime_tested=False))
print('REFERENCE_IRIS_BAKED')
if sys.argv[1:]==['--select']:
    import shutil
    shutil.copy2(ROOT/'T_Face3_Iris_Reference.png',ROOT/'T_Face3_Iris.png')
    report=read(ROOT/'iris-reference-provenance.json');report['selected']=True
    report['selected_source_sha256']=sha(ROOT/'T_Face3_Iris.png')
    write(ROOT/'iris-reference-provenance.json',report)
    print('REFERENCE_IRIS_SELECTED')
