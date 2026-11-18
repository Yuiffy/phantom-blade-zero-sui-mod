from common import *
if __name__=='__main__':
    script=CODE/sys.argv[1]
    assert script.is_file()
    print(run(script.stem,[BLENDER,'-b','-t','2','--python-exit-code','1','--python',script])[-1200:])
