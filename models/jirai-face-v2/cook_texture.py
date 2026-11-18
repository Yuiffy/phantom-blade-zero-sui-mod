"""Reuse the verified VT import/cook recipe in a fresh isolated project."""
from common import *
import importlib.util
loader=importlib.util.spec_from_file_location('face_cook',REPO/'models/fishnet-v1/cook_texture.py')
module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
module.cook()
