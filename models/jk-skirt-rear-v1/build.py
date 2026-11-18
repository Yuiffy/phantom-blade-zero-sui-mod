"""Reweight only the two render blend buffers of the installed performance skirt."""
import shutil
import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE.parent / "jk-skirt-perf-v1"))
import common
import compose
import package_verify
from native import DT, decode, unpack
import numpy as np

PREVIOUS = common.W
WORK = PREVIOUS.parent / "jk-skirt-rear-v1" / "side-blend"
STAGE = common.read(PREVIOUS / "chosen-stage.json")["stage"]
NAME = "zzzzzzzzzzz_Sui_JKSkirtRear1_12_P"
REL = common.relative_package(common.BODY)
common.W = compose.W = package_verify.W = WORK
read, write, sha = common.read, common.write, common.sha


def render_weights(document):
    positions, _, _, detail = decode(document)
    skirt = detail["sections"][14]
    assert skirt["cloth_index"] == 2 and skirt["material"] == 14
    lo = skirt["base_vertex"]
    y = positions[lo:lo + skirt["vertices"], 1]
    previous = np.array(skirt["cloth_maps"][0]["source"])[:, 3]
    # Front faces +Y in the native mesh. Protect the rear half including the side pleats.
    transition = np.clip((y + 5.0) / 12.0, 0, 1)
    transition = transition ** 2 * (3 - 2 * transition)
    # Cap front travel as well, so a strong upward impulse cannot raise the front
    # corner by the full displacement seen on the first rear-only candidate.
    x = np.abs(positions[lo:lo + skirt["vertices"], 0])
    side = np.clip((x - 15) / 9, 0, 1)
    cap = .65 - .47 * side**2 * (3 - 2*side)
    dynamic = np.minimum(1 - previous / 65535, cap) * transition
    updated = np.rint(65535 * (1 - dynamic)).astype("<u2")
    assert np.all(updated[y <= -5] == 65535) and dynamic.max() <= .65
    starts = [skirt["cloth_map_spans"][0]["offset"], detail["gpu_cloth_mapping_span"]["offset"] + 64 * skirt["gpu_mapping_offset"]]
    return updated, starts, dict(vertices=len(y), rear_fixed=int(sum(y <= -5)), transition=int(sum((y > -5) & (y < 7))), front_dynamic=int(sum(y >= 7)), front_center_cap=.65, outer_corner_cap=.18)


def build():
    before = common.snapshot()
    receipt = read(PREVIOUS / "installation-receipt.json")
    assert all(row in before for row in receipt["added"])
    write(WORK / "before.json", before)
    source = compose.extract("before", [common.MODS]) / (REL + ".uasset")
    payload = source.with_suffix(".uexp").read_bytes()
    assert sha(source.with_suffix(".uexp")) == sha(PREVIOUS / "legacy" / (REL + ".uexp")), "Effective JK body changed since the performance version"
    document = compose.tojson("before", source)
    original = unpack(document)
    assert payload.count(original) == 1
    updated, starts, report = render_weights(document)
    raw = bytearray(original)
    for start in starts:
        records = np.frombuffer(raw, dtype=DT, count=len(updated), offset=start)
        records["source"][:, 3] = updated
    dest = WORK / "legacy" / (REL + ".uasset")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    dest.with_suffix(".uexp").write_bytes(payload.replace(original, raw, 1))
    container = WORK / "container"
    container.mkdir(exist_ok=True)
    utoc = container / (NAME + ".utoc")
    retoc = common.diag.TOOLS / "retoc.exe"
    common.run("pack", [retoc, "to-zen", "--version", "UE5_6", "--no-parallel", WORK / "legacy", utoc])
    listing = common.run("list", [retoc, "list", "--path", utoc])
    packages = [line.split()[-1].replace(chr(92), "/").removeprefix("../../../") for line in listing.splitlines() if line.strip().endswith(".uasset")]
    assert packages == [REL + ".uasset"]
    files = [dict(name=p.name, bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(container.iterdir())]
    assert len(files) == 3 and {r["name"] for r in files} == {NAME + e for e in [".pak", ".ucas", ".utoc"]}
    write(WORK / "build.json", dict(blend=report, files=files, before_payload=sha(source.with_suffix(".uexp")), after_payload=sha(dest.with_suffix(".uexp"))))
    verify("final", [common.MODS, container])


def verify(label, dirs):
    report = read(WORK / "build.json")
    resolved = compose.extract(label, dirs)
    asset = resolved / (REL + ".uasset")
    assert sha(asset.with_suffix(".uexp")) == report["after_payload"]
    original = read(WORK / "native/before.json")
    current = compose.tojson(label, asset)
    updated, starts, _ = render_weights(original)
    raw = unpack(current)
    expected = bytearray(unpack(original))
    for start in starts:
        records = np.frombuffer(expected, dtype=DT, count=len(updated), offset=start)
        records["source"][:, 3] = updated
    assert raw == expected
    assert np.array_equal(np.array(decode(current)[3]["sections"][14]["cloth_maps"][0]["source"])[:, 3], updated)
    independent = package_verify.cue(label, dirs)
    for package, data in independent.items():
        reference = PREVIOUS / "independent/installed" / (common.relative_package(package) + ".json")
        assert data == read(reference), package
    before = WORK / "before-legacy"
    count = 0
    for path in before.rglob("*.uexp"):
        rel = path.relative_to(before)
        if rel.as_posix() != REL + ".uexp":
            assert sha(path) == sha(resolved / rel), rel
            count += 1
    assert count >= 133
    write(WORK / (label + "-verification.json"), dict(passed=True, retained_payloads=count, only_skirt_blend_changed=True, native_sha256=sha(WORK / "native" / (label + ".json")), files=report["files"]))
    print(label, report["blend"], count, flush=True)


if __name__ == "__main__":
    build()
