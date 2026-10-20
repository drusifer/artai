import base64
import io
import json
import os
import signal
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from PIL import Image

from artai.backends import get_backend
from artai.backends.base import GenerationFailed, Job, QuotaExhausted
from artai.cli import main
from artai.errors import ConfigError
from artai.imaging import is_valid
from artai.manifest import load_manifest
from tests.conftest import write
from tests.helpers.fake_cli import make_fake


@pytest.fixture
def fake(in_tmp, monkeypatch):
    record = in_tmp / "record.jsonl"
    monkeypatch.setenv("FAKE_RECORD", str(record))
    (in_tmp / "bin").mkdir()
    program = make_fake(in_tmp / "bin")

    def calls():
        return [json.loads(line) for line in record.read_text().splitlines()] if record.exists() else []

    return program, calls


def yaml_set(in_tmp, command="", extra=""):
    text = (
        f"artwork_set:\n  name: s\n  command: {json.dumps(command)}\n{extra}"
        "items:\n  - {id: a, prompt: A fox}\n  - {id: b, prompt: A bee}\n"
    )
    return write(in_tmp / "m.yaml", text)


def job_for(art_set, item_id="a", prompt="A fox", reference=None, timeout=30):
    return Job(
        id=item_id,
        prompt=prompt,
        master=art_set.masters_dir / f"{item_id}.png",
        log=art_set.logs_dir / f"{item_id}.log",
        timeout=timeout,
        reference_image=reference,
    )


# ── command ────────────────────────────────────────────────────────────────


def test_command_backend_end_to_end(in_tmp, fake, capsys):
    program, calls = fake
    manifest = yaml_set(in_tmp, f"{program} --size {{resolution}} --out {{output}} {{prompt}}")
    assert main(["generate", str(manifest), "--backend", "command"]) == 0
    assert is_valid(in_tmp / "build/artai/s/masters/a.png", 512)
    argvs = sorted(call["argv"] for call in calls())
    assert argvs[0][:2] == ["--size", "512x512"]
    assert {argv[-1] for argv in argvs} == {"A fox", "A bee"}


def test_command_prompt_cannot_inject_shell(in_tmp, fake):
    program, calls = fake
    art_set, _ = load_manifest(yaml_set(in_tmp, f"{program} --out {{output}} {{prompt}}"))
    backend = get_backend("command", art_set)
    evil = 'x"; touch PWNED; echo "$(touch PWNED2)'
    backend.generate(job_for(art_set, prompt=evil))
    assert calls()[0]["argv"][-1] == evil
    assert not (in_tmp / "PWNED").exists() and not (in_tmp / "PWNED2").exists()


def test_command_accepts_ghot_cli_command_alias(in_tmp, fake):
    program, _ = fake
    command = f"{program} --out {{output_path}} {{prompt}}"
    text = f"artwork_set: {{name: s, cli_command: '{command}'}}\nitems: [{{id: a, prompt: p}}]\n"
    art_set, _ = load_manifest(write(in_tmp / "g.yaml", text))
    get_backend("command", art_set).generate(job_for(art_set))
    assert is_valid(art_set.masters_dir / "a.png", 512)


def test_command_missing_template_refused(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "j.tsv", "a\tA\n"))
    with pytest.raises(ConfigError, match="artwork_set.command"):
        get_backend("command", art_set).preflight(items, 1)


@pytest.mark.parametrize(("mode", "error"), [("quota", QuotaExhausted), ("fail", GenerationFailed)])
def test_command_failure_modes(in_tmp, fake, monkeypatch, mode, error):
    program, _ = fake
    monkeypatch.setenv("FAKE_MODE", mode)
    art_set, _ = load_manifest(yaml_set(in_tmp, f"{program} --out {{output}} {{prompt}}"))
    with pytest.raises(error):
        get_backend("command", art_set).generate(job_for(art_set))


# ── codex ──────────────────────────────────────────────────────────────────


def test_codex_safe_flags_prompt_and_cwd(in_tmp, fake, monkeypatch):
    program, calls = fake
    monkeypatch.setenv("ARTAI_CODEX_CLI", str(program))
    art_set, _ = load_manifest(yaml_set(in_tmp))
    get_backend("codex", art_set).generate(job_for(art_set))
    call = calls()[0]
    argv = call["argv"]
    assert argv[:4] == ["exec", "--sandbox", "workspace-write", "--skip-git-repo-check"]
    assert not any("dangerously" in a or "bypass" in a for a in argv)
    assert "image generation tool" in argv[-1] and "Do not write code" in argv[-1]
    assert f"Save it to {art_set.masters_dir / 'a.png'}." in argv[-1]
    assert call["cwd"] == str(art_set.masters_dir)
    assert is_valid(art_set.masters_dir / "a.png", 512)


def test_codex_quota_and_failure(in_tmp, fake, monkeypatch):
    program, _ = fake
    monkeypatch.setenv("ARTAI_CODEX_CLI", str(program))
    art_set, _ = load_manifest(yaml_set(in_tmp))
    backend = get_backend("codex", art_set)
    monkeypatch.setenv("FAKE_MODE", "quota")
    with pytest.raises(QuotaExhausted):
        backend.generate(job_for(art_set))
    monkeypatch.setenv("FAKE_MODE", "nothing")
    with pytest.raises(GenerationFailed, match="without writing"):
        backend.generate(job_for(art_set))


def test_codex_reference_clause_and_missing_reference(in_tmp, fake, monkeypatch):
    program, calls = fake
    monkeypatch.setenv("ARTAI_CODEX_CLI", str(program))
    art_set, _ = load_manifest(yaml_set(in_tmp))
    reference = in_tmp / "ref.png"
    Image.new("RGB", (8, 8)).save(reference)
    backend = get_backend("codex", art_set)
    backend.generate(job_for(art_set, reference=reference))
    assert f"available at {reference}" in calls()[0]["argv"][-1]
    with pytest.raises(GenerationFailed, match="reference image not found: .*gone.png"):
        backend.generate(job_for(art_set, reference=in_tmp / "gone.png"))


# ── agy ────────────────────────────────────────────────────────────────────


def test_agy_argv_and_direct_write(in_tmp, fake, monkeypatch):
    program, calls = fake
    monkeypatch.setenv("ARTAI_AGY_CLI", str(program))
    monkeypatch.setenv("ARTAI_AGY_MODEL", "img-2")
    art_set, _ = load_manifest(yaml_set(in_tmp))
    get_backend("agy", art_set).generate(job_for(art_set, timeout=600))
    argv = calls()[0]["argv"]
    assert argv[0] == "-p" and "generate_image" in argv[1]
    assert argv[2:] == ["--output-format", "json", "--print-timeout", "10m", "--sandbox", "--model", "img-2"]
    assert "--dangerously-skip-permissions" not in argv


def test_agy_claims_newest_scratch_file(in_tmp, fake, monkeypatch):
    program, _ = fake
    monkeypatch.setenv("ARTAI_AGY_CLI", str(program))
    monkeypatch.setenv("ARTAI_AGY_SCRATCH", str(in_tmp / "scratch"))
    monkeypatch.setenv("FAKE_MODE", "scratch")
    art_set, _ = load_manifest(yaml_set(in_tmp))
    get_backend("agy", art_set).generate(job_for(art_set))
    with Image.open(art_set.masters_dir / "a.png") as image:
        assert image.size == (640, 640)
    assert [p.name for p in (in_tmp / "scratch").iterdir()] == ["a_1.png"]


def test_agy_yolo_only_for_one_item(in_tmp, fake, monkeypatch, capsys):
    program, calls = fake
    monkeypatch.setenv("ARTAI_AGY_CLI", str(program))
    monkeypatch.setenv("ARTAI_AGY_YOLO", "1")
    manifest = str(yaml_set(in_tmp))
    assert main(["generate", manifest, "--backend", "agy"]) == 1
    assert "ARTAI_AGY_YOLO" in capsys.readouterr().err and calls() == []
    assert main(["generate", manifest, "--backend", "agy", "--ids", "a"]) == 0
    assert "--dangerously-skip-permissions" in calls()[0]["argv"]


# ── gemini ─────────────────────────────────────────────────────────────────


def png_bytes(size=600):
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), "purple").save(buffer, "PNG")
    return buffer.getvalue()


class Stub:
    def __init__(self):
        self.requests = []
        self.reply = (200, {"output_image": {"data": base64.b64encode(png_bytes()).decode()}})
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = json.loads(self.rfile.read(int(self.headers["content-length"])))
                stub.requests.append({"headers": dict(self.headers), "body": body})
                status, payload = stub.reply
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_port}/v1beta/interactions"


@pytest.fixture
def stub(monkeypatch):
    server = Stub()
    monkeypatch.setenv("ARTAI_GEMINI_ENDPOINT", server.url)
    monkeypatch.setenv("GEMINI_API_KEY", "SECRET-KEY-123")
    yield server
    server.server.shutdown()


def test_gemini_requires_key(in_tmp, monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert main(["generate", str(yaml_set(in_tmp)), "--backend", "gemini"]) == 1
    assert "GEMINI_API_KEY" in capsys.readouterr().err
    assert not (in_tmp / "build").exists()


def test_gemini_success_request_shape_and_no_key_leak(in_tmp, stub, capsys):
    manifest = str(yaml_set(in_tmp))
    assert main(["generate", manifest, "--backend", "gemini"]) == 0
    request = stub.requests[0]
    headers = {k.lower(): v for k, v in request["headers"].items()}
    assert headers["x-goog-api-key"] == "SECRET-KEY-123"
    assert request["body"]["model"] == "gemini-nano-banana-2.1"
    assert request["body"]["input"][0]["type"] == "text"
    assert request["body"]["response_format"]["aspect_ratio"] == "1:1"
    assert is_valid(in_tmp / "build/artai/s/masters/a.png", 512)
    everything = capsys.readouterr()
    logs = "".join(p.read_text() for p in (in_tmp / "build/artai/s/logs").iterdir())
    assert "SECRET-KEY-123" not in everything.out + everything.err + logs


def test_gemini_model_override_and_reference_sent(in_tmp, stub, monkeypatch):
    monkeypatch.setenv("ARTAI_GEMINI_MODEL", "gemini-other")
    art_set, _ = load_manifest(yaml_set(in_tmp))
    reference = in_tmp / "ref.jpg"
    Image.new("RGB", (8, 8)).save(reference)
    get_backend("gemini", art_set).generate(job_for(art_set, reference=reference))
    body = stub.requests[0]["body"]
    assert body["model"] == "gemini-other"
    assert body["input"][1]["type"] == "image" and body["input"][1]["mime_type"] == "image/jpeg"
    assert base64.b64decode(body["input"][1]["data"]) == reference.read_bytes()


@pytest.mark.parametrize(
    ("reply", "error", "needle"),
    [
        ((429, {"error": {"message": "Resource exhausted"}}), QuotaExhausted, "429"),
        ((403, {"error": {"message": "Quota exceeded for project"}}), QuotaExhausted, "Quota"),
        ((500, {"error": {"message": "internal SECRET-KEY-123"}}), GenerationFailed, "internal ***"),
        ((200, {"output_text": "I can't draw that"}), GenerationFailed, "can't draw"),
        (
            (200, {"output_image": {"data": base64.b64encode(b"GIF89a....").decode()}}),
            GenerationFailed,
            "not a PNG",
        ),
        ((200, b"<html>oops"), GenerationFailed, "no image"),
    ],
)
def test_gemini_failures(in_tmp, stub, reply, error, needle):
    stub.reply = reply
    art_set, _ = load_manifest(yaml_set(in_tmp))
    with pytest.raises(error) as raised:
        get_backend("gemini", art_set).generate(job_for(art_set))
    assert needle in str(raised.value)
    assert "SECRET-KEY-123" not in str(raised.value)
    assert "SECRET-KEY-123" not in (art_set.logs_dir / "a.log").read_text()


def test_gemini_unreachable_is_failure(in_tmp, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("ARTAI_GEMINI_ENDPOINT", "http://127.0.0.1:9/none")
    art_set, _ = load_manifest(yaml_set(in_tmp))
    with pytest.raises(GenerationFailed, match="request failed"):
        get_backend("gemini", art_set).generate(job_for(art_set, timeout=3))


# ── Ctrl-C through the real CLI ─────────────────────────────────────────────


def test_ctrl_c_stops_quickly_and_releases_claims(in_tmp, fake):
    program, _ = fake
    manifest = yaml_set(in_tmp, f"{program} --out {{output}} {{prompt}}")
    env = {**os.environ, "FAKE_MODE": "sleep"}
    root = Path(__file__).resolve().parents[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "artai.cli", "generate", str(manifest), "--backend", "command"],
        cwd=in_tmp,
        env={**env, "PYTHONPATH": str(root / "src")},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    time.sleep(1.5)
    process.send_signal(signal.SIGINT)
    started = time.monotonic()
    _, err = process.communicate(timeout=20)
    assert time.monotonic() - started < 10
    assert process.returncode == 130 and "interrupted" in err
    assert not list((in_tmp / "build/artai/s/claims").glob("*.lock"))
