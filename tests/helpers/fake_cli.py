"""Write a stand-in provider program (codex/agy/command) into a temp dir."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPT = r"""#!{python}
import json, os, re, sys, time
from pathlib import Path
from PIL import Image

argv = sys.argv[1:]
with open(os.environ["FAKE_RECORD"], "a") as f:
    f.write(json.dumps({{"argv": argv, "cwd": os.getcwd()}}) + "\n")
mode = os.environ.get("FAKE_MODE", "ok")
text = " ".join(argv)
match = re.search(r"(?:Save it to|exactly to|--out) (\S+?\.png)", text)
if mode == "quota":
    print("ERROR: You've hit your usage limit. Upgrade your plan.")
    sys.exit(1)
if mode == "fail":
    print("something broke")
    sys.exit(4)
if mode == "sleep":
    time.sleep(60)
if mode == "nothing":
    sys.exit(0)
if mode == "scratch":
    scratch = Path(os.environ["ARTAI_AGY_SCRATCH"])
    scratch.mkdir(parents=True, exist_ok=True)
    name = Path(match.group(1)).stem
    Image.new("RGB", (600, 600), "red").save(scratch / f"{{name}}_1.png")
    time.sleep(0.05)
    Image.new("RGB", (640, 640), "blue").save(scratch / f"{{name}}_2.png")
    sys.exit(0)
seed = sum(Path(match.group(1)).stem.encode())
Image.new("RGB", (700, 700), (seed % 256, (seed * 7) % 256, (seed * 13) % 256)).save(match.group(1))
"""


def make_fake(directory: Path, name: str = "fake") -> Path:
    path = directory / name
    path.write_text(SCRIPT.format(python=sys.executable))
    path.chmod(0o755)
    return path
