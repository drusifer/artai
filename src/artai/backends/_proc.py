"""Run a provider program with a timeout, capturing its output to the item log."""

from __future__ import annotations

import os
import re
import signal
import subprocess
import threading
from datetime import UTC, datetime
from pathlib import Path

QUOTA = re.compile(
    r"quota|usage limit|rate limit|\b429\b|too many requests|upgrade your (subscription|plan)", re.I
)


_ACTIVE: set[subprocess.Popen] = set()
_ACTIVE_LOCK = threading.Lock()


def kill_all() -> None:
    """Kill every provider process group still running (used on Ctrl-C)."""
    with _ACTIVE_LOCK:
        processes = list(_ACTIVE)
    for process in processes:
        _kill(process)


def _kill(process: subprocess.Popen) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def is_quota(text: str) -> bool:
    return bool(QUOTA.search(text))


def append_log(log: Path, text: str) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as stream:
        stream.write(text if text.endswith("\n") else text + "\n")


def run_logged(
    argv: list[str],
    log: Path,
    timeout: float,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> tuple[int | None, str]:
    """Run ``argv`` (never through a shell). Returns (exit code, output); code None = did not finish."""
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    append_log(log, f"$ {argv[0]} … ({stamp})")
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
            start_new_session=True,  # so a timeout can kill the provider's children too
        )
    except FileNotFoundError:
        message = f"program not found: {argv[0]}"
        append_log(log, message)
        return None, message
    with _ACTIVE_LOCK:
        _ACTIVE.add(process)
    try:
        output, _ = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill(process)
        output, _ = process.communicate()
        output = f"{output or ''}\ntimed out after {timeout:g}s"
        append_log(log, output)
        return None, output
    except BaseException:
        _kill(process)
        raise
    finally:
        with _ACTIVE_LOCK:
            _ACTIVE.discard(process)
    if process.returncode < 0:
        message = f"{output or ''}\nstopped by signal {-process.returncode}"
        append_log(log, message)
        return None, message
    append_log(log, output or "")
    append_log(log, f"exit {process.returncode}")
    return process.returncode, output or ""
