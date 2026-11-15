"""Build an event-local v5 candidate from the immutable reviewed v4 WEMs.

Maintainer tool only: players install the resulting triplet without Python.
Build 26367565, bank v154, nonstreaming Chinese/English combat events only.
New packaged hashes isolate BulkData from the original asset-library cache.
No event, bank, media, HIRC or cache IDs are changed. Runtime test is pending.
"""
import base64
import copy
import hashlib
import json
import shutil
import struct
from pathlib import Path

import psutil
import build_combat_voice_experiment as b
from parse_wwise_events import Reader
from paths import ROOT, game_root
from resolve_bilingual_voice_inventory import read, write

WORK = ROOT/'variants/compact-reviewed-voice-v5'
V4 = ROOT/'variants/reviewed-natural-voice-v4'
NAME = 'z_Sui_Hun_NaturalVoice_Compact_v5_P'


class FieldReader(Reader):
    """Track serialized property positions, never search for integer bytes."""
    def __init__(self, data, names):
        super().__init__(data, names)
        self.stack = []
        self.packaged = {}

    def object(self, name):
        fields = {}
        self.stack.append((name, fields))
        result = super().object(name)
        self.stack.pop()
        if name == 'WwisePackagedFile':
            self.packaged[id(result)] = fields
        return result

    def prop(self, field):
        if self.stack and self.stack[-1][0] == 'WwisePackagedFile' and 'name' in field:
            self.stack[-1][1][field['name']] = self.pos
        return super().prop(field)


def sha_file(path):
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inputs():
    report = read(V4/'report.json')
    verification = read(V4/'verification.json')
    assert verification['source_report_sha256'] == sha_file(V4/'report.json')
    assert verification['exact_round2_choices_verified']
    inventory = read(V4/'bilingual-inventory.json')
    metadata = {e['event']: e for e in read(ROOT/'research/adult-wwise-metadata.json')}
    selections = {(r['language'], r['media_id']): r for r in report['replacements']}
    assert len(selections) == 474
    wem = {}
    for row in selections.values():
        data = (V4/'encoded'/(row['candidate']+'.wem')).read_bytes()
        assert b.sha(data) == row['replacement_sha256']
        wem[row['candidate']] = data
    assert len(wem) == 21
    targets = set(report['target_events'])
    # Same MediaID must use the same bytes/hash in every inspected event.
    affected = [e for e in inventory['events'] if e['event'] in targets or any(
        r['kind'] == 'Media' and (r['language'], r['id']) in selections
        for r in e['references'])]
    assert len(affected) == 28
    for event in affected:
        assert all((r['language'], r['id']) in selections for r in event['references']
                   if r['kind'] == 'Media'), 'Partial random pool requires a different design'
    reserved = {item['PackagedFile']['Hash'] for e in metadata.values()
                for _, _, item in b.traverse(e['metadata'])}
    for lib in ['VO_CN', 'VO_EN']:
        reserved.update(r['Hash'] for r in read(ROOT/'research/wwise-libraries'/lib/'parsed-index.json')['packaged_files'])
    return report, metadata, selections, wem, affected, reserved


def allocate_hashes(payloads, reserved):
    """Deterministic IDs with checked collisions against both local VO indexes."""
    used = set(reserved) | {0}
    result = {}
    for key in sorted(payloads):
        salt = 0
        while True:
            token = json.dumps(['Sui-reviewed-v5', *key, b.sha(payloads[key]), salt], separators=(',', ':'))
            value = int.from_bytes(hashlib.sha256(token.encode()).digest()[:4], 'little')
            if value not in used:
                break
            salt += 1
        result[key] = value
        used.add(value)
    return result


def prepare(event, meta, payloads, hashes, template):
    name = event['event']
    source = ROOT/'research/adult-audio-json'/(name+'.json')
    assert sha_file(source) == meta['json_sha256']
    original = read(source)
    edited = copy.deepcopy(original)
    ex = next(x for x in edited['Exports'] if x['ObjectName'].lower() == name.lower())
    native = base64.b64decode(ex['Extras'])
    reader = FieldReader(native, edited['NameMap'])
    cooked = reader.object('WwiseLocalizedEventCookedData')
    assert cooked == meta['metadata'] and reader.pos == meta['metadata_bytes']
    for _, _, item in b.traverse(cooked):
        if item['PackagedFile']['PackagingStrategy'] == 3:
            reader.num('i')
    tail = native[reader.pos:]
    assert len(tail) == 16
    native_out = bytearray(native[:meta['metadata_bytes']])
    resources, indices, rows = [], [], []
    bulk = bytearray()
    for lang, kind, item in b.traverse(cooked):
        ident = item['SoundBankId' if kind == 'SoundBanks' else 'MediaId'] & 0xffffffff
        key = (lang, kind, ident)
        pf = item['PackagedFile']
        assert lang in ['Chinese', 'English(US)']
        assert pf['PackagingStrategy'] in [3, 4] and not pf['bStreaming'] and not pf['PrefetchSize']
        fields = reader.packaged[id(pf)]
        assert 'Hash' in fields and 'PackagingStrategy' in fields
        assert native_out[fields['PackagingStrategy']] == pf['PackagingStrategy']
        native_out[fields['PackagingStrategy']] = 3
        struct.pack_into('<I', native_out, fields['Hash'], hashes[key])
        alignment = max(16, pf['MemoryAlignment'])
        assert alignment & (alignment-1) == 0 and alignment <= 262144
        padding = (-len(bulk)) % alignment
        bulk.extend(b'\0'*padding)
        data = payloads[key]
        resource = copy.deepcopy(template)
        resource.update(SerialOffset=len(bulk), SerialSize=len(data), RawSize=len(data))
        indices.append(len(resources))
        resources.append(resource)
        bulk.extend(data)
        rows.append({'language':lang, 'kind':kind, 'id':ident,
                     'old_hash':pf['Hash'], 'hash':hashes[key],
                     'bytes':len(data), 'sha256':b.sha(data)})
    ex['Extras'] = base64.b64encode(native_out+b''.join(struct.pack('<i', i) for i in indices)+tail).decode()
    edited['DataResources'] = resources
    edited['DataResourceVersion'] = 'Initial'
    dest = (WORK/'stage'/b.ASSET_DIR/name).with_suffix('.uasset')
    dest.parent.mkdir(parents=True, exist_ok=True)
    jp = WORK/'edited-json'/(name+'.json')
    write(jp, edited)
    b.run('fromjson-'+name, [b.TOOLS/'UAssetGUI.exe', 'fromjson', jp, dest, 'PBZ'], b.TOOLS)
    dest.with_suffix('.ubulk').write_bytes(bulk)
    return {'event':name, 'resources':rows, 'bulk_bytes':len(bulk), 'bulk_sha256':b.sha(bulk)}


def main():
    if not __debug__:
        raise RuntimeError('Do not disable format assertions with python -O')
    assert not b.game_pids(), 'Defer while PBZ is running'
    assert not (WORK/'report.json').exists(), 'Already built; verify instead'
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    policy = read(ROOT/'project-policy.json')
    assert all(policy[k] is False for k in ['tts_enabled','voice_conversion_enabled','new_asr_enabled','source_separation_enabled'])
    for name in ['logs', 'edited-json', 'readback-json', 'container']:
        (WORK/name).mkdir(parents=True, exist_ok=True)
    b.WORK = WORK
    v4, metadata, choices, wem, events, reserved = inputs()
    payloads = {}
    for event in events:
        for language in ['Chinese', 'English(US)']:
            media = {r['id']:wem[choices[(language, r['id'])]['candidate']]
                     for r in event['references'] if r['language'] == language and r['kind'] == 'Media'}
            for ref in event['references']:
                if ref['language'] != language:
                    continue
                original = (ROOT/ref['path']).read_bytes()
                assert b.sha(original) == ref['sha256']
                data = media[ref['id']] if ref['kind'] == 'Media' else b.patch_bank(original, ref['id'], media)[0]
                key = (language, ref['kind'], ref['id'])
                assert key not in payloads or payloads[key] == data
                payloads[key] = data
    hashes = allocate_hashes(payloads, reserved)
    template = read(ROOT/'research/adult-audio-json/SFX_Combat_VO_Hun_Snort.json')['DataResources'][0]
    assert template['LegacyBulkDataFlags'] == 0x10501
    assets = []
    for event in events:
        assets.append(prepare(event, metadata[event['event']], payloads, hashes, template))
        print('STAGED', event['event'], flush=True)
    utoc = WORK/'container'/(NAME+'.utoc')
    b.run('pack', [b.TOOLS/'retoc.exe', 'to-zen', '--version', 'UE5_6', '--no-parallel', WORK/'stage', utoc], b.TOOLS)
    listing = b.run('list', [b.TOOLS/'retoc.exe', 'list', '--path', utoc], b.TOOLS)
    listed = [s for s in listing.splitlines() if '.uasset' in s]
    assert len(listed) == 28 and all(sum(a['event']+'.uasset' in s for s in listed) == 1 for a in assets)
    inp = WORK/'readback-input'
    inp.mkdir(exist_ok=True)
    for ext in ['.utoc', '.ucas']:
        source = game_root()/'ProjectPBZ/Content/Paks'/('global'+ext)
        assert source.stat().st_size < 5*1024*1024
        shutil.copyfile(source, inp/source.name)
    files = sorted((WORK/'container').iterdir())
    assert {p.suffix for p in files} == {'.pak', '.ucas', '.utoc'} and len(files) == 3
    assert sum(p.stat().st_size for p in files) < 100*1024*1024
    for p in files:
        shutil.copyfile(p, inp/p.name)
    b.run('unpack', [b.TOOLS/'retoc.exe', 'to-legacy', '--version', 'UE5_6', '--no-shaders', '--no-parallel', inp, WORK/'readback'], b.TOOLS)
    report = {'status':'built-awaiting-independent-verification-and-runtime', 'variant':WORK.name,
              'build_id':'26367565', 'v4_report_sha256':sha_file(V4/'report.json'),
              'target_events':v4['target_events'], 'shared_alias_events':sorted({e['event'] for e in events}-set(v4['target_events'])),
              'unique_reviewed_wems':len(wem), 'unique_reviewed_wem_bytes':sum(map(len, wem.values())),
              'media_assignments':len(choices), 'asset_count':len(assets), 'assets':assets,
              'source_library_override':False, 'original_voice_media_included':False,
              'new_packaged_hash_count':len(hashes), 'collision_scope':'42 inspected events plus complete VO_CN and VO_EN packaged indexes',
              'preserved_ids':['EventID','SoundBankID','MediaID','HIRC IDs','CacheID'],
              'audio_regenerated':False, 'runtime_tested':False,
              'files':[{'name':p.name, 'bytes':p.stat().st_size, 'sha256':sha_file(p)} for p in files]}
    write(WORK/'report.json', report)
    print(json.dumps({k:v for k,v in report.items() if k != 'assets'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
