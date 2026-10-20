import pytest

from artai import backends
from artai.cli import main
from tests.conftest import write
from tests.helpers.fakes import Scripted


@pytest.fixture
def manifest(in_tmp):
    return str(write(in_tmp / "j.tsv", "".join(f"i{n}\tprompt {n}\n" for n in range(4))))


@pytest.fixture
def scripted(monkeypatch):
    holder = {}

    def factory(art_set, script=None):
        holder["backend"] = Scripted(holder.get("script"))
        return holder["backend"]

    monkeypatch.setitem(backends.REGISTRY, "scripted", factory)
    return holder


def test_backend_is_required(manifest, capsys):
    assert main(["generate", manifest]) == 1
    err = capsys.readouterr().err
    assert "--backend" in err and "mock" in err


def test_mock_generate_and_resume(manifest, in_tmp, capsys):
    assert main(["generate", manifest, "--backend", "mock"]) == 0
    assert len(list((in_tmp / "build/artai/j/masters").glob("*.png"))) == 4
    assert "4 generated, 0 already present" in capsys.readouterr().out
    assert main(["generate", manifest, "--backend", "mock"]) == 0
    assert "0 generated, 4 already present" in capsys.readouterr().out


@pytest.mark.parametrize("value", ["0", "9", "x"])
def test_parallel_bounds(manifest, value, capsys, in_tmp):
    assert main(["generate", manifest, "--backend", "mock", "--parallel", value]) == 1
    assert "--parallel" in capsys.readouterr().err
    assert not (in_tmp / "build").exists()


def test_unknown_ids_refused(manifest, capsys, in_tmp):
    assert main(["generate", manifest, "--backend", "mock", "--ids", "i1,zz"]) == 1
    assert "unknown id zz" in capsys.readouterr().err
    assert not (in_tmp / "build").exists()


def test_ids_selects_subset(manifest, in_tmp):
    assert main(["generate", manifest, "--backend", "mock", "--ids", "i1,i3"]) == 0
    names = sorted(p.name for p in (in_tmp / "build/artai/j/masters").glob("*.png"))
    assert names == ["i1.png", "i3.png"]


def test_quota_exit_2_with_advice(manifest, scripted, capsys):
    scripted["script"] = {"i0": ["quota"]}
    assert main(["generate", manifest, "--backend", "scripted", "--parallel", "1"]) == 2
    err = capsys.readouterr().err
    assert "quota exhausted" in err and "Re-run the same command" in err


def test_failures_exit_1_listing_ids(manifest, scripted, capsys):
    scripted["script"] = {"i2": ["fail"] * 5}
    assert main(["generate", manifest, "--backend", "scripted", "--retries", "1"]) == 1
    out = capsys.readouterr().out
    assert "failed: i2" in out


def test_status_separates_placeholders(manifest, scripted, capsys):
    assert main(["generate", manifest, "--backend", "mock", "--ids", "i0,i1"]) == 0
    assert main(["generate", manifest, "--backend", "scripted", "--ids", "i2"]) == 0
    capsys.readouterr()
    assert main(["status", manifest]) == 0
    out = capsys.readouterr().out
    assert "masters:      1 " in out and "placeholders: 2 " in out
