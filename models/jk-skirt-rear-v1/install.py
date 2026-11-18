"""Install only the reviewed three files and check the actual mounted body."""
import shutil
from datetime import datetime

from build import WORK, common, read, sha, verify, write


def install():
    before = read(WORK / "before.json")
    assert common.snapshot() == before, "Effective installation changed since packaging"
    assert read(WORK / "final-verification.json")["passed"]
    assert read(WORK / "motion/evaluation.json")["passed"]
    review = read(WORK / "review.json")
    assert review["passed"] and all(sha(WORK / path) == digest for path, digest in review["hashes"].items())
    files = read(WORK / "build.json")["files"]
    assert files == read(WORK / "final-verification.json")["files"]
    assert all(sha(WORK / "container" / row["name"]) == row["sha256"] for row in files)
    assert not common.game_pids(), "Exit the game before installation"
    created = []
    try:
        for row in files:
            assert not common.game_pids()
            target = common.MODS / row["name"]
            with (WORK / "container" / target.name).open("rb") as source, target.open("xb") as out:
                created.append(target)
                shutil.copyfileobj(source, out)
            assert sha(target) == row["sha256"]
        after = common.snapshot()
        expected = {row["name"]: row for row in before + files}
        assert len(after) == len(expected) and all(expected.get(row["name"]) == row for row in after)
        verify("installed", [common.MODS])
        assert common.snapshot() == after
        write(WORK / "installation.json", dict(installed_at=datetime.now().astimezone().isoformat(),
              before=before, after=after, added=files, independent_readback=True, game_runtime_tested=False))
    except Exception:
        # Only files exclusively created by this invocation can be rolled back.
        if not common.game_pids():
            for path in reversed(created):
                expected = next(row for row in files if row["name"] == path.name)
                if sha(path) == expected["sha256"]:
                    path.unlink()
        raise


if __name__ == "__main__":
    install()
