import json
import os
import socket

from artai.claims import holder, release, try_claim


def test_claim_is_exclusive_and_released(tmp_path):
    first = try_claim(tmp_path, "a")
    assert first is not None
    assert try_claim(tmp_path, "a") is None
    record, live = holder(tmp_path, "a")
    assert record["pid"] == os.getpid() and live
    release(first)
    assert holder(tmp_path, "a") == (None, False)
    assert try_claim(tmp_path, "a") is not None


def test_stale_claim_from_dead_process_is_taken_over(tmp_path):
    (tmp_path / "a.lock").write_text(
        json.dumps({"pid": 999_999_999, "start_time": "1", "host": socket.gethostname()})
    )
    _, live = holder(tmp_path, "a")
    assert not live
    claim = try_claim(tmp_path, "a")
    assert claim is not None
    assert json.loads((tmp_path / "a.lock").read_text())["pid"] == os.getpid()


def test_unreadable_claim_is_stale(tmp_path):
    (tmp_path / "a.lock").write_text("")
    assert try_claim(tmp_path, "a") is not None


def test_claim_from_other_host_is_assumed_live(tmp_path):
    (tmp_path / "a.lock").write_text(json.dumps({"pid": 1, "start_time": "1", "host": "elsewhere"}))
    assert holder(tmp_path, "a")[1] is True
    assert try_claim(tmp_path, "a") is None


def test_concurrent_takeover_of_stale_claim_has_one_winner(tmp_path):
    import threading

    stale = json.dumps({"pid": 999_999_999, "start_time": "1", "host": socket.gethostname()})
    for round_ in range(20):
        item = f"x{round_}"
        (tmp_path / f"{item}.lock").write_text(stale)
        results = []
        barrier = threading.Barrier(4)

        def contend(item=item, barrier=barrier, results=results):
            barrier.wait()
            results.append(try_claim(tmp_path, item))

        threads = [threading.Thread(target=contend) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert sum(r is not None for r in results) == 1
