"""Generate masters for a set: resumable, bounded-parallel, quota-terminal, safe across processes.

Each rule exists because a real production run went wrong without it (recard imagegen,
GlobalHeadsOrTails sticker_art): never pay twice for an image already on disk; the first quota
error stops everything; validate images by dimensions; claim each item before working on it.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime

from artai.backends._proc import append_log, kill_all
from artai.backends.base import Backend, GenerationFailed, Job, QuotaExhausted
from artai.claims import release, try_claim
from artai.imaging import is_placeholder, is_valid
from artai.model import ArtSet, Item
from artai.prompts import render


@dataclass(frozen=True)
class RunOptions:
    parallel: int = 2
    retries: int = 2  # extra attempts after the first
    timeout: float = 600.0
    min_size: int = 512
    reverse: bool = False


@dataclass
class RunSummary:
    total: int = 0
    ok: int = 0
    skipped: int = 0
    busy: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    quota: bool = False
    not_started: int = 0

    def as_dict(self) -> dict:
        return asdict(self)


Result = str  # "ok" | "skip" | "busy" | "fail" | "quota" | "stopped"
OnResult = Callable[[Result, Item, int, int], None]


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


class _Run:
    def __init__(self, art_set: ArtSet, backend: Backend, options: RunOptions, on_result: OnResult | None):
        self.art_set = art_set
        self.backend = backend
        self.options = options
        self.on_result = on_result
        self.quota = threading.Event()
        self.interrupted = threading.Event()
        self.lock = threading.Lock()
        self.summary = RunSummary()
        self.done = 0

    def finished(self, master) -> bool:
        if not is_valid(master, self.options.min_size):
            return False
        # Placeholder art only counts as finished for the mock backend itself.
        return self.backend.name == "mock" or not is_placeholder(master)

    def one(self, item: Item) -> Result:
        master = item.master(self.art_set)
        if self.finished(master):
            return "skip"
        if self.quota.is_set() or self.interrupted.is_set():
            return "stopped"
        claim = try_claim(self.art_set.claims_dir, item.id)
        if claim is None:
            return "busy"
        try:
            if self.finished(master):  # another process finished it between our checks
                return "skip"
            return self.attempts(item, master)
        finally:
            release(claim)

    def attempts(self, item: Item, master) -> Result:
        log = self.art_set.logs_dir / f"{item.id}.log"
        job = Job(
            id=item.id,
            prompt=render(self.art_set, item).prompt,
            master=master,
            log=log,
            timeout=self.options.timeout,
            reference_image=item.reference_image,
        )
        for attempt in range(1, self.options.retries + 2):
            if self.quota.is_set() or self.interrupted.is_set():
                return "stopped"
            master.unlink(missing_ok=True)  # anything here is invalid or placeholder art
            append_log(log, f"=== attempt {attempt} · backend {self.backend.name} · {_now()} ===")
            try:
                self.backend.generate(job)
            except QuotaExhausted as error:
                append_log(log, f"quota exhausted: {error}")
                self.quota.set()
                self.art_set.work_dir.mkdir(parents=True, exist_ok=True)
                self.art_set.quota_marker.write_text(_now() + "\n", encoding="utf-8")
                return "quota"
            except GenerationFailed as error:
                append_log(log, f"failed: {error}")
                continue
            except Exception as error:  # a provider bug must not kill the other workers
                append_log(log, f"failed: {type(error).__name__}: {error}")
                continue
            if is_valid(master, self.options.min_size):
                return "ok"
            append_log(
                log, f"failed: backend produced no valid image (≥{self.options.min_size}px) at {master}"
            )
        return "fail"

    def record(self, item: Item, result: Result) -> None:
        with self.lock:
            summary = self.summary
            if result == "ok":
                summary.ok += 1
            elif result == "skip":
                summary.skipped += 1
            elif result == "busy":
                summary.busy.append(item.id)
            elif result == "fail":
                summary.failed.append(item.id)
            elif result == "quota":
                summary.quota = True
            if result == "stopped":
                summary.not_started += 1
            else:
                self.done += 1
            if self.on_result and result != "stopped":
                self.on_result(result, item, self.done, summary.total)


def run(
    art_set: ArtSet,
    items: list[Item],
    backend: Backend,
    options: RunOptions | None = None,
    on_result: OnResult | None = None,
) -> RunSummary:
    options = options or RunOptions()
    queue = list(reversed(items)) if options.reverse else list(items)
    state = _Run(art_set, backend, options, on_result)
    state.summary.total = len(queue)
    cursor = iter(queue)
    cursor_lock = threading.Lock()

    def worker() -> None:
        while True:
            with cursor_lock:
                item = next(cursor, None)
            if item is None:
                return
            state.record(item, state.one(item))

    lanes = max(1, min(options.parallel, len(queue) or 1))
    pool = ThreadPoolExecutor(max_workers=lanes, thread_name_prefix="artai")
    futures = [pool.submit(worker) for _ in range(lanes)]
    try:
        for future in futures:
            future.result()
    except KeyboardInterrupt:
        # Stop scheduling, kill running providers; workers then release their claims.
        state.interrupted.set()
        kill_all()
        pool.shutdown(wait=True, cancel_futures=True)
        raise
    pool.shutdown(wait=True)

    summary = state.summary
    summary.failed.sort(key=[i.id for i in queue].index)
    if not summary.quota and art_set.quota_marker.exists():
        art_set.quota_marker.unlink()
    return summary
