"""Import the authored 8K face atlas as a real sRGB virtual texture."""
from pathlib import Path
R=Path(__file__).resolve().parents[2]
source=R/'models/fishnet-v1/import_texture_ue.py'
text=source.read_text(encoding='utf-8-sig').replace('private/fishnet-v1','private/jirai-face-v2').replace("package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Base'","package='/HuaShira/Mods/SuiPBZ/JiraiVT/T_Jirai_Face2'")
exec(compile(text,str(source),'exec'))
