"""Publish only numeric/hash summaries after installed independent readback."""
from common import *

def publish():
    receipt=read(W/'installation-receipt.json')
    assert receipt['status']=='installed-independent-readback-verified-runtime-pending'
    assert snapshot()==receipt['after']
    stage=read(W/'chosen-stage.json')['stage']
    report=read(W/'installed-verification.json');assert report['passed']
    out=REPO/'evidence/jk-skirt-perf-v1';out.mkdir(parents=True,exist_ok=True)
    write(out/'performance.json',read(W/'performance-verification.json'))
    write(out/'matched-original-costs.json',read(W/'cost-comparison.json'))
    write(out/'verification.json',dict(
        installed_at=receipt['installed_at'],status=receipt['status'],
        installed=report,cloth=read(W/'installed-cloth-readback.json'),
        continuous_surface=read(W/stage/'evaluation.json'),
        static_mapping=read(W/'static-mapping-verification.json'),
        game_runtime_tested=False,
        limitations=['Synthetic animations and single-thread editor timings; no game FPS guarantee.',
                     'Residual clipping remains; deep crouch and performance require game feedback.',
                     'Five cloth assets still share the 12/3 solver; four individual configs preserved.']))
    write(out/'installation.json',{k:receipt[k] for k in
          ['status','installed_at','added','before','after','retained_other_chat_face','game_runtime_tested']})
    old=REPO/'private/jk-skirt-v1'
    contacts={}
    for name,path in [('before-skirt',old/'baseline/contacts.json'),
                      ('expensive-v1',old/'delivery/contacts.json'),
                      ('optimized',W/stage/'contacts.json')]:
        contacts[name]=[{k:v for k,v in row.items() if k!='samples'} for row in read(path)['records']]
    write(out/'sampled-contacts.json',dict(basis='Visible sampled edge intersections, not exposed area or game animation.',stages=contacts))
    gates=read(W/'delivery-gates.json')
    hashes={Path(p).relative_to(REPO).as_posix():h for p,h in gates['evidence_hashes'].items()}
    for name in ['performance-verification.json','delivery-gates.json','installation-receipt.json',
                 'installed-verification.json','installed-cloth-readback.json']:
        hashes['private/jk-skirt-perf-v1/'+name]=sha(W/name)
    write(out/'evidence-hashes.json',hashes)
    print('JK_PERF_PUBLIC_EVIDENCE_READY')

if __name__=='__main__':publish()
