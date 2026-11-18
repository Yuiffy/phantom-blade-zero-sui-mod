"""Record the current JK constraints without pretending a solver fix was made."""
from common import *
import numpy as np
from package_candidate import parse, unpack

def main():
    source=JK/'cloth-details.json';d=read(source)
    assets=d['assets'];a=next(a for a in assets if a['name'].startswith('CA_Sui_Skirt'))
    detail=read(JK/'independent/cloth-native-details.json')
    section=next(s for s in detail['sections'] if s['slot']=='MI_JK_PleatedSkirt')
    assert assets[section['cloth_index']]['name']==a['name']
    doc=read(ROOT/'native/source.json')
    _,_,_,current=parse(doc)
    assert current['sections'][section['material']]['cloth_maps']==section['cloth_maps']
    distances=next(m['values'] for m in a['maps'] if m['name']=='MaxDistance')
    mapping=np.array(section['cloth_maps'][0]['source']);alpha=1-mapping[:,3]/65535
    assert len(distances)==288 and max(distances)<.65
    config=a['config'];positions=np.array(a['positions'])
    write(ROOT/'skirt-diagnosis.json',dict(status='diagnosed-left-unchanged-as-user-allows',
        source_cloth_details_sha256=sha(source),native_source_sha256=sha(ROOT/'native/source.json'),verified_against_current_native_mapping=True,
        physical_particles=len(distances),pinned_particles=int(np.count_nonzero(np.array(distances)==0)),
        max_distance_cm=float(max(distances)),cage_bounds_cm=[positions.min(0).tolist(),positions.max(0).tolist()],
        gravity_scale=config['gravityScale'],bending_stiffness=config['bendingStiffnessWeighted'],render_blend_range=[float(alpha.min()),float(alpha.max())],
        existing_collision_asset=a['physics_asset'],
        interpretation='The small permitted particle travel limits collision avoidance. This supports a limitation diagnosis, not a unique proven cause of gameplay clipping.',
        jirai_lessons=['Use a separate skirt collision envelope without changing gameplay/ragdoll physics.','Evaluate updated particle travel and pinning together with collisions.','Consume TeleportAndReset before continuous walk/jog/crouch cycles.','Check rendered GPU-mapped surfaces, rest silhouette and recovery rather than cage motion alone.','Do not copy the Jirai visible blend cap without checking the different JK skirt and leg skinning.'],
        changes_to_skirt=False,new_cloth_simulation_performed=False,game_runtime_tested=False))
    print('JK_SKIRT_LIMITS_RECORDED',max(distances))

if __name__=='__main__':main()
