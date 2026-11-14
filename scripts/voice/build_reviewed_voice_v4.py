"""Apply the immutable round-two human choices to the working v3 library layout.

LOCAL ONLY. Original game payloads remain in these containers. No synthesis,
gain, time stretching or duration-fitting edits. Runtime playback remains pending.
"""
import copy
import json
from pathlib import Path
import shutil
import wave
import psutil
import build_library_voice_variant as lib
import build_combat_voice_experiment as b
from resolve_bilingual_voice_inventory import read, write
from verify_library_voice_variant import sha_file
from paths import game_root

ROOT = b.ROOT
OLD = ROOT/'variants/library-natural-voice-v3'
WORK = ROOT/'variants/reviewed-natural-voice-v4'
NAME = 'z_Sui_Hun_NaturalVoice_Reviewed_v4_P'
EVIDENCE = WORK/'review-evidence'


def pcm(path):
    with wave.open(str(path), 'rb') as f:
        assert f.getparams()[:3] == (1, 2, 48000)
        return f.readframes(f.getnframes())


def resolve():
    snapshot = read(EVIDENCE/'snapshot.json')
    assert sha_file(EVIDENCE/'manifest.json') == snapshot['manifest_sha256']
    assert sha_file(EVIDENCE/'user-review.json') == snapshot['review_sha256']
    review = read(EVIDENCE/'user-review.json')
    manifest = read(EVIDENCE/'manifest.json')
    old = read(OLD/'report.json')
    assert sha_file(OLD/'report.json') == manifest['source_report_sha256']
    assert review['manifest_sha256'] == snapshot['manifest_sha256'] and not review['media']
    issues = {x['id']: x for x in manifest['issues']}
    candidates = {x['id']: x for x in manifest['candidates']}
    current = {x['number']: x for x in manifest['current']}
    assert set(issues) == set(review['issues']) and len(issues) == 12
    mapping = {}
    sources = {}
    for issue_id, selection in review['issues'].items():
        issue = issues[issue_id]
        candidate = candidates[selection['choice']]
        audition = ROOT/'voice-review-round2'/candidate['url']
        assert sha_file(audition) == candidate['sha256']
        assert len(pcm(audition))//2 == candidate['samples']
        if candidate['id'].startswith('reuse-'):
            target = current[candidate['prior_number']]['id']
            assert sha_file(OLD/'encoded'/(target+'.decoded.wav')) == candidate['sha256']
        else:
            target = candidate['id']
            context = ROOT/'voice-review-round2'/candidate['context_url']
            a, z = candidate['source_range_samples']
            assert pcm(audition) == pcm(context)[a*2:z*2]
        mapping[issue['old_id']] = target
        sources[target] = candidate
    chosen = copy.deepcopy(old['replacements'])
    changes = []
    for row in chosen:
        previous = row['candidate']
        row['previous_v3_candidate'] = previous
        row['previous_v3_sha256'] = row['replacement_sha256']
        if previous in mapping:
            target = mapping[previous]
            source = sources[target]
            row.update(candidate=target, replacement_seconds=source['seconds'],
                       review='user-selected-round2', review_candidate_id=source['id'])
            changes.append({'language': row['language'], 'media_id': row['media_id'],
                            'from': previous, 'to': target, 'review_candidate': source['id']})
        row['review_choice_changed'] = previous in mapping
    assert len(chosen) == 474
    return old, manifest, chosen, sources, changes


def duration_audit(manifest, chosen):
    """Report observed metadata, not an unproven playback-time guarantee."""
    event_max = {e['id']: e['event_duration']['maximum_seconds'] for e in manifest['events']}
    longer = []
    for row in chosen:
        if row['replacement_seconds'] > row['cap_seconds']+1/48000:
            assert row['review_choice_changed']
            longer.append({k:row[k] for k in ['language','media_id','candidate','replacement_seconds','cap_seconds','events']})
    action_properties = []
    for path in (ROOT/'research/voice-jump-diagnosis/abilities').rglob('*.json'):
        for obj in read(path):
            props = obj.get('Properties') or {}
            refs = [v['ObjectPath'] for v in props.values() if isinstance(v,dict)
                    and '/Wwise/Events/VO/' in v.get('ObjectPath','')]
            if refs:
                action_properties.append({'path':str(path.relative_to(ROOT)),
                                          'type':obj['Type'],'name':obj['Name'],'properties':props})
    audit = {'status':'preserve-complete-user-selected-audio-runtime-window-pending',
             'previous_cap_basis':'min(original decoded media duration, serialized event MaximumDuration); conservative v3 selection policy, not independently established as a forced stop',
             'event_maximum_seconds':event_max,'longer_than_previous_policy':longer,
             'serialized_voice_actions_inspected':len(action_properties),
             'voice_action_properties':action_properties,
             'UAkAudioEvent_parser_sha256':sha_file(ROOT/'research/primary-source/UAkAudioEvent.cs'),
             'native_event_metadata_changed':False,'bank_changes':'in_memory_size only',
             'no_proof_of_unconditional_full_runtime_playback':True,
             'runtime_check':'Listen for cutoff/overlap on quick repeated attacks, especially selected 1.29-second new-zap-aha. No runtime trace available.',
             'duration_fitting_truncation':False,'time_stretch':False}
    write(EVIDENCE/'duration-audit.json',audit)


def main():
    assert not b.game_pids()
    assert not (WORK/'report.json').exists(), 'Already built; verify instead'
    psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    policy=read(ROOT/'project-policy.json')
    assert all(policy[k] is False for k in ['tts_enabled','voice_conversion_enabled','new_asr_enabled','source_separation_enabled'])
    for name in ['logs','encoded','edited-json','container','readback-json','source-json']:
        (WORK/name).mkdir(parents=True,exist_ok=True)
    b.WORK=lib.WORK=WORK
    old, manifest, selections, sources, changes = resolve()
    duration_audit(manifest,selections)
    # Copy immutable original inputs into the new variant, leaving v3 untouched.
    for language, label in lib.LANGS.items():
        rel=lib.ASSET/(label+'.ubulk')
        dest=WORK/'original-legacy'/rel
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copyfile(OLD/'original-legacy'/rel,dest)
        assert sha_file(dest)==sha_file(OLD/'original-legacy'/rel)
        shutil.copyfile(OLD/'source-json'/(label+'.json'),WORK/'source-json'/(label+'.json'))
    shutil.copyfile(OLD/'bilingual-inventory.json',WORK/'bilingual-inventory.json')
    inventory=read(WORK/'bilingual-inventory.json')
    events={e['event']:e for e in inventory['events']}
    chosen={(r['language'],r['media_id']):r for r in selections}
    codecs={c['candidate']:c for c in old['encoding_evidence']}
    encoded={}; encoding=[]
    for target in sorted({c['candidate'] for c in selections}):
        if target in codecs:
            evidence=copy.deepcopy(codecs[target])
            for ext in ['.wem','.decoded.wav']:
                shutil.copyfile(OLD/'encoded'/(target+ext),WORK/'encoded'/(target+ext))
            data=(WORK/'encoded'/(target+'.wem')).read_bytes()
            assert b.sha(data)==evidence['wem_sha256']
        else:
            source=sources[target]
            voice={'id':target,'output':(Path('voice-review-round2')/source['url']).as_posix(),
                   'quality':{'sha256':source['sha256']},'kind':'original-recording-cut',
                   'review':'user-selected-round2'}
            data,evidence=b.encode(voice)
            assert evidence['samples']==source['samples']
        encoded[target]=data;encoding.append(evidence)
    for row in selections:
        row['replacement_sha256']=b.sha(encoded[row['candidate']])
        if not row['review_choice_changed']:
            assert row['replacement_sha256']==row['previous_v3_sha256']
    changed_payloads={};bank_evidence=[]
    for name,event in events.items():
        for language in lib.LANGS:
            media={r['id']:encoded[chosen[(language,r['id'])]['candidate']]
                   for r in event['references'] if r['language']==language and r['kind']=='Media'
                   and (language,r['id']) in chosen}
            if not media:continue
            for ref in event['references']:
                if ref['language']!=language:continue
                original=(ROOT/ref['path']).read_bytes()
                assert b.sha(original)==ref['sha256']
                if ref['kind']=='Media':
                    if ref['id'] not in media:continue
                    data=media[ref['id']]
                else:
                    data,patches=b.patch_bank(original,ref['id'],media)
                    bank_evidence.append({'language':language,'event':name,'bank_id':ref['id'],'patches':patches})
                key=(language,ref['kind'],ref['id'])
                assert key not in changed_payloads or changed_payloads[key][0]==data
                changed_payloads[key]=(data,ref)
    staged=[];covered=set()
    for language,label in lib.LANGS.items():
        index=read(ROOT/'research/wwise-libraries'/label/'parsed-index.json')
        by_hash={r['Hash']:r for r in index['packaged_files']}
        patches={}
        for key,(data,ref) in changed_payloads.items():
            if key[0]!=language or ref['packaging_strategy']!=4:continue
            f=by_hash[ref['packaged_hash']]
            assert not f['bStreaming'] and not f['PrefetchSize'] and len(f['bulk'])==1
            idx=f['bulk'][0]['index']
            detail={'language':language,'kind':ref['kind'],'id':ref['id'],'packaged_hash':ref['packaged_hash'],
                    'original_sha256':ref['sha256'],'alignment':f['MemoryAlignment'],
                    'events':sorted({n for n,e in events.items() if any(r['language']==language and r['kind']==ref['kind'] and r['id']==ref['id'] for r in e['references'])})}
            assert idx not in patches
            patches[idx]=(data,detail);covered.add(key)
        staged.append(lib.stage_patch(label,WORK/'source-json'/(label+'.json'),patches))
        print('STAGED',label,len(patches),flush=True)
    for name,event in events.items():
        patches={}
        for ref in event['references']:
            key=(ref['language'],ref['kind'],ref['id'])
            if ref['packaging_strategy']!=3 or key not in changed_payloads:continue
            data,_=changed_payloads[key]
            detail={'language':ref['language'],'kind':ref['kind'],'id':ref['id'],
                    'packaged_hash':ref['packaged_hash'],'original_sha256':ref['sha256'],'events':[name]}
            patches[ref['resource_index']]=(data,detail);covered.add(key)
        if patches:staged.append(lib.stage_patch(name,ROOT/'research/adult-audio-json'/(name+'.json'),patches))
    assert len(staged)==8 and covered==set(changed_payloads)
    utoc=WORK/'container'/(NAME+'.utoc')
    b.run('pack',[b.TOOLS/'retoc.exe','to-zen','--version','UE5_6','--no-parallel',WORK/'stage',utoc],b.TOOLS)
    listing=b.run('list',[b.TOOLS/'retoc.exe','list','--path',utoc],b.TOOLS)
    assets=[s for s in listing.splitlines() if '.uasset' in s]
    assert len(assets)==8 and all(sum(a['name']+'.uasset' in s for s in assets)==1 for a in staged)
    inp=WORK/'readback-input';inp.mkdir(exist_ok=True)
    for ext in ['.utoc','.ucas']:
        p=(game_root()/'ProjectPBZ/Content/Paks')/('global'+ext)
        shutil.copyfile(p,inp/p.name)
    files=sorted((WORK/'container').glob('*'));assert len(files)==3
    for p in files:shutil.copyfile(p,inp/p.name)
    b.run('unpack',[b.TOOLS/'retoc.exe','to-legacy','--version','UE5_6','--no-shaders','--no-parallel',inp,WORK/'readback'],b.TOOLS)
    report={'status':'human-reviewed-voice-built-awaiting-independent-verification-and-runtime',
            'variant':'reviewed-natural-voice-v4','build_id':'26367565',
            'target_events':old['target_events'],'event_count':27,'languages':list(lib.LANGS),
            'replacements':selections,'language_counts':old['language_counts'],
            'assets':staged,'bank_evidence':bank_evidence,'encoding_evidence':encoding,
            'review_mapping':changes,'reviewed_issue_count':12,'fresh_encoding_count':3,
            'review_snapshot_sha256':sha_file(EVIDENCE/'snapshot.json'),
            'previous_report_sha256':sha_file(OLD/'report.json'),
            'container_files':[{'path':str(p.relative_to(ROOT)),'name':p.name,'bytes':p.stat().st_size,'sha256':sha_file(p)} for p in files],
            'synthetic_audio':False,'duration_target_truncation':False,'language_settings_changed':False,
            'runtime_tested':False,'installed':False,'selected_changes_human_reviewed':True,
            'scope_limit':old['scope_limit'],'local_only_reason':old['local_only_reason']}
    write(WORK/'report.json',report)
    print(json.dumps({'variant':report['variant'],'changed_media':len(changes),'codecs':len(encoding),'files':report['container_files']},indent=2))


if __name__=='__main__':main()
