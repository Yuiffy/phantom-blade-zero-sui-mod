from common import *
import importlib.util
loader=importlib.util.spec_from_file_location('hairpin_cook',REPO/'models/fishnet-v1/cook_texture.py')
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
if __name__=='__main__':module.cook()
