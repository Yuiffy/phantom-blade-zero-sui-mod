"""Read-only game-data comparison and second-round natural-audio audition.

Decodes already extracted WEMs and bounded local buttons, one process at a time
at below-normal priority. Never loads a voice model, packages or installs a MOD.
"""
import array
import hashlib
import json
import math
import os
import shutil
import subprocess
import wave
from pathlib import Path

from paths import ROOT
OUT = ROOT / 'voice-review-round2'
WORK = ROOT / 'variants/library-natural-voice-v3'
FLAGS = subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS
ENV = dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', MKL_NUM_THREADS='1')


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def info(p):
    with wave.open(str(p), 'rb') as f:
        channels, width, rate, samples = f.getnchannels(), f.getsampwidth(), f.getframerate(), f.getnframes()
        assert width == 2
        values = array.array('h', f.readframes(samples))
    rms = math.sqrt(sum(v * v for v in values) / max(1, len(values))) / 32768
    return {'seconds': samples / rate, 'samples': samples, 'rate': rate, 'channels': channels,
            'rms_dbfs': round(20 * math.log10(max(1e-9, rms)), 2), 'sha256': sha(p)}


def run(args):
    p = subprocess.run([str(v) for v in args], capture_output=True, env=ENV,
                       creationflags=FLAGS, timeout=30)
    assert p.returncode == 0, p.stderr.decode('utf-8', errors='replace')[:500]


def copy_audio(path, name):
    target = OUT / 'audio' / name
    if not target.exists() or sha(path) != sha(target):
        shutil.copyfile(path, target)
    return {'url': 'audio/' + name, **info(target)}


def audition(path, key):
    """Remove only outer silence; preserve all internal audio and pauses.

    Source is retained for comparison. This is never fitted to a target length.
    """
    context = copy_audio(path, key + '.context.wav')
    with wave.open(str(path), 'rb') as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (1, 2, 48000)
        pcm = f.readframes(f.getnframes())
    values = array.array('h', pcm)
    frame = 480
    levels = [math.sqrt(sum(v * v for v in values[i:i + frame]) / len(values[i:i + frame])) / 32768
              for i in range(0, len(values), frame)]
    threshold = max(10 ** (-50 / 20), max(levels) * 10 ** (-35 / 20))
    active = [i for i, level in enumerate(levels) if level > threshold]
    assert active, path
    lo = max(0, active[0] * frame - 1920)
    hi = min(len(values), (active[-1] + 1) * frame + 2880)
    target = OUT / 'audio' / (key + '.audition.wav')
    with wave.open(str(target), 'wb') as f:
        f.setparams((1, 2, 48000, 0, 'NONE', 'not compressed'))
        f.writeframes(pcm[lo * 2:hi * 2])
    with wave.open(str(target), 'rb') as f:
        assert f.readframes(f.getnframes()) == pcm[lo * 2:hi * 2]
    return {'url': 'audio/' + target.name, 'context_url': context['url'],
            'source_range_samples': [lo, hi], 'source_range_seconds': [lo / 48000, hi / 48000],
            'outer_silence_only': True, 'target_duration_fit': False, **info(target)}


def event_label(name):
    suffix = name.split('_Hun_', 1)[-1]
    labels = {
        'Attack_Short': '短促攻击', 'BiQi_01_DuanCu': '短促憋气 / 使劲', 'BiQi_02_Long': '较长憋气 / 使劲',
        'Break': '破招', 'Charge_SuperLong': '长蓄力', 'ChuZhao_01_DuanCu': '短促出招', 'ChuZhao_02': '出招',
        'Hurt': '受击', 'Hurt_BiXian': '受击变体 BiXian', 'Hurt_Heavy': '重受击', 'Hurt_Heavy_Mix': '重受击混合',
        'ShouZhao_DoubleBlade': '双刀收招 · 含空中攻击', 'ShouZhao_LongBlade': '长刀收招 · 含空中攻击',
        'ShouZhao_TangBlade': '唐刀收招 · 含空中攻击', 'Snort': '哼声', 'ZhongZhuan': '动作中转',
        'ZhongZhuan_01': '动作中转共享变体', 'Charge_Heavy_Long': '重击长蓄力', 'Charge_Heavy_Short': '重击短蓄力',
        'Charge_Long': '长蓄力', 'Charge_Short': '短蓄力', 'Charge_Release_Heavy': '蓄力重击释放',
        'Charge_Release_Light': '蓄力轻击释放', 'Cough': '咳嗽', 'Execute_Attack_Heavy': '处决重击',
        'Heavy_Release': '重击释放', 'Special_Stifle': '特殊闷哼', 'Weapon_Break': '武器破招'}
    return labels.get(suffix, suffix)


def main():
    for folder in ['audio', 'evidence', 'reviews']:
        (OUT / folder).mkdir(parents=True, exist_ok=True)
    feedback_path = ROOT / 'voice-review-v3/reviews/user-review.json'
    snapshot_path = OUT / 'evidence/round1-user-review.json'
    if not snapshot_path.exists():
        shutil.copyfile(feedback_path, snapshot_path)
    feedback = read(snapshot_path)
    report = read(WORK / 'report.json')
    assert feedback['report_sha256'] == sha(WORK / 'report.json')
    prior = read(ROOT / 'voice-review-v3/manifest.json')
    prior_rows = {r['id']: r for r in prior['rows']}
    issues = {k: v for k, v in feedback['reviews'].items() if v.get('status') not in [None, 'good']}
    assert len(issues) == 12
    originals = {}
    inventory = read(WORK / 'bilingual-inventory.json')
    for event in inventory['events']:
        for ref in event['references']:
            if ref['kind'] == 'Media':
                key = (ref['language'], ref['id'])
                assert key not in originals or originals[key]['sha256'] == ref['sha256']
                originals[key] = ref

    # Current 30 clips are copied byte-identically from the first review.
    current = {}
    for row in prior['rows']:
        key = row['id']
        audio = copy_audio(ROOT / 'voice-review-v3' / row['decoded_url'], 'current-' + key + '.wav')
        assert audio['sha256'] == row['decoded_sha256']
        current[key] = {**row, **audio, 'round1': feedback['reviews'].get(key, {})}

    # Reuse only whole recordings or complete existing segments. No new tiny
    # energy islands, no duration-fitting truncation, normalization or synthesis.
    natural = read(ROOT / 'audio/natural-segments/manifest.json')
    natural_parents = {r['id']: r for r in natural['parents']}
    candidates = {}
    for number in [21, 22, 23, 25, 26, 27, 28, 29, 30, 14, 15]:
        row = next(r for r in prior['rows'] if r['number'] == number)
        key = 'reuse-' + str(number)
        candidates[key] = {'id': key, 'title': row['title'], 'label': f'原 #{number:02d} · 完整片段 {row["segment"]}',
                           'kind': 'user-approved' if row['id'] in feedback['reviews'] and feedback['reviews'][row['id']].get('status') == 'good' else 'existing-unrejected',
                           'prior_number': number, **copy_audio(ROOT / 'voice-review-v3' / row['decoded_url'], key + '.wav')}
    old_voices = {v['id']: v for v in read(ROOT / 'audio/voice-manifest.json')['voices']}
    new_sources = [
        ('new-ah', old_voices['hurt_real_05'], '啊！ · 完整按钮'),
        ('new-husky', old_voices['hurt_heavy_real_01'], '啊！（沙哑） · 完整按钮'),
        ('new-effort', old_voices['attack_effort_real_04'], '嗯呃！ · 完整按钮'),
        ('new-groan', natural_parents['effort_groan_real_06'], '呃~ · 完整按钮'),
        ('new-effort-sequence', old_voices['attack_effort_real_05'], '呃嗯嗯嗯呃呃呃嗯呃（攻击） · 完整按钮'),
        ('new-cough', old_voices['cough_context_real_03'], '呵咳~（开心） · 完整按钮'),
    ]
    for key, v, label in new_sources:
        p = ROOT / v['output']
        assert sha(p) == v['quality']['sha256']
        candidates[key] = {'id': key, 'title': v['text_label'], 'label': label, 'kind': 'new-audition',
                           'source_sha256': v['source_sha256'], 'source_file': Path(v['source']).name,
                           'processing': 'Existing normalized PCM; only outer silence removed. Internal audio/pause samples remain byte-identical; no new gain or time changes.',
                           **audition(p, key)}
    buttons = Path(os.environ['SUI_BUTTON_ROOT']).resolve()
    cat = read(buttons / 'src/voices.json')
    by_path = {v['path']: v for c in cat['voices'] for v in c['voiceList']}
    for key, name in [('new-zap-aha', '啊哈（被水母电）.MP3'), ('new-zap-ah', '啊，啊（被水母电）.MP3')]:
        src = buttons / 'public/voices' / name
        assert src.stat().st_size < 2 * 1024 * 1024 and name in by_path
        target = OUT / 'audio' / (key + '.wav')
        if not target.exists():
            run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-threads', '1', '-filter_threads', '1',
                 '-i', src, '-vn', '-ac', '1', '-ar', '48000', '-c:a', 'pcm_s16le', target])
        candidates[key] = {'id': key, 'title': by_path[name]['description']['zh-CN'], 'label': '新找 · 完整按钮',
                           'kind': 'new-audition', 'source_file': name, 'source_sha256': sha(src),
                           'processing': 'Complete button decoded to mono PCM48; only outer silence removed; no added gain or duration-fitting cuts.',
                           **audition(target, key)}

    default_attack = ['reuse-23', 'reuse-14', 'new-effort', 'new-zap-aha']
    default_effort = ['reuse-21', 'reuse-22', 'reuse-23', 'new-groan', 'new-effort', 'new-effort-sequence']
    default_hurt = ['reuse-28', 'reuse-29', 'new-ah', 'new-husky', 'new-zap-ah']
    default_cough = ['reuse-15', 'new-cough', 'reuse-21', 'new-groan']
    issue_rows = []
    for key, review in sorted(issues.items(), key=lambda kv: kv[1]['number']):
        row = current[key]
        suggestions = default_cough if review['number'] in [16, 17, 18, 19, 20] else (default_effort + ['reuse-28', 'new-husky', 'new-ah', 'new-zap-ah'] if review['number'] == 24 else default_attack)
        if review['number'] == 7:
            suggestions = ['reuse-14', 'new-husky', 'new-effort', 'new-zap-aha']
        issue_rows.append({'id': f'issue-{review["number"]:02d}', 'old_id': key, 'old_number': review['number'],
                           'title': row['title'], 'feedback': review, 'current_url': row['url'],
                           'suggestions': suggestions, 'language_uses': row['language_uses'],
                           'mixed_contexts': review['number'] == 24})

    media = []
    for index, replacement in enumerate(report['replacements']):
        lang, ident = replacement['language'], replacement['media_id']
        ref = originals[(lang, ident)]
        assert ref['sha256'] == replacement['original_sha256']
        src = ROOT / ref['path']
        assert sha(src) == ref['sha256']
        tag = 'cn' if lang == 'Chinese' else 'en'
        output = OUT / 'audio' / f'original-{tag}-{ident}.wav'
        if not output.exists():
            run([ROOT / 'research/vgmstream/vgmstream-cli.exe', '-i', '-o', output, src])
        audio = info(output)
        assert audio['samples'] == ref['description']['decoded_samples']
        assert audio['rate'] == ref['description']['sample_rate']
        assert audio['channels'] == ref['description']['channels']
        old = replacement['candidate']
        first_event = replacement['events'][0]
        suggestion_ids = default_hurt if 'Hurt' in first_event else (default_cough if 'Cough' in first_event else (default_effort if any(s in first_event for s in ['BiQi', 'Charge_', 'Stifle']) else default_attack))
        old_issue = next((r for r in issue_rows if r['old_id'] == old), None)
        media.append({'id': f'{tag}-{ident}', 'language': lang, 'media_id': ident,
                      'original_url': 'audio/' + output.name, 'original_wem_sha256': ref['sha256'],
                      'original_source_name': ref['source_name'], 'original_pcm': audio,
                      'original_seconds': replacement['original_seconds'], 'v3_cap_seconds': replacement['cap_seconds'],
                      'current_id': old, 'current_number': prior_rows[old]['number'], 'current_url': current[old]['url'],
                      'current_title': prior_rows[old]['title'], 'current_seconds': prior_rows[old]['seconds'],
                      'issue_id': old_issue['id'] if old_issue else None,
                      'events': replacement['events'], 'suggestions': suggestion_ids if old_issue else []})
        if (index + 1) % 75 == 0:
            print(f'ORIGINALS_DECODED {index + 1}/{len(report["replacements"])}', flush=True)

    air = read(ROOT / 'research/voice-jump-diagnosis/all-weapons-air-routes.json')
    events = []
    by_name = {e['event']: e for e in inventory['events']}
    for name in sorted({e for m in media for e in m['events']}):
        links = [{'ability': r['ability'].rsplit('/', 1)[-1], 'start_seconds': link['start_seconds']}
                 for r in air['abilities'] for link in r['voice_links'] if link['event'] == name]
        events.append({'id': name, 'title': event_label(name),
                       'selected_target': name in report['target_events'],
                       'event_id': by_name[name]['event_id'], 'event_duration': by_name[name]['duration'],
                       'air_routes': links,
                       'meaning_basis': 'Static event-name interpretation; only the listed airborne timelines have direct action evidence.'})
    for issue in issue_rows:
        related = [m for m in media if m['issue_id'] == issue['id']]
        issue['media_ids'] = [m['id'] for m in related]
        issue['events'] = sorted({e for m in related for e in m['events']})
        issue['duration_fit'] = {cid: {'under_v3_cap': sum(candidates[cid]['seconds'] <= m['v3_cap_seconds'] + 1 / 48000 for m in related),
                                      'total': len(related)} for cid in issue['suggestions']}
    assert len(media) == 474 and len(events) == 28 and len(issue_rows) == 12
    assert all(i['media_ids'] and i['suggestions'] for i in issue_rows)
    data = {'schema': 1, 'id': 'voice-audition-round2', 'game_build': report['build_id'],
            'source_report_sha256': sha(WORK / 'report.json'), 'feedback_snapshot_sha256': sha(snapshot_path),
            'round1_feedback_preserved': True, 'installed_variant_unchanged': True,
            'new_audio_is_audition_not_game_encoded': True,
            'candidate_selection_note': '8 whole-button natural auditions plus existing complete segments; labels and prior feedback are search evidence, not independent listening approval.',
            'issues': issue_rows, 'candidates': list(candidates.values()), 'current': list(current.values()),
            'media': media, 'events': events,
            'limits': 'Original files are dry source WEMs, without game mixing/effects. All listed original Chinese/English pool members are included; other game VO is outside this comparison.'}
    write(OUT / 'manifest.json', data)
    write(OUT / 'evidence/build-summary.json', {'issues': len(issue_rows), 'new_auditions': sum(c['kind'] == 'new-audition' for c in candidates.values()),
          'comparison_candidates': len(candidates), 'original_cn': sum(m['language'] == 'Chinese' for m in media),
          'original_en': sum(m['language'] == 'English(US)' for m in media), 'events': len(events),
          'feedback_snapshot_sha256': sha(snapshot_path), 'game_files_written': False,
          'synthesis': False, 'new_asr': False, 'source_separation': False, 'screen_capture': False})
    print(json.dumps(read(OUT / 'evidence/build-summary.json'), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
