"""Append-only native resource staging; automatic v3 selection is omitted."""
import copy
import shutil
from pathlib import Path
import build_combat_voice_experiment as b
from resolve_bilingual_voice_inventory import read, write
ROOT=b.ROOT
WORK=ROOT/'variants/reviewed-natural-voice-v4'
ASSET=Path('ProjectPBZ/Content/Wwise')
LANGS={'Chinese':'VO_CN','English(US)':'VO_EN'}

def stage_patch(label,source,changes):
    """Keep every original byte and offset, append changed resources."""
    original=read(source)
    edited=copy.deepcopy(original)
    if label in ['VO_CN','VO_EN']:
        rel=ASSET/(label+'.uasset')
    else:
        rel=b.ASSET_DIR/(label+'.uasset')
    src=WORK/'original-legacy'/rel if label in ['VO_CN','VO_EN'] else ROOT/'research/extract'/rel
    src_bulk=src.with_suffix('.ubulk')
    dest=WORK/'stage'/rel
    dest.parent.mkdir(exist_ok=True,parents=True)
    shutil.copyfile(src_bulk,dest.with_suffix('.ubulk'))
    resources=edited['DataResources']
    patched=[]
    with dest.with_suffix('.ubulk').open('ab') as out, src_bulk.open('rb') as old:
        for idx,(payload,detail) in sorted(changes.items()):
            row=resources[idx];orig=original['DataResources'][idx]
            assert row['LegacyBulkDataFlags']==0x10501
            old.seek(orig['SerialOffset']);data=old.read(orig['SerialSize'])
            assert b.sha(data)==detail['original_sha256']
            alignment=max(detail.get('alignment',16),16)
            assert alignment&(alignment-1)==0 and alignment<=262144
            padding=(-out.tell())%alignment
            out.write(b'\0'*padding)
            offset=out.tell();out.write(payload)
            row['SerialOffset']=offset
            row['SerialSize']=row['RawSize']=len(payload)
            patched.append({**detail,'resource_index':idx,'original_offset':orig['SerialOffset'],
                'original_bytes':orig['SerialSize'],'offset':offset,'bytes':len(payload),
                'sha256':b.sha(payload),'append_padding':padding})
    assert all(edited[k]==original[k] for k in original if k!='DataResources')
    assert all(row==original['DataResources'][idx] for idx,row in enumerate(resources) if idx not in changes)
    jp=WORK/'edited-json'/(label+'.json')
    write(jp,edited)
    b.run('fromjson-'+label,[b.TOOLS/'UAssetGUI.exe','fromjson',jp,dest,'PBZ'],b.TOOLS)
    assert dest.exists() and dest.with_suffix('.ubulk').exists()
    return {'name':label,'path':rel.as_posix(),'source_json':str(source.relative_to(ROOT)),
        'original_bulk_bytes':src_bulk.stat().st_size,'bulk_bytes':dest.with_suffix('.ubulk').stat().st_size,
        'original_bulk_sha256':b.sha(src_bulk.read_bytes()),'bulk_sha256':b.sha(dest.with_suffix('.ubulk').read_bytes()),
        'native_export_metadata_unchanged':True,'patches':patched,'resource_count':len(resources)}
