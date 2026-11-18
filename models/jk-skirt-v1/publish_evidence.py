"""Export numeric/hash evidence only, after independently verified installation."""
from common import *


def publish():
    receipt = read(W / 'installation-receipt.json')
    assert receipt['status'] == 'installed-independent-readback-verified-runtime-pending'
    assert snapshot() == receipt['after']
    out = REPO / 'evidence/jk-skirt-v1'
    out.mkdir(parents=True, exist_ok=True)
    evaluation = read(W / 'delivery/evaluation.json')
    gates = read(W / 'delivery-gates.json')
    installed = read(W / 'installed-verification.json')
    assert evaluation['passed'] and gates['passed'] and installed['passed']
    write(out / 'verification.json', dict(
        installed_at=receipt['installed_at'], status=receipt['status'],
        game_runtime_tested=False, installed_verification=installed,
        cloth_readback=read(W / 'installed-cloth-readback.json'),
        static_mapping=read(W / 'static-mapping-verification.json'),
        continuous_surface=evaluation,
        running_comparisons=gates['running_comparisons'],
        retained_previous_files=len(receipt['before']),
        installed_files=len(receipt['after']),
        known_limitations=[
            'Synthetic motion, not extracted game animations; runtime and performance pending.',
            'Residual running intersections remain; deep crouch is not fixed.',
            'Crouch 30 Hz visible crossing sum increases from 303 to 352.',
            'The solver is shared by all five JK cloth assets (1745 particles).',
        ],
    ))
    write(out / 'installation.json', dict(
        status=receipt['status'], installed_at=receipt['installed_at'],
        added=receipt['added'], before=receipt['before'], after=receipt['after'],
        retained_other_chat_face=receipt['retained_other_chat_face'],
        game_runtime_tested=False,
    ))
    summaries = {}
    for stage in ['baseline', 'delivery']:
        summaries[stage] = [
            {k: v for k, v in row.items() if k != 'samples'}
            for row in read(W / stage / 'contacts.json')['records']
        ]
    write(out / 'sampled-contacts.json', dict(
        basis='Sampled visible edge crossings; not exposed area or actual game animation.',
        stages=summaries,
    ))
    # Relativize the evidence index; the referenced private inputs remain local.
    hashes = {Path(p).relative_to(REPO).as_posix(): h
              for p, h in gates['evidence_hashes'].items()}
    for name in ['delivery-gates.json', 'installation-receipt.json',
                 'installed-verification.json', 'installed-cloth-readback.json']:
        hashes['private/jk-skirt-v1/' + name] = sha(W / name)
    write(out / 'evidence-hashes.json', hashes)
    print('JK_SKIRT_PUBLIC_NUMERIC_EVIDENCE_READY')


if __name__ == '__main__':
    publish()
