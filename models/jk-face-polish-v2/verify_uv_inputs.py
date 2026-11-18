"""The unchanged authored Normal/Mix maps must remain constant across moved UVs."""
from common import *
import numpy as np
from PIL import Image

def main():
 maps=[('Normal',PBZ/'variants/new-jk-v11/textures/T_JK_FlatNormal.png',[128,128,255,255]),('Mix',REPO/'private/skin-eyes-v1/variant/textures/T_Jirai_ARM_Skin.png',[255,145,0,255])]
 doc,=read(ROOT/'independent/final'/(relative_package(SKIN)+'.json'));params={p['ParameterInfo']['Name']:p['ParameterValue']['ObjectPath'].rsplit('.',1)[0] for p in doc['Properties']['TextureParameterValues']}
 assert params['Normal']=='/HuaShira/Mods/SuiPBZ/JKVT/T_JK_FlatNormal' and params['Mix']=='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_ARM_Skin'
 results=[]
 for parameter,path,value in maps:
  im=np.array(Image.open(path).convert('RGBA'));assert np.all(im==value),(parameter,im.min((0,1)),im.max((0,1)))
  results.append(dict(parameter=parameter,package=params[parameter],source_sha256=sha(path),constant_rgba=value,dimensions=list(im.shape[:2])))
 assert sha(ROOT/'legacy'/(relative_package(SKIN)+'.uexp'))==sha(FACE/'installed-legacy'/(relative_package(SKIN)+'.uexp'))
 write(ROOT/'uv-input-verification.json',dict(passed=True,constant_unchanged_source_maps=results,material_properties_and_native_export_exact=True,cooked_vt_independently_decoded=False))
 print('JK_UV_CONSTANT_INPUTS_VERIFIED')

if __name__=='__main__':main()
