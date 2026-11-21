"""Apply the Pink Beret skirt UV correction to the verified trial payload."""

import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()

    patch = json.loads(Path(__file__).with_name("pink-uv-patch.json").read_text(encoding="utf-8"))
    payload = bytearray(args.source.read_bytes())
    if hashlib.sha256(payload).hexdigest() != patch["source_sha256"]:
        parser.error("the input does not match the trial PinkBeret_GuYou.uexp")

    for vertex, uv in patch["vertices"]:
        offset = patch["uv_offset"] + 4 * vertex
        payload[offset:offset + 4] = bytes.fromhex(uv)

    if hashlib.sha256(payload).hexdigest() != patch["result_sha256"]:
        parser.error("the patched payload did not match the release hash")
    with args.destination.open("xb") as output:
        output.write(payload)


if __name__ == "__main__":
    main()
