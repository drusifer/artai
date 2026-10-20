import json

from artai.cli import main
from tests.conftest import write

YAML = """
artwork_set: {name: demo, style: inked}
items:
  - {id: a, prompt: Apple}
  - {id: b, prompt_template: 'Bee {colour}'}
"""


def test_prompts_prints_id_tab_prompt(in_tmp, capsys):
    assert main(["prompts", str(write(in_tmp / "m.yaml", YAML))]) == 0
    out, err = capsys.readouterr()
    assert out.splitlines() == ["a\tApple inked", "b\tBee {colour}"]
    assert "warning: b: no value for placeholder {colour}" in err


def test_prompts_json(in_tmp, capsys):
    assert main(["prompts", "--json", str(write(in_tmp / "m.yaml", YAML))]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0] == {"id": "a", "filename": "a.webp", "prompt": "Apple inked", "metadata": {}}


def test_status_counts_and_missing_list(in_tmp, capsys):
    items = "\n".join(f"  - {{id: i{n:02d}, prompt: p}}" for n in range(12))
    path = write(in_tmp / "m.yaml", f"artwork_set: {{name: big}}\nitems:\n{items}\n")
    out_dir = in_tmp / "build/artai/big/out"
    out_dir.mkdir(parents=True)
    (out_dir / "i00.webp").write_bytes(b"x")
    (out_dir / "i01.webp").write_bytes(b"x")
    assert main(["status", str(path)]) == 0
    out = capsys.readouterr().out
    assert "set:          big" in out
    assert "items:        12" in out
    assert "packed:       2" in out
    assert "missing:      10" in out
    assert "  i02" in out and "  i09" in out and "  i10" not in out
    assert "... and 2 more" in out


def test_bad_manifest_exit_1_message(in_tmp, capsys):
    text = "artwork_set: {name: x}\nitems: [{id: a, prompt: p}, {id: a, prompt: q}]\n"
    path = write(in_tmp / "dup.yaml", text)
    assert main(["status", str(path)]) == 1
    err = capsys.readouterr().err
    assert err.startswith("artai: ") and "dup.yaml" in err and "Traceback" not in err


def test_tsv_with_out_override(in_tmp, capsys):
    path = write(in_tmp / "j.tsv", "a\tApple\n")
    assert main(["status", "--out", "packed", str(path)]) == 0
    assert str(in_tmp / "packed") in capsys.readouterr().out


def test_no_command_prints_usage(capsys):
    assert main([]) == 1


def test_usage_errors_exit_1_not_quota_code(in_tmp, capsys):
    path = str(write(in_tmp / "m.yaml", YAML))
    assert main(["genrate", path]) == 1
    assert main(["pack", path, "--format", "gif"]) == 1
    assert main(["--help"]) == 0
