"""Independent readback audit for the local source-library voice trial."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import struct
import numpy as np
import psutil
import build_combat_voice_experiment as b
from parse_wwise_events import Reader, describe_payload
from build_snort_experiment import chunks,wave_samples
from resolve_bilingual_voice_inventory import read,write

ROOT=b.ROOT
WORK=ROOT/'variants/reviewed-natural-voice-v4'
AUDIT=ROOT/'public-export-audits/reviewed-natural-voice-v4'

def sha_file(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for data in iter(lambda:f.read(8*1024*1024),b''):h.update(data)
    return h.hexdigest()

def export(j,name):
    return next(e for e in j['Exports'] if e['ObjectName'].lower()==name.lower())

def library_layout(j,name):
    ex=export(j,name);raw=base64.b64decode(ex['Extras'])
    r=Reader(raw,j['NameMap'])
    assert r.object('WwiseAssetLibraryCookedData')=={}
    native=raw[r.pos:r.pos+16];r.pos+=16;n=r.num('i')
    files=[r.object('WwisePackagedFile') for _ in range(n)]
    used=[]
    for f in files:
        f['resource_indices']=[]
        for _ in range(2 if f['PrefetchSize'] else 1):
            padding=r.num('i')
            if padding:
                idx=r.num('i');used.append(idx)
                assert j['DataResources'][idx]['SerialSize']==padding
            idx=r.num('i');used.append(idx);f['resource_indices'].append(idx)
    assert r.pos==len(raw) and used==list(range(len(j['DataResources'])))
    return {'native':native.hex(),'files':files,'indices':used}

def main():
    assert not b.game_pids()
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    for folder in ['logs','readback-json','encoded']:
        (AUDIT/folder).mkdir(parents=True,exist_ok=True)
    b.WORK=AUDIT
    report=read(WORK/'report.json')
    inventory=read(WORK/'bilingual-inventory.json')
    events={e['event']:e for e in inventory['events']}
    chosen={(r['language'],r['media_id']):r for r in report['replacements']}
    old=read(ROOT/'variants/library-natural-voice-v3/report.json')
    review=read(WORK/'review-evidence/user-review.json')
    manifest=read(WORK/'review-evidence/manifest.json')
    snapshot=read(WORK/'review-evidence/snapshot.json')
    assert sha_file(WORK/'review-evidence/user-review.json')==snapshot['review_sha256']
    assert sha_file(WORK/'review-evidence/manifest.json')==review['manifest_sha256']==snapshot['manifest_sha256']
    assert sha_file(ROOT/'variants/library-natural-voice-v3/report.json')==manifest['source_report_sha256']==report['previous_report_sha256']
    assert not review['media'] and len(review['issues'])==12
    candidates={r['id']:r for r in manifest['candidates']}
    current={r['number']:r for r in manifest['current']}
    old_chosen={(r['language'],r['media_id']):r for r in old['replacements']}
    assert set(chosen)==set(old_chosen)=={(r['language'],r['media_id']) for r in manifest['media']}
    assert report['target_events']==old['target_events'] and report['language_counts']=={'Chinese':238,'English(US)':236}
    assert {a['path'] for a in report['assets']}=={a['path'] for a in old['assets']}
    by_old={}
    for issue in manifest['issues']:
        candidate=candidates[review['issues'][issue['id']]['choice']]
        target=(current[candidate['prior_number']]['id'] if candidate['id'].startswith('reuse-') else candidate['id'])
        by_old[issue['old_id']]=(target,candidate)
    changed=0;unchanged=0
    for key,row in chosen.items():
        previous=old_chosen[key]
        assert row['events']==previous['events'] and row['original_sha256']==previous['original_sha256']
        selected=by_old.get(previous['candidate'])
        if selected:
            target,candidate=selected
            assert row['candidate']==target and row['review_choice_changed']
            assert abs(row['replacement_seconds']-candidate['seconds'])<1/48000
            audition=ROOT/'voice-review-round2'/candidate['url']
            assert sha_file(audition)==candidate['sha256']
            if candidate['id'].startswith('reuse-'):
                assert sha_file(WORK/'encoded'/(target+'.wem'))==next(x['wem_sha256'] for x in old['encoding_evidence'] if x['candidate']==target)
                assert sha_file(ROOT/'variants/library-natural-voice-v3/encoded'/(target+'.decoded.wav'))==candidate['sha256']
            else:
                codec=next(x for x in report['encoding_evidence'] if x['candidate']==target)
                assert codec['source_sha256']==candidate['sha256'] and codec['samples']==candidate['samples']
            changed+=1
        else:
            assert not row['review_choice_changed'] and row['candidate']==previous['candidate']
            assert row['replacement_sha256']==previous['replacement_sha256']
            unchanged+=1
    for row in report['container_files']:
        p=ROOT/row['path'];assert p.stat().st_size==row['bytes'] and sha_file(p)==row['sha256']
    expected={a['path'] for a in report['assets']}
    assert {p.relative_to(WORK/'readback').as_posix() for p in (WORK/'readback').rglob('*.uasset')}==expected
    payloads={};audits=[]
    for item in report['assets']:
        name=item['name'];asset=WORK/'readback'/item['path']
        jp=AUDIT/'readback-json'/(name+'.json')
        b.run('readback-'+name,[b.TOOLS/'UAssetGUI.exe','tojson',asset,jp,'VER_UE5_6','PBZ'],b.TOOLS)
        got=read(jp);orig=read(ROOT/item['source_json'])
        assert export(got,name)['Data']==export(orig,name)['Data']
        assert base64.b64decode(export(got,name)['Extras'])==base64.b64decode(export(orig,name)['Extras']), 'Native metadata or ID/index table changed'
        assert got['Imports']==orig['Imports'] and got['NameMap']==orig['NameMap']
        assert len(got['DataResources'])==len(orig['DataResources'])==item['resource_count']
        bulk=asset.with_suffix('.ubulk')
        assert bulk.stat().st_size==item['bulk_bytes'] and sha_file(bulk)==item['bulk_sha256']
        original_asset=(WORK/'original-legacy'/item['path'] if name in ['VO_CN','VO_EN'] else ROOT/'research/extract'/item['path'])
        original_bulk=original_asset.with_suffix('.ubulk')
        assert sha_file(original_bulk)==item['original_bulk_sha256']
        # Every original byte survives, including untouched stream alignment/padding.
        with original_bulk.open('rb') as f,bulk.open('rb') as g:
            while True:
                a=f.read(8*1024*1024)
                if not a:break
                assert g.read(len(a))==a
        patches={p['resource_index']:p for p in item['patches']}
        if name in ['VO_CN','VO_EN']:
            layout=library_layout(got,name)
            assert layout==library_layout(orig,name)
            index=read(ROOT/'research/wwise-libraries'/name/'parsed-index.json')
            assert len(layout['files'])==index['packaged_file_count']
            for file,old_file in zip(layout['files'],index['packaged_files']):
                assert file['resource_indices']==[r['index'] for r in old_file['bulk']]
                assert all(file[k]==old_file[k] for k in file if k!='resource_indices')
        else:
            meta=next(e for e in read(ROOT/'research/adult-wwise-metadata.json') if e['event']==name)
            data=base64.b64decode(export(got,name)['Extras'])
            r=Reader(data,got['NameMap'])
            assert r.object('WwiseLocalizedEventCookedData')==meta['metadata']
            indices=[]
            for language,kind,obj in b.traverse(meta['metadata']):
                if obj['PackagedFile']['PackagingStrategy']==3:
                    idx=r.num('i');indices.append(idx)
                    ref=next(z for z in events[name]['references'] if z['language']==language and z['kind']==kind and z['id']==(obj['SoundBankId' if kind=='SoundBanks' else 'MediaId']&0xffffffff))
                    assert idx==ref['resource_index']
            assert len(data)-r.pos==16
        with bulk.open('rb') as f:
            for idx,res in enumerate(got['DataResources']):
                before=orig['DataResources'][idx]
                patch=patches.get(idx)
                if patch is None:
                    assert res==before
                    continue
                allowed={'SerialOffset','SerialSize','RawSize'}
                assert {k:v for k,v in res.items() if k not in allowed}=={k:v for k,v in before.items() if k not in allowed}
                assert res['SerialOffset']==patch['offset'] and res['SerialSize']==res['RawSize']==patch['bytes']
                assert res['SerialOffset']>=item['original_bulk_bytes']
                f.seek(res['SerialOffset']);data=f.read(res['SerialSize'])
                assert b.sha(data)==patch['sha256']
                key=(patch['language'],patch['kind'],patch['id'])
                assert key not in payloads or payloads[key]==data
                payloads[key]=data
        audits.append({'asset':name,'original_prefix_byteidentical':True,
            'native_metadata_byteidentical':True,'untouched_resource_count':len(got['DataResources'])-len(patches),
            'changed_resource_count':len(patches)})
    # Resolve actual final payloads through every original event reference.
    for name,event in events.items():
        for language in report['languages']:
            refs=[r for r in event['references'] if r['language']==language]
            media={r['id']:r for r in refs if r['kind']=='Media'}
            for bank in (r for r in refs if r['kind']=='SoundBanks'):
                key=(language,'SoundBanks',bank['id'])
                original=(ROOT/bank['path']).read_bytes()
                data=payloads.get(key,original)
                after=describe_payload(data,'SoundBanks',bank['id'])
                before=describe_payload(original,'SoundBanks',bank['id'])
                assert len(data)==len(original)
                for a,z in zip(before['sound_sources'],after['sound_sources']):
                    assert {k:v for k,v in a.items() if k!='in_memory_size'}=={k:v for k,v in z.items() if k!='in_memory_size'}
                    if a['plugin_id']!=0x00040001:
                        assert a==z;continue
                    ref=media[z['source_id']]
                    mkey=(language,'Media',ref['id'])
                    actual=payloads.get(mkey,(ROOT/ref['path']).read_bytes())
                    assert z['in_memory_size']==len(actual)
                    selection=chosen.get((language,ref['id']))
                    if selection:
                        assert b.sha(actual)==selection['replacement_sha256']
                        assert actual==(WORK/'encoded'/(selection['candidate']+'.wem')).read_bytes()
                    else:assert actual==(ROOT/ref['path']).read_bytes()
    stats={}
    for language in report['languages']:
        rows=[]
        for name in report['target_events']:
            refs=[r for r in events[name]['references'] if r['language']==language and r['kind']=='Media']
            assert all((language,r['id']) in chosen for r in refs)
            rows.append({'event':name,'pool_media':len(refs),'replaced':len(refs)})
        stats[language]=rows
    codecs=[]
    for row in report['encoding_evidence']:
        wem=WORK/'encoded'/(row['candidate']+'.wem')
        decoded=AUDIT/'encoded'/(row['candidate']+'.audit-decoded.wav')
        b.run('audit-decode-'+row['candidate'],[ROOT/'research/vgmstream/vgmstream-cli.exe','-i','-o',decoded,wem])
        a=wave_samples(ROOT/row['source']);z=wave_samples(decoded)
        assert b.sha(wem.read_bytes())==row['wem_sha256'] and sha_file(ROOT/row['source'])==row['source_sha256']
        assert len(a)==len(z)==row['samples']
        corr=float(np.sum(a*z)/np.sqrt(np.sum(a*a)*np.sum(z*z)))
        snr=float(10*np.log10(np.sum(a*a)/np.sum((a-z)**2)))
        assert corr>.98 and snr>18
        codecs.append({'candidate':row['candidate'],'samples':len(a),'snr_db':snr,'correlation':corr})
    for row in chosen.values():
        if row['replacement_seconds']>row['cap_seconds']+1/48000:
            assert row['review_choice_changed'], 'Longer clips must be explicitly human selected'
    result={'status':'independently-readback-verified-runtime-pending','build_id':report['build_id'],
        'source_report_sha256':sha_file(WORK/'report.json'),'assets':audits,
        'languages':report['languages'],'language_counts':report['language_counts'],
        'target_event_pool_coverage':stats,'codecs':codecs,
        'original_events_preserve_external_packaging':True,'shared_media_consistent_in_42_inspected_events':True,
        'unchanged_v3_media_byteidentical':unchanged,'human_selected_changed_media':changed,'reviewed_issue_count':12,'exact_round2_choices_verified':True,'longer_selected_clips_preserved':True,'original_library_prefixes_unchanged':True,
        'language_settings_changed':False,'runtime_tested':False,'selected_changes_human_reviewed':True,'runtime_duration_playback_pending':True}
    write(AUDIT/'verification.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ['assets','target_event_pool_coverage','codecs']},indent=2))
    print('ASSETS',len(audits),'CODECS',len(codecs),'CHANGED_PAYLOADS',len(payloads))

if __name__=='__main__':main()
