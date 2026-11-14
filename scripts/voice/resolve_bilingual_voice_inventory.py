"""JSON helpers used by the reviewed-voice pipeline."""
import json

def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))


def write(p,d):
    p.parent.mkdir(exist_ok=True,parents=True)
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
