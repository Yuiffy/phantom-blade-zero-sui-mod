from common import *
import importlib.util
spec=importlib.util.spec_from_file_location('polish_cook',REPO/'models/fishnet-v1/cook_texture.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
if __name__=='__main__':mod.cook()
