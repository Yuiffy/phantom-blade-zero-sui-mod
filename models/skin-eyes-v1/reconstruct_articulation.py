from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from reuse_r6 import execute
execute('reconstruct_articulation', globals())
