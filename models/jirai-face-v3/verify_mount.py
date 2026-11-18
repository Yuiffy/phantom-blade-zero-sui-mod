from common import *
from package_candidate import PACKAGES,inspect_mount

def check(installed=False):
    gate=read(ROOT/'verification.json');assert gate['passed']
    assert read(ROOT/'geometry-verification.json')['passed']
    assert read(ROOT/'surface-verification.json')['passed']
    expected={p:read(ROOT/'independent/json'/(relative_package(p)+'.json')) for p in PACKAGES}
    if not installed:
        baseline=read(ROOT/'baseline.json')['installed']
        assert {r['name']:r['sha256'] for r in baseline}=={p.name:sha(p) for p in MODS.iterdir() if p.is_file()}
        for label,dirs in [('patch-last',[MODS,ROOT/'container']),('patch-first',[ROOT/'container',MODS])]:
            assert inspect_mount(label,dirs)==expected,'Mount priority changes with directory order'
    else:
        assert inspect_mount('installed',[MODS])==expected,'Installed package resolution differs'
    old=inspect_mount('original-atlas-installed' if installed else 'original-atlas-preflight',[MODS],[OLD_ATLAS])
    assert old[OLD_ATLAS]==read(BASE/'independent/json'/(relative_package(OLD_ATLAS)+'.json'))
    snapshot=[dict(name=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(MODS.iterdir()) if p.is_file()]
    write(ROOT/('installed-mount-verification.json' if installed else 'mount-verification.json'),dict(passed=True,
        installed=installed,directory_order_independent=not installed,patch_priority='Numeric _2_P suffix, independently mounted',
        source_atlas_sha256=gate['source_atlas_sha256'],source_iris_sha256=gate['source_iris_sha256'],surface_sha256=gate['surface_sha256'],
        original_shared_atlas_exact=True,installed_mod_snapshot=snapshot,game_runtime_tested=False))
    print('FACE3_MOUNT_VERIFIED','installed' if installed else 'preflight')

if __name__=='__main__':check(sys.argv[1:]==['installed'])
