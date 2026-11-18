"""Replay unchanged solver outputs with the independently extracted render mapping."""
import os
import shutil
from build import CODE, STAGE, WORK, PREVIOUS, read, write, sha, common
import evaluate

stage = WORK / "motion"
stage.mkdir(exist_ok=True)
manifest = read(PREVIOUS / STAGE / "input-manifest.json")
for source in (PREVIOUS / STAGE).glob("*.json"):
    if source.name.split("-")[0] not in {"walk", "jog", "crouch", "cloth"} and source.name not in {"render-settings.json", "selection.json"}:
        continue
    if str(source) in manifest["outputs"]:
        assert sha(source) == manifest["outputs"][str(source)]
    local = stage / source.name
    if not local.exists():
        shutil.copy2(source, local)
    assert sha(local) == sha(source)
shutil.copy2(PREVIOUS / "reference-bones.json", WORK / "reference-bones.json")
evaluate.W = WORK
evaluate.evaluate("motion", WORK / "native/final.json")
assert read(stage / "evaluation.json")["passed"]
blender = "D:/develop/Blender/blender-4.5.14-windows-x64/blender.exe"
common.run("contacts", [blender, "-b", "-t", "2", "--python-exit-code", "1", "-P", CODE.parent / "jk-skirt-perf-v1/contacts_blender.py", "--", stage])
for row in read(stage / "contacts.json")["records"]:
    print(row["file"], row["visible_thigh_sum"], row["visible_lining_sum"], flush=True)
