"""Prepare an isolated R8 author project and run bounded, single-thread measurements."""
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

code = Path(__file__).resolve().parent
repo = code.parents[1]
root = repo / 'private/jirai-perf-v1'
project = root / 'ue/ProjectPBZ'
author = repo / 'private/jirai-skirt-shape-v1/variant/ue/ProjectPBZ'
helper = repo / 'private/jk-skirt-perf-v1/variant/ue/ProjectPBZ/Plugins/PBZModTools'
editor = Path('F:/FTools/UE57/UE_5.7/Engine/Binaries/Win64/UnrealEditor-Cmd.exe')


def prepare():
    uproject = project / 'ProjectPBZ.uproject'
    if not uproject.exists():
        project.mkdir(parents=True, exist_ok=True)
        for name in ['Config', 'Content', 'Plugins/HuaShira']:
            shutil.copytree(author / name, project / name, dirs_exist_ok=True)
        shutil.copytree(helper, project / 'Plugins/PBZModTools', dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns('Intermediate', 'Saved'))
        shutil.copy2(author / uproject.name, uproject)
    return uproject


def run(jobs):
    uproject = prepare()
    env = dict(os.environ, JIRAI_TEST_JOBS=json.dumps(jobs), RAYON_NUM_THREADS='1',
               DOTNET_PROCESSOR_COUNT='2', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='2')
    env.pop('PBZ_SKIRT_ONLY', None)
    args = [editor, uproject, '-unattended', '-nop4', '-stdout', '-onethread', '-NullRHI',
            '-NoShaderCompile', '-NoShaderWorker', '-run=pythonscript', f'-script={code / "measure_ue.py"}']
    log = root / ('measure-' + jobs[0]['label'] + '.log')
    with log.open('wb') as stream:
        subprocess.run(args, env=env, stdout=stream, stderr=subprocess.STDOUT, check=True,
                       creationflags=subprocess.CREATE_NO_WINDOW | subprocess.BELOW_NORMAL_PRIORITY_CLASS)
    output = log.read_text(errors='replace')
    assert all('JIRAI_PERF_DONE ' + j['label'] in output for j in jobs)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['benchmark', 'quality'])
    parser.add_argument('settings', nargs='+', help='iterations x substeps, e.g. 8x3')
    args = parser.parse_args()
    jobs = []
    for index, value in enumerate(args.settings):
        solver = list(map(int, value.split('x')))
        motions = [('jog-recover', 60)] if args.mode == 'benchmark' else [
            (motion + '-recover', hz) for motion in ['crouch', 'jog', 'walk'] for hz in [30, 60]]
        for profile, hz in motions:
            jobs.append(dict(solver=solver, profile=profile, hz=hz,
                             steps=181 if args.mode == 'benchmark' else 61 + 16*hz,
                             label=f'{args.mode}-{index}-{value}-{profile}-{hz}'))
    run(jobs)
