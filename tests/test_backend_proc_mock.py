import sys

import pytest

from artai.backends import BACKEND_NAMES, get_backend
from artai.backends._proc import is_quota, run_logged
from artai.backends.base import Job
from artai.errors import ConfigError
from artai.imaging import is_placeholder, is_valid
from artai.manifest import load_manifest
from tests.conftest import write


@pytest.mark.parametrize(
    "text",
    [
        "Quota exceeded",
        "You've hit your usage limit",
        "rate limit reached",
        "HTTP 429",
        "Too Many Requests",
        "please upgrade your plan",
        "Upgrade your subscription",
    ],
)
def test_quota_phrases(text):
    assert is_quota(text)


def test_ordinary_failure_is_not_quota():
    assert not is_quota("error: file not found")


def test_run_logged_captures_output_and_code(tmp_path):
    log = tmp_path / "logs/a.log"
    code, output = run_logged([sys.executable, "-c", "import sys; print('hi'); sys.exit(3)"], log, timeout=10)
    assert code == 3 and "hi" in output
    assert "hi" in log.read_text()


def test_run_logged_times_out(tmp_path):
    code, output = run_logged(
        [sys.executable, "-c", "import time; time.sleep(30)"], tmp_path / "l.log", timeout=0.5
    )
    assert code is None and "timed out" in output


def test_run_logged_missing_program(tmp_path):
    code, output = run_logged(["definitely-not-a-program-xyz"], tmp_path / "l.log", timeout=5)
    assert code is None and "not found" in output


def test_unknown_backend_lists_choices(in_tmp):
    art_set, _ = load_manifest(write(in_tmp / "j.tsv", "a\tA\n"))
    with pytest.raises(ConfigError, match="unknown backend 'nope'"):
        get_backend("nope", art_set)
    assert "mock" in BACKEND_NAMES


def test_mock_writes_tagged_deterministic_master(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "j.tsv", "a\tA\n"))
    backend = get_backend("mock", art_set)
    job = Job(id="a", prompt="A", master=in_tmp / "m/a.png", log=in_tmp / "l/a.log", timeout=5)
    backend.generate(job)
    first = job.master.read_bytes()
    backend.generate(job)
    assert job.master.read_bytes() == first
    assert is_valid(job.master, 1024) and is_placeholder(job.master)


def test_kill_all_stops_running_provider(tmp_path):
    import threading
    import time

    from artai.backends._proc import kill_all

    result = {}

    def target():
        result["value"] = run_logged(
            [sys.executable, "-c", "import time; time.sleep(30)"], tmp_path / "l.log", 60
        )

    thread = threading.Thread(target=target)
    started = time.monotonic()
    thread.start()
    time.sleep(0.5)
    kill_all()
    thread.join(timeout=10)
    assert not thread.is_alive() and time.monotonic() - started < 5
    assert result["value"][0] is None and "stopped by signal" in result["value"][1]
