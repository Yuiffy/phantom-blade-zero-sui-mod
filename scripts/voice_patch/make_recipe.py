"""Maintainer tool: derive a small recipe from a locally verified v4 container.

Private inputs and their paths are never copied into the bundle. A new game
build requires a new independently verified candidate, not editing version IDs.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import shutil

from generate import digest, file_hash, idle, read_key
from iostore import RangeReader, Toc, require


class Payload:
    def __init__(self):
        self.data = bytearray()
        self.offsets = {}

    def add(self, data):
        require(len(data) > 0, 'Empty ADD')
        if data not in self.offsets:
            self.offsets[data] = len(self.data)
            self.data.extend(data)
        return ['add', self.offsets[data], len(data)]


def same_offset_delta(old, new, base, payload):
    """Only changed byte runs are included; untouched bank/metadata stays COPY."""
    require(len(old) == len(new), 'Only equal-sized native metadata/bank patches are verified')
    result = []
    start = 0
    while start < len(new):
        equal = old[start] == new[start]
        end = start + 1
        while end < len(new) and (old[end] == new[end]) == equal:
            end += 1
        result.append(['copy', base + start, end-start] if equal else payload.add(new[start:end]))
        start = end
    return result


def range_hash(stream, offset, size):
    stream.seek(offset)
    h = hashlib.sha256()
    while size:
        data = stream.read(min(size, 4*1048576))
        require(bool(data), 'Truncated candidate container')
        h.update(data); size -= len(data)
    return h.hexdigest()


def write_provenance(root, destination, report):
    natural = json.loads((root/'audio/natural-segments/manifest.json').read_text(encoding='utf-8'))
    review = json.loads((root/'variants/reviewed-natural-voice-v4/review-evidence/manifest.json').read_text(encoding='utf-8'))
    known = {c['id']: c for c in natural['voices']}
    choices = {c['id']: c for c in review['candidates']}
    used = set(p['candidate'] for p in report['replacements'])
    provenance = []
    for entry in report['encoding_evidence']:
        if entry['candidate'] not in used:
            continue
        row = {k:entry[k] for k in ('candidate','source_sha256','wem_sha256',
                                    'duration_seconds','samples')}
        cid = entry['candidate']
        if cid in known:
            source = known[cid]
            require(source['quality']['sha256'] == entry['source_sha256'], 'Candidate source provenance mismatch')
            row.update({'source_file': Path(source['original_recording']).name,
                        'recording_sha256': source['original_sha256'],
                        'range_in_normalized_pcm': source['range']})
        else:
            source = choices[cid]
            require(source['sha256'] == entry['source_sha256'], 'Audition source provenance mismatch')
            row.update({'source_file': source['source_file'],
                        'recording_sha256': source['source_sha256'],
                        'range_in_normalized_pcm': {'samples':source['source_range_samples'],
                                                    'seconds':source['source_range_seconds'], 'rate':48000}})
        provenance.append(row)
    require(len(provenance) == 21, 'Missing selected audio provenance')
    wems = [root/'variants/reviewed-natural-voice-v4/encoded'/(c+'.wem') for c in used]
    (destination/'audio-provenance.json').write_text(json.dumps({
        'source_project': 'Yuiffy/suiji-sui-button',
        'synthetic_audio': False, 'time_stretching': False, 'target_duration_truncation': False,
        'license': 'Character/recording rights remain with their respective owners; not MIT.',
        'encoding': provenance, 'unique_wem_count': len(wems),
        'unique_wem_bytes': sum(p.stat().st_size for p in wems),
        'review_snapshot_sha256': report['review_snapshot_sha256']}, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def make(root, destination, source_reader):
    root, destination = Path(root), Path(destination)
    require(not destination.exists(), 'Bundle destination already exists')
    variant = root / 'variants/reviewed-natural-voice-v4'
    report = json.loads((variant / 'report.json').read_text(encoding='utf-8'))
    target_toc_path = next((variant/'container').glob('*.utoc'))
    target_toc = Toc(target_toc_path)
    payload = Payload()
    chunks = []
    seen_assets = set()
    by_size = {a['original_bulk_bytes']: a for a in report['assets']}
    require(len(by_size) == 8, 'Expected eight distinct original bulk sizes')
    media = {file_hash(p): p for p in (variant/'encoded').glob('*.wem')}
    require(len(media) == 21, 'Expected 21 reviewed WEM payloads')
    with target_toc_path.with_suffix('.ucas').open('rb') as target:
        expected_position = 0
        for cid in target_toc.chunks:
            idle()
            physical, size = target_toc.plain_chunk_position(cid)
            require(physical == expected_position, 'Unexpected target chunk order or physical gap')
            expected_position += size
            chunk = {'id': cid, 'bytes': size, 'sha256': range_hash(target, physical, size)}
            if cid.endswith('06'):
                require(size == 256, 'Unexpected generated container header')
                target.seek(physical)
                chunk['ops'] = [payload.add(target.read(size))]
            else:
                source_size = source_reader.chunk(cid)[1]
                if cid.endswith('01'):
                    old = source_reader.read(cid, 0, source_size)
                    target.seek(physical); new = target.read(size)
                    chunk['source'] = {'id': cid, 'bytes': source_size, 'sha256': digest(old)}
                    chunk['ops'] = same_offset_delta(old, new, 0, payload)
                else:
                    require(cid.endswith('02') and source_size in by_size, 'Unexpected bulk chunk')
                    asset = by_size[source_size]
                    seen_assets.add(asset['name'])
                    library = asset['name'] in ('VO_CN', 'VO_EN')
                    relative = Path(asset['path']).with_suffix('.ubulk')
                    original = ((variant/'original-legacy'/relative) if library
                                else (root/'research/extract'/relative))
                    require(original.stat().st_size == source_size and
                            file_hash(original) == asset['original_bulk_sha256'], 'Private source bulk hash mismatch')
                    require(range_hash(target, physical, source_size) == asset['original_bulk_sha256'],
                            'Candidate did not preserve original bulk prefix')
                    chunk['source'] = {'id': cid, 'bytes': source_size, 'sha256': asset['original_bulk_sha256']}
                    ops = [['copy', 0, source_size]]
                    cursor = source_size
                    with original.open('rb') as old:
                        for patch in sorted(asset['patches'], key=lambda p:p['offset']):
                            offset, length = patch['offset'], patch['bytes']
                            require(offset >= cursor, 'Overlapping appended patches')
                            target.seek(physical+cursor)
                            gap = target.read(offset-cursor)
                            require(not any(gap), 'Nonzero alignment gap')
                            if gap:
                                ops.append(['zero', len(gap)])
                            target.seek(physical+offset); data = target.read(length)
                            require(digest(data) == patch['sha256'], 'Candidate patch mismatch')
                            if patch['kind'] == 'Media':
                                require(digest(data) in media and media[digest(data)].read_bytes() == data,
                                        'ADD media is not a reviewed Sui WEM')
                                ops.append(payload.add(data))
                            else:
                                require(patch['kind'] == 'SoundBanks', 'Unknown patch kind')
                                old.seek(patch['original_offset']); source = old.read(patch['original_bytes'])
                                require(digest(source) == patch['original_sha256'], 'Original bank hash mismatch')
                                ops.extend(same_offset_delta(source, data, patch['original_offset'], payload))
                            cursor = offset + length
                    require(cursor == size, 'Unexpected trailing target bulk data')
                    chunk['ops'] = ops
            chunks.append(chunk)
    require(len(chunks) == 17 and len(seen_assets) == 8, 'Unexpected asset scope')
    outputs = []
    for ext in ('pak', 'utoc', 'ucas'):
        p = target_toc_path.with_suffix('.'+ext)
        item = {'name': p.name, 'bytes': p.stat().st_size, 'sha256': file_hash(p)}
        if ext != 'ucas':
            item['template'] = ext+'.bin'
        outputs.append(item)
    recipe = {'format': 'pbz-voice-recipe-1', 'variant': report['variant'],
              'build_id': report['build_id'], 'source_toc_sha256': digest(source_reader.data),
              'payload': {'name': 'payload.bin', 'bytes': len(payload.data), 'sha256': digest(payload.data)},
              'chunks': chunks, 'outputs': outputs}
    destination.mkdir(parents=True)
    for item in outputs:
        if 'template' in item:
            shutil.copyfile(target_toc_path.with_suffix('.'+item['name'].rsplit('.',1)[1]), destination/item['template'])
    (destination/'payload.bin').write_bytes(payload.data)
    (destination/'recipe.json').write_text(json.dumps(recipe, indent=2)+'\n', encoding='utf-8')
    write_provenance(root, destination, report)
    print(json.dumps({'chunks': len(chunks), 'payload_bytes': len(payload.data),
                      'bundle_bytes': sum(p.stat().st_size for p in destination.iterdir())}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-root', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--source-toc', type=Path, required=True)
    parser.add_argument('--oodle-dll', type=Path, required=True)
    parser.add_argument('--key-file', type=Path)
    parser.add_argument('--bladesmith-config', type=Path)
    args = parser.parse_args()
    idle()
    ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
    with RangeReader(args.source_toc, key=read_key(args), oodle_dll=args.oodle_dll) as source:
        make(args.task_root, args.destination, source)


if __name__ == '__main__':
    main()
