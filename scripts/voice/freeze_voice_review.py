"""Freeze the supported, fully resolved round-two review without editing originals."""
from datetime import datetime, timezone
import shutil
from paths import ROOT
from resolve_bilingual_voice_inventory import read, write
from verify_library_voice_variant import sha_file


def main():
    source=ROOT/'voice-review-round2'
    review=read(source/'reviews/user-review.json')
    manifest=read(source/'manifest.json')
    digest=sha_file(source/'manifest.json')
    if review.get('manifest_sha256')!=digest:
        raise ValueError('Review manifest mismatch')
    issues={i['id']:i for i in manifest['issues']}
    if review.get('media'):
        raise ValueError('This v4 builder does not apply per-media overrides; resolve explicitly first')
    if len(issues)!=12 or set(issues)!=set(review['issues']):
        raise ValueError('Expected all 12 resolved v4 issue choices')
    for key,row in review['issues'].items():
        if row.get('choice') not in issues[key]['suggestions']:
            raise ValueError(f'Unresolved or unsupported choice: {key}')
    evidence=ROOT/'variants/reviewed-natural-voice-v4/review-evidence'
    evidence.mkdir(parents=True,exist_ok=True)
    for p in [source/'manifest.json',source/'reviews/user-review.json']:
        dest=evidence/p.name
        if dest.exists():
            if sha_file(dest)!=sha_file(p):
                raise ValueError('Frozen input differs; create a new variant instead of overwriting it')
        else:
            shutil.copyfile(p,dest)
    snapshot=evidence/'snapshot.json'
    content={'created_at':datetime.now(timezone.utc).isoformat(),
             'review_sha256':sha_file(evidence/'user-review.json'),
             'manifest_sha256':digest,
             'choices':{k:v['choice'] for k,v in review['issues'].items()}}
    if snapshot.exists():
        prior=read(snapshot)
        if any(prior.get(k)!=content[k] for k in ['review_sha256','manifest_sha256','choices']):
            raise ValueError('Frozen snapshot differs')
    else:write(snapshot,content)
    print('Review frozen; no game files changed. Installation needs a separate --apply.')


if __name__=='__main__':main()
