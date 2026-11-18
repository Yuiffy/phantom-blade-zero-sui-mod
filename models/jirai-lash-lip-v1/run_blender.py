from common import *
if __name__=='__main__':print(run(sys.argv[1],[BLENDER,'--factory-startup','-b','-t','2','--python-exit-code','1','--python',CODE/sys.argv[1]])[-1200:])
