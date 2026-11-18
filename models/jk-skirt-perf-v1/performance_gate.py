"""Measure matching frames only; never present offline milliseconds as game FPS."""
from common import *
import numpy as np

def summarize(rows):
    return {k:dict(median_ms=float(np.median([r[k] for r in rows])),
                   p95_ms=float(np.percentile([r[k] for r in rows],95)),
                   mean_ms=float(np.mean([r[k] for r in rows])))
            for k in ['solve_ms','prepare_ms','readback_ms','bones_ms']}

def check():
    stage=read(W/'chosen-stage.json')['stage']
    original_path=W/'cost32x8/jog-60.json'
    candidate_path=W/stage/'jog-60.json'
    original=read(original_path);candidate=read(candidate_path)
    # Initial warmup is excluded in the C++ timer. Compare identical first 181 ticks.
    before=original['timings'];after=[r for r in candidate['timings'] if r['step']<=240]
    assert len(before)==len(after)==181
    assert [r['step'] for r in before]==[r['step'] for r in after]
    a,b=summarize(before),summarize(after)
    ratios={key:b['solve_ms'][key]/a['solve_ms'][key] for key in ['median_ms','p95_ms']}
    assert max(ratios.values())<=.25,ratios
    assert all(set(a['asset_index'] for a in f['assets'])==set(range(5))
               for f in candidate['frames'])
    settings=read(W/stage/'selection.json')
    assert settings['iterations']<=12 and settings['substeps']<=3
    report=dict(passed=True,basis='Matched 60 Hz synthetic jog, synchronous single-thread UE editor solve; not game frame time or FPS. Original A/B/A checked local repeatability; candidate is a later full quality run.',
                original=a,candidate=b,solve_cost_ratios=ratios,
                source_sha256={str(original_path):sha(original_path),str(candidate_path):sha(candidate_path)},
                original_solver=[32,8],candidate_solver=[settings['iterations'],settings['substeps']],
                original_skirt_particles=288,candidate_skirt_particles=64,
                game_runtime_tested=False)
    write(W/'performance-verification.json',report)
    print('JK_PERFORMANCE_GATE_PASSED',ratios,flush=True)
    return report

if __name__=='__main__':check()
