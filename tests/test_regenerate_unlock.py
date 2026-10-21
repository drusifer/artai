import json
import os
import socket
import subprocess
import sys

import pytest

from artai.cli import main
from tests.conftest import write


@pytest.fixture
def made(in_tmp, capsys):
    manifest = str(
        write(in_tmp / "m.yaml", "artwork_set: {name: s}\nitems: [{id: a, prompt: A}, {id: b, prompt: B}]")
    )
    assert main(["generate", manifest, "--backend", "mock"]) == 0
    assert main(["pack", manifest]) == 0
    capsys.readouterr()
    return manifest, in_tmp / "build/artai/s"


def live_claim(work, item_id):
    """A claim held by a real, still-running process."""
    sleeper = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    stat = open(f"/proc/{sleeper.pid}/stat").read().rsplit(")", 1)[1].split()
    (work / "claims").mkdir(parents=True, exist_ok=True)
    record = {"pid": sleeper.pid, "start_time": stat[19], "host": socket.gethostname()}
    (work / f"claims/{item_id}.lock").write_text(json.dumps(record))
    return sleeper


def test_regenerate_archives_then_generates(made, capsys):
    manifest, work = made
    old_master = (work / "masters/a.png").read_bytes()
    assert main(["regenerate", manifest, "--ids", "a", "--backend", "mock"]) == 0
    archives = list((work / "rejected").iterdir())
    assert len(archives) == 1
    assert sorted(p.name for p in archives[0].iterdir()) == ["a.png", "a.webp"]
    assert (archives[0] / "a.png").read_bytes() == old_master
    assert (work / "masters/a.png").is_file()  # regenerated
    assert not (work / "out/a.webp").exists()  # needs a fresh pack
    assert (work / "masters/b.png").is_file() and (work / "out/b.webp").is_file()
    assert "pack" in capsys.readouterr().out


def test_regenerate_requires_ids(made, capsys):
    manifest, work = made
    assert main(["regenerate", manifest, "--backend", "mock"]) == 1
    assert "--ids" in capsys.readouterr().err
    assert not (work / "rejected").exists()


def test_regenerate_refuses_all_if_any_is_live(made, capsys):
    manifest, work = made
    sleeper = live_claim(work, "b")
    try:
        assert main(["regenerate", manifest, "--ids", "a,b", "--backend", "mock"]) == 1
        assert "b" in capsys.readouterr().err
        assert not (work / "rejected").exists()
        assert (work / "masters/a.png").is_file()
    finally:
        sleeper.kill()


def test_unlock_clears_dead_and_refuses_live(made, capsys):
    manifest, work = made
    (work / "claims/a.lock").write_text(
        json.dumps({"pid": 999_999_999, "start_time": "1", "host": socket.gethostname()})
    )
    sleeper = live_claim(work, "b")
    try:
        assert main(["unlock", manifest, "--ids", "a,b"]) == 1
        assert "b is held by live process" in capsys.readouterr().err
        assert (work / "claims/a.lock").exists()  # all-or-nothing
        assert main(["unlock", manifest, "--ids", "a"]) == 0
        assert "cleared stale claim: a" in capsys.readouterr().out
        assert not (work / "claims/a.lock").exists()
    finally:
        sleeper.kill()


def test_unlock_requires_ids(made, capsys):
    manifest, _ = made
    assert main(["unlock", manifest]) == 1
    assert "--ids" in capsys.readouterr().err


def test_unlock_nothing_to_clear(made, capsys):
    manifest, _ = made
    assert main(["unlock", manifest, "--ids", "a"]) == 0
    assert "no claim: a" in capsys.readouterr().out


assert os.name == "posix"


def test_generate_force_archives_then_regenerates(made, capsys):
    manifest, work = made
    assert main(["generate", manifest, "--backend", "mock"]) == 0
    assert "0 generated, 2 already present" in capsys.readouterr().out
    assert main(["generate", manifest, "--backend", "mock", "--force", "--ids", "a"]) == 0
    out = capsys.readouterr().out
    assert "1 generated" in out and "set aside" in out
    assert len(list((work / "rejected").iterdir())) == 1


def test_pack_cli_reports_up_to_date(made, capsys):
    manifest, _ = made
    assert main(["pack", manifest]) == 0
    assert "2 already up to date" in capsys.readouterr().out
