"""Reuse the frozen R6 pipeline in an isolated candidate, without editing R6."""
from pathlib import Path
import hashlib, json

CODE = Path(__file__).resolve().parent

def execute(name, namespace):
    source = CODE.parent / 'jirai-detail-v1' / (name + '.py')
    expected=json.loads((CODE/'pipeline-source-hashes.json').read_text(encoding='utf8'))
    assert hashlib.sha256(source.read_bytes()).hexdigest()==expected[name], ('R6 pipeline source changed',name)
    text = source.read_text(encoding='utf-8-sig')
    assert 'private/jirai-detail-v1' in text, name
    text = text.replace('private/jirai-detail-v1','private/skin-eyes-v1')
    text = text.replace("ROOT.name=='jirai-detail-v1'", "ROOT.name=='skin-eyes-v1'")
    if name == 'verify_mod':
        text = text.replace("e['CachedData']['ParentLayerIndexRemap']==[0,1]", "e['CachedData']['ParentLayerIndexRemap']==m.get('layer_remap',[0,1])")
    if name == 'import_mod_ue':
        text = text.replace("row['kind']!='normal'", "row['kind']!='normal' and row['name']!='T_SkinEyes_SCMT'")
    if name == 'author_cloth_ue':
        text += "\nscmt=unreal.load_asset('/HuaShira/Mods/SuiPBZ/JiraiVT/T_SkinEyes_SCMT')\nscmt.set_editor_property('compression_no_alpha',False)\nassert E.save_loaded_asset(scmt)\n"
    namespace['__file__'] = str(CODE / (name + '.py'))
    exec(compile(text, namespace['__file__'], 'exec'), namespace)
