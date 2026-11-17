from common import *
import importlib.util
loader=importlib.util.spec_from_file_location('face3_cook',REPO/'models/fishnet-v1/cook_texture.py')
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
if __name__=='__main__':
    module.cook()
    report=read(ROOT/'import-report.json')
    sources=['T_Jirai_Base.png','T_Face3_Iris.png','T_Face3_EyeMix.png']
    assert len(report['textures'])==len(sources)
    for row,name in zip(report['textures'],sources):assert row['source_sha256']==sha(ROOT/name)
    gate=read(ROOT/'cook-report.json');gate['texture_sources']={name:sha(ROOT/name) for name in sources}
    write(ROOT/'cook-report.json',gate)
