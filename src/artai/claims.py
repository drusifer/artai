"""Per-item claim files so any number of ``artai generate`` processes can share a work dir.

A claim is ``<claims_dir>/<id>.lock`` holding ``{pid, start_time, host}``. It is created with
``os.link`` from a fully written temp file, so a claim is never seen half-written. A claim
whose owner is no longer alive on this host is stale and may be taken over.
"""

from __future__ import annotations

import fcntl
import json
import os
import socket
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Claim:
    path: Path
    record: dict[str, Any]


def _start_time(pid: int) -> str | None:
    """Process start time from /proc (field 22) — distinguishes a reused PID. None if unknown."""
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
    except (OSError, IndexError):
        return None
    return None if fields[0] == "Z" else fields[19]


def _me() -> dict[str, Any]:
    pid = os.getpid()
    return {"pid": pid, "start_time": _start_time(pid), "host": socket.gethostname()}


def _alive(record: dict[str, Any]) -> bool:
    if record.get("host") != socket.gethostname():
        return True  # cannot check another machine: assume it is still working
    pid = record.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return False
    if Path("/proc").is_dir():
        current = _start_time(pid)
        return current is not None and current == record.get("start_time")
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read(path: Path) -> dict[str, Any] | None:
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return record if isinstance(record, dict) else None


def holder(claims_dir: Path, item_id: str) -> tuple[dict[str, Any] | None, bool]:
    """(record, alive) for the current claim on ``item_id``; (None, False) when unclaimed."""
    path = claims_dir / f"{item_id}.lock"
    if not path.exists():
        return None, False
    record = _read(path)
    return (record or {}), bool(record) and _alive(record)


def try_claim(claims_dir: Path, item_id: str) -> Claim | None:
    """Claim ``item_id`` for this process, taking over a stale claim. None if a live process holds it."""
    claims_dir.mkdir(parents=True, exist_ok=True)
    path = claims_dir / f"{item_id}.lock"
    record = _me()
    handle, temp_name = tempfile.mkstemp(prefix=f".{item_id}.", suffix=".tmp", dir=claims_dir)
    temp = Path(temp_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(record, stream)
        try:
            os.link(temp, path)
            return Claim(path, record)
        except FileExistsError:
            pass
        # Taking over a stale claim: check, remove and re-link under one directory lock, so two
        # processes that both saw the same dead claim cannot remove each other's new one.
        with (claims_dir / ".takeover").open("a") as mutex:
            fcntl.flock(mutex, fcntl.LOCK_EX)
            if holder(claims_dir, item_id)[1]:
                return None
            path.unlink(missing_ok=True)
            try:
                os.link(temp, path)
            except FileExistsError:
                return None
            return Claim(path, record)
    finally:
        temp.unlink(missing_ok=True)


def release(claim: Claim) -> None:
    """Remove the claim if it is still ours."""
    if _read(claim.path) == claim.record:
        claim.path.unlink(missing_ok=True)


def clear_stale(claims_dir: Path, item_id: str) -> bool:
    """Remove a dead owner's claim. False if the owner is alive. True if removed or absent."""
    record, live = holder(claims_dir, item_id)
    if record is None:
        return True
    if live:
        return False
    (claims_dir / f"{item_id}.lock").unlink(missing_ok=True)
    return True
