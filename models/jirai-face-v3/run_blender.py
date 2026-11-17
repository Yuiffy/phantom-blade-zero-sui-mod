from common import *
if __name__ == '__main__':
    script = CODE / sys.argv[1]
    assert script.is_file()
    if script.name=='author_candidate.py':
        import numpy as np
        from PIL import Image
        blender('export-source',CODE/'export_source.py')
        d=np.load(ROOT/'source-uv.npz');v=d['positions'];uv=d['uv'];lv=d['loop_vertices']
        im=np.array(Image.open(REPO/'private/fishnet-v1/T_Jirai_Base.png').convert('RGB'))
        q=np.rint(uv*8191).astype(int);vc=np.zeros((len(v),3));vn=np.zeros(len(v))
        np.add.at(vc,lv,im[8191-q[:,1],q[:,0]]);np.add.at(vn,lv,1);vc/=np.maximum(1,vn[:,None])
        np.savez_compressed(ROOT/'source-colors.npz',positions=v,colors=vc)
    print(blender(script.stem, script, *sys.argv[2:])[-1500:])
