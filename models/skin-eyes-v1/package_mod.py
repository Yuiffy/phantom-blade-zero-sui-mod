from common import PBZ
import build_native_shader_assets as native
from material_recipe import build
native.materials = build
from reuse_r6 import execute
execute('package_mod', globals())
