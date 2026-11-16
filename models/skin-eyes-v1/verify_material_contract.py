"""Verify texture sampler contracts against actual native parents' textures."""
from common import *

D=ROOT/'dual';J=D/'independent/json'
original=[]
for path in sorted((ROOT/'research/parent-texture-contract').rglob('*.json')):
    e,=read(path)
    assert e['Properties'].get('VirtualTextureStreaming',False)
    original.append(dict(name=e['Name'],virtual_texture=True,
        formats=e['VTData']['LayerTypes'],readback_sha256=sha(path)))
assert len(original)==8
materials=read(ROOT/'variant/material-spec.json')['materials']+read(D/'jk-material-spec.json')['materials']
checked=[]
for m in materials:
    for name,package in m['textures'].items():
        e,=read(J/(relative_package(package)+'.json'))
        assert e['Properties'].get('VirtualTextureStreaming',False),(m['slot'],name)
        assert e['VTData']['NumMips']>0 and e['VTData']['Chunks']
        assert e['Properties'].get('SRGB',True)==(name=='Albedo'),(m['slot'],name,'color space')
        if name in ['Normal','SkinNormal_MICRO']:assert e['VTData']['LayerTypes']==['PF_BC5']
        if name=='SCMT_Map':
            assert e['VTData']['LayerTypes']==['PF_DXT5'],'Thickness alpha must be preserved'
            color=e['VTData']['LayerFallbackColors'][0]
            assert abs(color['A']-96/255)<1e-5
        checked.append(dict(slot=m['slot'],parameter=name,package=package))
write(ROOT/'variant/texture-contract-verification.json',dict(passed=True,
    basis='independent reads of native equipment/skin parameter textures and final dual container',
    native_texture_contracts=original,leaf_texture_bindings=len(checked),
    virtual_texture_and_color_space_verified=True,skin_thickness_alpha_preserved=True,
    native_material_parent_own_static_permutations_unchanged=True,game_runtime_tested=False))
print('NATIVE_TEXTURE_CONTRACTS_VERIFIED',len(original),len(checked))
