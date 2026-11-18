import json
import sys
from pathlib import Path

code=Path(__file__).resolve().parent
repo=code.parents[1]
sys.path.insert(0,str(code.parent/'jirai-perf-v1'))
import importlib.util

spec=importlib.util.spec_from_file_location('jirai_measure',code.parent/'jirai-perf-v1/measure.py')
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
sys.path.insert(0,str(code.parent/'jk-skirt-perf-v1'))
import common

prior=common.W
root=prior.parent/'jk-outfit-perf-v2'
base.project=root/'ue/ProjectPBZ'
base.author=prior/'variant/ue/ProjectPBZ'
common.W=root
definitions={'baseline':(True,False,12),'shell':(False,False,12),'bend':(True,True,12),'both':(False,True,12),'repeat':(True,False,12)}
definitions['reduced']=(True,False,12)

def run(labels, full):
    assert all(label=='reduced' for label in labels) or 'reduced' not in labels
    if 'reduced' not in labels:
        base.project=root/'control/ProjectPBZ'
    project=base.prepare()
    jobs=[]
    for label in labels:
        for profile in (['walk','jog','crouch'] if full else ['jog']):
            for hz in ([30,60] if full else [60]):
                jobs.append([label+('-full' if full else ''),*definitions[label],profile,hz,61+16*hz if full else 181])
    result=common.run('trial-'+jobs[0][0],[base.editor,project,'-unattended','-nop4','-stdout','-onethread','-NullRHI','-NoShaderCompile','-NoShaderWorker','-run=pythonscript','-script='+str(code/'trial_ue.py')],dict(JK_PERF_JOBS=json.dumps(jobs),PBZ_SKIRT_ONLY='0'))
    assert 'Success - 0 error' in result
    for label, _, _, _, profile, hz, steps in jobs:
        data=common.read(root/label/f'{profile}-{hz}.json')
        assert [t['step'] for t in data['timings']]==list(range(60,steps))

if __name__=='__main__':
    run(sys.argv[2:] or ['baseline','shell','bend','both','repeat'],sys.argv[1]=='full')
