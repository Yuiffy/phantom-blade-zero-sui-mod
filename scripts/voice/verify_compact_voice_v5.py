"""Independently audit the final v5 container readback against original/v4 data.

Does not use the builder's expected native metadata or bank patch function.
"""
import base64
import copy
import json
from collections import Counter

import psutil
import build_combat_voice_experiment as b
from build_compact_voice_v5 import WORK, V4, NAME, sha_file
from parse_wwise_events import Reader, describe_payload
from resolve_bilingual_voice_inventory import read, write


def main():
    if not __debug__:
        raise RuntimeError('Do not disable format assertions with python -O')
    assert not b.game_pids()
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    b.WORK = WORK
    report = read(WORK/'report.json')
    v4 = read(V4/'report.json')
    assert report['v4_report_sha256'] == sha_file(V4/'report.json')
    choices = {(r['language'], r['media_id']):r for r in v4['replacements']}
    metadata = {e['event']:e for e in read(b.ROOT/'research/adult-wwise-metadata.json')}
    inventory = read(V4/'bilingual-inventory.json')
    bank_sources = {}
    for asset in v4['assets']:
        for patch in asset['patches']:
            if patch['kind'] == 'SoundBanks':
                bank_sources[(patch['language'], patch['id'])] = (asset['path'], patch)
    names = set(v4['target_events']) | {'SFX_Combat_VO_Hun_ZhongZhuan_01'}
    assets = sorted((WORK/'readback'/b.ASSET_DIR).glob('*.uasset'))
    assert {p.stem for p in assets} == names
    assert {p.relative_to(WORK/'readback').as_posix() for p in (WORK/'readback').rglob('*.uasset')} == {
        (b.ASSET_DIR/(name+'.uasset')).as_posix() for name in names}
    original_hashes = {item['PackagedFile']['Hash'] for e in metadata.values()
                       for _, _, item in b.traverse(e['metadata'])}
    for lib in ['VO_CN', 'VO_EN']:
        original_hashes.update(f['Hash'] for f in read(b.ROOT/'research/wwise-libraries'/lib/'parsed-index.json')['packaged_files'])
    identities, hash_owners, assignments, wem_hashes = {}, {}, {}, set()
    media_instances = 0
    for path in assets:
        name = path.stem
        jp = WORK/'readback-json'/(name+'.json')
        b.run('readback-'+name, [b.TOOLS/'UAssetGUI.exe','tojson',path,jp,'VER_UE5_6','PBZ'], b.TOOLS)
        actual = read(jp)
        original = read(b.ROOT/'research/adult-audio-json'/(name+'.json'))
        assert actual['NameMap'] == original['NameMap'] and actual['Imports'] == original['Imports']
        old_export = next(e for e in original['Exports'] if e['ObjectName'].lower() == name.lower())
        export = next(e for e in actual['Exports'] if e['ObjectName'].lower() == name.lower())
        assert export['Data'] == old_export['Data']
        assert {k:v for k,v in export.items() if k not in ['Extras','SerialSize','SerialOffset']} == {
            k:v for k,v in old_export.items() if k not in ['Extras','SerialSize','SerialOffset']}
        native = base64.b64decode(export['Extras'])
        reader = Reader(native, actual['NameMap'])
        cooked = reader.object('WwiseLocalizedEventCookedData')
        expected = copy.deepcopy(metadata[name]['metadata'])
        bulk = path.with_suffix('.ubulk').read_bytes()
        used, end = set(), 0
        pools = {}
        refs = { (r['language'],r['kind'],r['id']):r for e in inventory['events'] if e['event'] == name for r in e['references'] }
        for (language,kind,item), (_,_,old_item) in zip(b.traverse(cooked),b.traverse(expected), strict=True):
            ident = item['MediaId' if kind == 'Media' else 'SoundBankId'] & 0xffffffff
            key = (language,kind,ident)
            pf = item['PackagedFile']
            assert pf['PackagingStrategy'] == 3 and not pf['bStreaming'] and not pf['PrefetchSize']
            value = pf['Hash']
            assert value and value not in original_hashes
            assert value not in hash_owners or hash_owners[value] == key
            hash_owners[value] = key
            old_item['PackagedFile'].update(PackagingStrategy=3, Hash=value)
            index = reader.num('i')
            assert index not in used
            used.add(index)
            resource = actual['DataResources'][index]
            assert resource['LegacyBulkDataFlags'] == 0x10501
            offset, size = resource['SerialOffset'], resource['SerialSize']
            assert size == resource['RawSize'] and offset % max(16,pf['MemoryAlignment']) == 0
            assert offset >= end and bulk[end:offset] == b'\0'*(offset-end)
            data = bulk[offset:offset+size]
            assert len(data) == size
            end = offset+size
            digest = b.sha(data)
            identity = (value,digest)
            assert key not in identities or identities[key] == identity
            identities[key] = identity
            if kind == 'Media':
                row = choices[(language,ident)]
                source = V4/'encoded'/(row['candidate']+'.wem')
                assert data == source.read_bytes() and digest == row['replacement_sha256']
                wem_hashes.add(digest)
                assignments[(language,ident)] = digest
                pools.setdefault(language,{})[ident] = len(data)
                media_instances += 1
            else:
                if (language,ident) in bank_sources:
                    rel, patch = bank_sources[(language,ident)]
                    with (V4/'readback'/rel).with_suffix('.ubulk').open('rb') as f:
                        f.seek(patch['offset'])
                        previous = f.read(patch['bytes'])
                    assert b.sha(previous) == patch['sha256']
                    assert data == previous, 'Bank must be byte-identical to independently verified v4'
                else:
                    # The empty English Charge_SuperLong bank has no media.
                    assert all(s['plugin_id'] == 0 and s['source_id'] == 0 and
                               s['cache_id'] == 0 and s['in_memory_size'] == 0
                               for s in refs[key]['description']['sound_sources'])
                    assert data == (b.ROOT/refs[key]['path']).read_bytes()
                description = describe_payload(data,kind,ident)
                assert description['chunks'] == ['BKHD','HIRC'], 'No original audio chunks allowed'
        assert cooked == expected, 'Only strategy and packaged hash may change in native metadata'
        assert used == set(range(len(actual['DataResources']))) and end == len(bulk)
        old_native = base64.b64decode(old_export['Extras'])
        assert native[reader.pos:] == old_native[-16:] and len(native[reader.pos:]) == 16
        for language in cooked['EventLanguageMap']:
            lang = language['key']['LanguageName']
            media = pools.get(lang,{})
            for bank in language['value']['SoundBanks']:
                idx = next(i for i,(_,kind,item) in enumerate(b.traverse(cooked))
                           if kind == 'SoundBanks' and item is bank)
                res = actual['DataResources'][idx]
                data = bulk[res['SerialOffset']:res['SerialOffset']+res['SerialSize']]
                all_sources = describe_payload(data,'SoundBanks',bank['SoundBankId']&0xffffffff)['sound_sources']
                other = [s for s in all_sources if s['plugin_id'] != 0x40001]
                original_other = [s for s in refs[(lang,'SoundBanks',bank['SoundBankId']&0xffffffff)]['description']['sound_sources']
                                  if s['plugin_id'] != 0x40001]
                assert other == original_other and all(s['in_memory_size'] == 0 for s in other)
                sources = [s for s in all_sources if s['plugin_id'] == 0x40001]
                assert {s['source_id'] for s in sources} == set(media)
                assert all(s['plugin_id'] == 0x40001 and s['stream_type'] == 0 and
                           s['in_memory_size'] == media[s['source_id']] for s in sources)
        print('VERIFIED',name,flush=True)
    assert set(assignments) == set(choices) and len(wem_hashes) == 21
    assert len(identities) == len(hash_owners) == 530
    # An unmodified inspected event must never introduce old media for these IDs.
    assert all(e['event'] in names for e in inventory['events'] if any(
        r['kind'] == 'Media' and (r['language'],r['id']) in assignments for r in e['references']))
    files = []
    for row in report['files']:
        path = WORK/'container'/row['name']
        assert path.name.startswith(NAME) and path.stat().st_size == row['bytes'] and sha_file(path) == row['sha256']
        files.append(row)
    assert {p.name for p in (WORK/'container').iterdir()} == {r['name'] for r in files}
    result = {'status':'independent-final-container-readback-verified-runtime-pending',
              'source_report_sha256':sha_file(WORK/'report.json'), 'variant':WORK.name,
              'asset_count':len(assets), 'unique_media_assignments':len(assignments),
              'language_counts':dict(Counter(k[0] for k in assignments)),
              'media_reference_instances':media_instances, 'unique_reviewed_wems':len(wem_hashes),
              'new_distinct_packaged_hashes':len(hash_owners), 'all_v4_wems_byteidentical':True,
              'all_nonempty_banks_match_verified_v4':True, 'source_libraries_included':False,
              'original_voice_media_included':False, 'native_ids_and_duration_unchanged':True,
              'shared_reference_scope':'42 inspected adult combat events; 28 overridden including shared alias',
              'runtime_tested':False, 'files':files, 'total_bytes':sum(r['bytes'] for r in files)}
    write(WORK/'verification.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
