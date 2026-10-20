import json
import subprocess
import sys
import textwrap

import pytest

from artai.backends import get_backend
from artai.imaging import is_placeholder
from artai.manifest import load_manifest
from artai.runner import RunOptions, run
from tests.conftest import write
from tests.helpers.fakes import Scripted, paint


@pytest.fixture
def five(in_tmp):
    path = write(in_tmp / "j.tsv", "".join(f"i{n}\tprompt {n}\n" for n in range(5)))
    return load_manifest(path)


def test_generates_every_item_then_resumes(five):
    art_set, items = five
    backend = Scripted()
    summary = run(art_set, items, backend, RunOptions())
    assert (summary.ok, summary.skipped, summary.failed, summary.quota) == (5, 0, [], False)
    again = Scripted()
    summary = run(art_set, items, again, RunOptions())
    assert (summary.ok, summary.skipped) == (0, 5)
    assert again.calls == []


def test_too_small_or_corrupt_master_is_regenerated(five):
    art_set, items = five
    paint(items[0].master(art_set), size=100)
    items[1].master(art_set).write_bytes(b"\x89PNG broken")
    backend = Scripted()
    run(art_set, items, backend, RunOptions(min_size=512))
    assert sorted(backend.calls) == ["i0", "i1", "i2", "i3", "i4"]


def test_retries_then_reports_failed_ids(five):
    art_set, items = five
    backend = Scripted({"i1": ["fail", "fail", "fail"], "i2": ["fail", "ok"], "i3": ["tiny", "tiny", "tiny"]})
    summary = run(art_set, items, backend, RunOptions(retries=2, parallel=1))
    assert summary.failed == ["i1", "i3"]
    assert backend.calls.count("i1") == 3 and backend.calls.count("i2") == 2
    assert summary.ok == 3
    log = (art_set.logs_dir / "i1.log").read_text()
    assert log.count("attempt") == 3 and "provider said no" in log


def test_quota_stops_run_and_leaves_marker(five):
    art_set, items = five
    backend = Scripted({"i1": ["quota"]})
    summary = run(art_set, items, backend, RunOptions(parallel=1))
    assert summary.quota is True
    assert backend.calls == ["i0", "i1"]
    assert art_set.quota_marker.is_file()
    assert summary.not_started == 3


def test_clean_run_clears_old_quota_marker(five):
    art_set, items = five
    art_set.work_dir.mkdir(parents=True)
    art_set.quota_marker.write_text("2026-01-01T00:00:00+00:00")
    run(art_set, items, Scripted(), RunOptions())
    assert not art_set.quota_marker.exists()


def test_reverse_order(five):
    art_set, items = five
    backend = Scripted()
    run(art_set, items, backend, RunOptions(parallel=1, reverse=True))
    assert backend.calls == ["i4", "i3", "i2", "i1", "i0"]


def test_parallel_runs_concurrently(five):
    import time

    art_set, items = five
    started = time.monotonic()
    run(art_set, items, Scripted(delay=0.3), RunOptions(parallel=5))
    assert time.monotonic() - started < 1.2


def test_item_claimed_by_live_process_is_busy(five):
    from artai.claims import try_claim

    art_set, items = five
    claim = try_claim(art_set.claims_dir, "i2")
    assert claim is not None
    backend = Scripted()
    summary = run(art_set, items, backend, RunOptions())
    assert summary.busy == ["i2"] and "i2" not in backend.calls


def test_real_backend_replaces_mock_placeholders(five):
    art_set, items = five
    run(art_set, items, get_backend("mock", art_set), RunOptions())
    assert is_placeholder(items[0].master(art_set))
    again = run(art_set, items, get_backend("mock", art_set), RunOptions())
    assert again.skipped == 5
    real = Scripted()
    summary = run(art_set, items, real, RunOptions())
    assert summary.ok == 5 and not is_placeholder(items[0].master(art_set))


def test_backend_that_writes_nothing_fails(five):
    art_set, items = five
    summary = run(art_set, items[:1], Scripted(default="none"), RunOptions(retries=0))
    assert summary.failed == ["i0"]
    assert "no valid image" in (art_set.logs_dir / "i0.log").read_text()


TWO_PROCESS = textwrap.dedent(
    """
    import sys, time
    from artai.manifest import load_manifest
    from artai.runner import RunOptions, run
    sys.path.insert(0, {root!r})
    from tests.helpers.fakes import Scripted

    class Recording(Scripted):
        def generate(self, job):
            with open({calls!r}, "a") as f:
                f.write(job.id + "\\n")
            super().generate(job)

    art_set, items = load_manifest({manifest!r})
    run(art_set, items, Recording(delay=0.2), RunOptions(parallel=2))
    """
)


def test_two_processes_never_generate_the_same_item(in_tmp):
    from pathlib import Path

    manifest = write(in_tmp / "j.tsv", "".join(f"i{n}\tp\n" for n in range(8)))
    calls = in_tmp / "calls.txt"
    root = str(Path(__file__).resolve().parents[1])
    script = TWO_PROCESS.format(root=root, calls=str(calls), manifest=str(manifest))
    procs = [subprocess.Popen([sys.executable, "-c", script], cwd=in_tmp) for _ in range(2)]
    assert [p.wait(timeout=60) for p in procs] == [0, 0]
    ids = calls.read_text().split()
    assert sorted(ids) == sorted(set(ids))
    assert len(set(ids)) == 8
    assert not list((in_tmp / "build/artai/j/claims").glob("*.lock"))


def test_summary_json_shape(five):
    art_set, items = five
    summary = run(art_set, items, Scripted(), RunOptions())
    assert json.loads(json.dumps(summary.as_dict()))["ok"] == 5
