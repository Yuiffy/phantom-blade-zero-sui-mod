"""Apply the verified installed Fishnet1 atlas to author previews/editable source."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[2];F=R/'private/fishnet-v1'

def apply(m,pack=False):
 import bpy
 path=F/'T_Jirai_Base.png';digest=hashlib.sha256(path.read_bytes()).hexdigest()
 gate=json.loads((F/'verification.json').read_text())
 assert gate['status']=='independent-final-container-verified-runtime-pending'
 assert gate['source_atlas_sha256']==digest and gate['texture_width']==8192
 skin=m.materials['MI_Jirai_Skin'];bs=skin.node_tree.nodes.get('Principled BSDF')
 nodes=[link.from_node for link in bs.inputs['Base Color'].links if link.from_node.type=='TEX_IMAGE'];assert len(nodes)==1
 old=nodes[0].image
 targets=[n for mat in m.materials if mat.use_nodes for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image==old]
 image=bpy.data.images.load(str(path),check_existing=True);assert tuple(image.size)==(8192,8192)
 for n in targets:n.image=image
 if pack:image.pack()
 return dict(source_atlas_sha256=digest,width=8192,height=8192,bindings=len(targets),basis='verified installed Fishnet1 input atlas; final VT payload independently preserved')
