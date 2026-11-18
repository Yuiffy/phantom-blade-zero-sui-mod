from common import *
if __name__=='__main__':
 script=CODE/sys.argv[1];assert script.is_file()
 label=script.stem+'-'+os.environ.get('PBZ_PATTERN_OUTFIT','scene')+'-'+os.environ.get('PBZ_PATTERN_AFTER','0')+'-'+os.environ.get('PBZ_PATTERN_DIR','preview')
 print(run(label,[BLENDER,'-b','-t','2','--python-exit-code','1','--python',script])[-1000:])
