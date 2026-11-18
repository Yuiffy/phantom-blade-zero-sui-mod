"""Build and verify a Jirai-only shared solver overlay atop the installed ChinClean body."""
import argparse
import copy
import json
import shutil
import struct
import sys
from pathlib import Path

import numpy as np
from measure import repo, root

sys.path.insert(0, str(repo / 'models/jirai-chin-clean-v1'))
import common
from ue_pipeline import game_pids

chin = common.ROOT
common.ROOT = root
from package_candidate import extract, inspect_mount
from patch_native import parse_doc
from common import BODY, MODS, diag, read, relative_package, run, sha, snapshot, write

name = 'zzzzzzzzzzz_Sui_JiraiPerf1_12_P'
relative = Path(relative_package(BODY) + '.uasset')
container = root / 'container'
settings = {'IterationCount':8, 'MaxIterationCount':8, 'SubdivisionCount':3}


def performance():
    rows = []
    for path in sorted(root.glob('benchmark-*.json')):
        data = read(path)
        timings = data['timings']
        assert [r['step'] for r in timings] == list(range(60,181))
        values = [r['solve_ms'] for r in timings]
        rows.append(dict(solver=data['solver'],samples=len(values),sha256=sha(path),
                         median_ms=float(np.median(values)),p95_ms=float(np.percentile(values,95))))
    assert [r['solver'] for r in rows] == [[24,6],[8,3],[12,4],[24,6]]
    assert all(rows[1][k] < min(rows[i][k] for i in (0,3))*.3 for k in ['median_ms','p95_ms'])
    return rows


def check_quality():
    report = read(root/'quality-report-8x3.json')
    assert report['passed'] and len(report['records'])==6
    for record in report['records']:
        assert record['passed'] and sha(root/record['file'])==record['sha256']
    return report


def patched_payload(source, doc):
    export, = (e for e in doc['Exports'] if e['ObjectName']=='ChaosClothSharedSimConfig')
    assert [(p['Name'],p['Value']) for p in export['Data']]==list(zip(settings,[24,24,6]))
    data = bytearray(source.with_suffix('.uexp').read_bytes())
    start = export['SerialOffset']-source.stat().st_size
    block = data[start:start+export['SerialSize']]
    # Versioned property tags. Match each field's name, type, value size and original value.
    changed = []
    for prop in export['Data']:
        key = prop['Name']
        tag = struct.pack('<iiiiiiBi',doc['NameMap'].index(key),0,doc['NameMap'].index('IntProperty'),
                          0,0,4,0,prop['Value'])
        assert block.count(tag)==1,key
        offset = start+block.index(tag)+len(tag)-4
        struct.pack_into('<i',data,offset,settings[key])
        changed.append(offset)
    return data, changed


def build():
    costs = performance()
    quality = check_quality()
    before = snapshot()
    source = extract('live-before',[MODS])/relative
    known = chin/'installed-legacy'/relative
    # Native parser offsets must belong to precisely this header and payload.
    assert source.read_bytes()==known.read_bytes() and sha(source.with_suffix('.uexp'))==sha(known.with_suffix('.uexp'))
    doc = read(chin/'independent/native.json')
    rendered,weights,_,details = parse_doc(doc)
    ref = repo/'private/jirai-skirt-shape-v1/variant/independent'
    reference = read(ref/'cloth-native-details.json')
    idx = next(i for i,s in enumerate(reference['sections']) if s['slot']=='MI_Jirai_Skirt')
    section = reference['sections'][idx]
    assert details['sections'][idx]['cloth_maps']==section['cloth_maps']
    lo = section['base_vertex']
    span = slice(lo,lo+section['vertices'])
    assert np.array_equal(rendered[span],np.load(ref/'render-data.npz')['positions'][span])
    assert weights[span]==read(ref/'render-weights.json')[span]
    baseline = inspect_mount('before',[MODS],[BODY])[BODY]
    r8 = read(next((ref/'json').rglob('Hun_Body_Simple.json')))
    def normalize_scope(value):
        return json.dumps(value,sort_keys=True).replace('/EscapeOnly/','/JiraiOnly/')
    for export in r8:
        if export['Type'] in ('ClothingAssetCommon','ChaosClothConfig','ChaosClothSharedSimConfig'):
            current = next(e for e in baseline if e['Name']==export['Name'] and
                           normalize_scope(e.get('Outer'))==normalize_scope(export.get('Outer')))
            assert normalize_scope(current)==normalize_scope(export),export['Name']
    target = root/'legacy'/relative
    target.parent.mkdir(parents=True,exist_ok=True)
    # The installed-set legacy conversion lacks two game import names. Use the
    # original packing header after binding it to the actual installed payload.
    authored = chin/'legacy'/relative
    assert authored.stat().st_size == source.stat().st_size
    assert sha(authored.with_suffix('.uexp')) == sha(source.with_suffix('.uexp'))
    shutil.copy2(authored,target)
    payload, offsets = patched_payload(source,doc)
    target.with_suffix('.uexp').write_bytes(payload)
    container.mkdir(exist_ok=True)
    retoc = diag.TOOLS/'retoc.exe'
    run('package',[retoc,'to-zen','--version','UE5_6','--no-parallel',root/'legacy',container/(name+'.utoc')])
    listing = run('list',[retoc,'list','--path',container/(name+'.utoc')])
    packages = [l.split()[-1].replace('\\','/').removeprefix('../../../') for l in listing.splitlines() if l.strip().endswith('.uasset')]
    assert packages==[relative.as_posix()]
    expected = copy.deepcopy(baseline)
    shared, = (e for e in expected if e['Type']=='ChaosClothSharedSimConfig')
    shared['Properties'].update(settings)
    for label,dirs in [('first',[container,MODS]),('last',[MODS,container])]:
        assert inspect_mount(label,dirs,[BODY])[BODY]==expected
    assert snapshot()==before
    rows = [dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(container.iterdir())]
    assert {r['name'] for r in rows}=={name+ext for ext in ['.pak','.utoc','.ucas']}
    write(root/'expected.json',expected)
    write(root/'candidate.json',dict(before=before,files=rows,body=BODY,source_sha256=sha(source.with_suffix('.uexp')),
          payload_sha256=sha(target.with_suffix('.uexp')),changed_offsets=offsets,costs=costs,
          quality_sha256=sha(root/'quality-report-8x3.json'),quality_passed=quality['passed']))
    print('JIRAI_CANDIDATE_VERIFIED')


def install():
    report = read(root/'candidate.json')
    assert not game_pids() and snapshot()==report['before']
    added = []
    try:
        for row in report['files']:
            path = MODS/row['name']
            src = container/path.name
            assert not game_pids() and sha(src)==row['sha256']
            with path.open('xb') as stream:
                added.append(path)
                stream.write(src.read_bytes())
            assert sha(path)==row['sha256']
        assert inspect_mount('installed',[MODS],[BODY])[BODY]==read(root/'expected.json')
        resolved = extract('live-after',[MODS])/relative
        assert sha(resolved.with_suffix('.uexp'))==report['payload_sha256']
        after = snapshot()
        assert after==sorted(report['before']+report['files'],key=lambda x:x['name'])
    except Exception:
        for path in reversed(added):
            if not game_pids() and sha(path)==sha(container/path.name):
                path.unlink()
        raise
    write(root/'installation.json',dict(verified=True,files=report['files'],before=report['before'],after=after,
                                       readback_payload_sha256=report['payload_sha256']))
    evidence = repo/'evidence/jirai-perf-v1'
    write(evidence/'verification.json',dict(installed=True,scope=BODY,solver=settings,benchmarks=report['costs'],
          quality=check_quality(),old_files_retained=len(report['before']),files_added=report['files'],
          payload_readback_sha256=report['payload_sha256'],changed_payload_offsets=report['changed_offsets'],
          offline_only=True,game_fps_after=None))
    print('JIRAI_INSTALLED_VERIFIED')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['build','install'])
    args=parser.parse_args()
    (build if args.action=='build' else install)()
