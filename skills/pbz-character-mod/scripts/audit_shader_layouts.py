"""Read-only shader layout audit for the PBZ build 26367565 case format.
Fails on unsupported structures; never changes signatures or input files.
"""
import base64
import hashlib
import json
import struct
from pathlib import Path

def parse(name, data):
    first = data.index(b'FMaterialShaderMapContent\0')
    start = first - 12
    resources, count = struct.unpack_from('<ii', data, start)
    assert 0 < resources < 20 and 0 < count < 1000
    pos = first - 4
    names = []
    for _ in range(count):
        size = struct.unpack_from('<i', data, pos)[0]
        pos += 4
        assert 0 < size < 2048
        value = data[pos:pos + size]
        assert value[-1] == 0
        names.append(value[:-1].decode('ascii'))
        pos += size + 4  # FNameEntrySerialized + two uint16 hashes
    loc_count = struct.unpack_from('<i', data, pos)[0]
    pos += 4
    assert loc_count == resources
    locs = []
    for _ in range(loc_count):
        locs.append(struct.unpack_from('<IBB', data, pos))
        pos += 6
    num_bytes = struct.unpack_from('<i', data, pos)[0]
    pos += 4
    assert locs[0][0] == 0 and 0 < num_bytes <= len(data) - pos
    images = []
    for i, (offset, feature, quality) in enumerate(locs):
        q = pos + offset
        limit = pos + (locs[i + 1][0] if i + 1 < len(locs) else num_bytes)
        # FMaterial::SerializeInlineShaderMap: two bools; cooked ShaderMapId:
        # quality uint8, feature int32, FSHAHash[20], platform layout[8].
        cooked, valid = struct.unpack_from('<II', data, q)
        assert cooked == valid == 1
        assert data[q + 8] == quality and struct.unpack_from('<i', data, q + 9)[0] == feature
        id_layout = struct.unpack_from('<II', data, q + 33)
        # FMemoryImageResult::LoadFromArchive: layout[8], size, image, dependencies.
        layout = struct.unpack_from('<II', data, q + 41)
        assert layout == id_layout == (8, 5)
        frozen_size = struct.unpack_from('<I', data, q + 49)[0]
        dep_pos = q + 53 + frozen_size
        assert q < dep_pos < limit
        dep_count = struct.unpack_from('<i', data, dep_pos)[0]
        assert 1 <= dep_count <= len(names) and dep_pos + 4 + dep_count * 32 < limit
        deps = []
        for j in range(dep_count):
            at = dep_pos + 4 + j * 32
            idx, number, size = struct.unpack_from('<iiI', data, at)
            assert 0 <= idx < len(names) and number == 0 and 0 < size < 65536
            deps.append({'name': names[idx], 'size': size, 'hash': data[at + 12:at + 32].hex()})
        assert len({d['name'] for d in deps}) == len(deps)
        assert deps[0]['name'] == 'FMaterialShaderMapContent'
        images.append({'feature_level': feature, 'quality_level': quality,
                       'platform_layout': layout, 'frozen_size': frozen_size,
                       'dependency_offset': dep_pos, 'dependencies': deps})
    return {'name': name, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data),
            'resource_count': resources, 'resource_bytes': num_bytes, 'images': images}


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('inputs', nargs='+', type=Path)
    ap.add_argument('--export', help='ObjectName for JSON with multiple exports')
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    records = []
    for path in args.inputs:
        data = path.read_bytes()
        if path.suffix.lower() == '.json':
            doc = json.loads(data.decode('utf-8-sig'))
            exports = [e for e in doc['Exports'] if e.get('Extras') and
                       (not args.export or e.get('ObjectName') == args.export)]
            if len(exports) != 1:
                raise ValueError('Select exactly one shader export with --export')
            data = base64.b64decode(exports[0]['Extras'], validate=True)
        records.append(parse(path.name, data))
    out = json.dumps(records, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.write_text(out, encoding='utf-8')
    else:
        print(out)

if __name__ == '__main__':
    if not __debug__:
        raise RuntimeError('Do not run with -O: structural assertions are required')
    main()
