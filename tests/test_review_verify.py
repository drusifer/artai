import shutil

import pytest
from PIL import Image

from artai.cli import main
from artai.imaging import save_png
from artai.manifest import load_manifest
from artai.pack import pack
from artai.review import build_contact_sheet, verify
from tests.conftest import write

YAML = """
artwork_set: {name: s, description: "Demo <set>"}
items:
  - {id: a, prompt: 'Fox <b>bold</b>', metadata: {name: Foxy, clan: Red}}
  - {id: b, prompt: Bee}
  - {id: c, prompt: Cat}
"""


@pytest.fixture
def setup(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "m.yaml", YAML))
    for n, item in enumerate(items[:2]):
        save_png(Image.new("RGB", (800, 800), (n * 90, 40, 200)), item.master(art_set))
    pack(art_set, items)
    return art_set, items


def test_contact_sheet_content(setup):
    art_set, items = setup
    page = build_contact_sheet(art_set, items)
    assert page == art_set.review_dir / "contact_sheet.html"
    html = page.read_text()
    assert html.count('class="art-card') == 3
    assert "../out/a.webp" in html  # relative, opens from disk
    assert "Fox &lt;b&gt;bold&lt;/b&gt;" in html and "<b>bold</b>" not in html
    assert "Demo &lt;set&gt;" in html
    assert "Foxy" in html and "clan" in html
    assert "missing" in html.lower() and 'type="search"' in html
    assert "2 of 3" in html


def test_review_cli_prints_path(setup, capsys, in_tmp):
    assert main(["review", str(in_tmp / "m.yaml")]) == 0
    assert "contact_sheet.html" in capsys.readouterr().out


def test_verify_reports_missing(setup):
    art_set, items = setup
    report = verify(art_set, items)
    assert not report.ok
    assert report.problems == [("c", "no packed image")]


def test_verify_passes_when_complete(setup):
    art_set, items = setup
    save_png(Image.new("RGB", (800, 800), "teal"), items[2].master(art_set))
    pack(art_set, items)
    report = verify(art_set, items)
    assert report.ok and report.checked == 3


def test_verify_wrong_size_and_duplicates(setup):
    art_set, items = setup
    save_png(Image.new("RGB", (800, 800), "teal"), items[2].master(art_set))
    pack(art_set, items)
    Image.new("RGB", (100, 100)).save(art_set.output_dir / "c.webp")
    shutil.copy(art_set.output_dir / "a.webp", art_set.output_dir / "b.webp")
    report = verify(art_set, items)
    assert ("c", "is 100x100, expected 512x512") in report.problems
    assert report.duplicates == [("a", "b")]
    assert not report.ok


def test_verify_rejects_placeholder_art_unless_allowed(in_tmp, capsys):
    manifest = str(write(in_tmp / "m.yaml", "artwork_set: {name: s}\nitems: [{id: a, prompt: p}]"))
    assert main(["generate", manifest, "--backend", "mock"]) == 0
    assert main(["pack", manifest]) == 0
    capsys.readouterr()
    assert main(["verify", manifest]) == 1
    assert "a: placeholder art (mock)" in capsys.readouterr().out
    assert main(["verify", manifest, "--allow-mock"]) == 0


def test_verify_cli_sample_notice_and_unknown_ids(setup, capsys, in_tmp):
    manifest = str(in_tmp / "m.yaml")
    assert main(["verify", manifest, "--ids", "a"]) == 0
    out = capsys.readouterr().out
    assert "selected sample only" in out and "cannot show the set is complete" in out
    assert main(["verify", manifest, "--ids", "zz"]) == 1


def test_verify_contain_size_rule(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "j.tsv", "a\tA\n"))
    save_png(Image.new("RGB", (1024, 1536)), items[0].master(art_set))
    pack(art_set, items)
    assert verify(art_set, items).ok
    Image.new("RGB", (300, 200)).save(items[0].packed(art_set))
    assert verify(art_set, items).problems == [("a", "is 300x200, expected longest edge 512")]


def test_long_metadata_goes_into_details(in_tmp):
    text = (
        "artwork_set: {name: s}\nitems: [{id: a, prompt: p, metadata: {lore: '"
        + "x" * 80
        + "', tier: gold}}]"
    )
    art_set, items = load_manifest(write(in_tmp / "m.yaml", text))
    html = build_contact_sheet(art_set, items).read_text()
    assert "<span><b>tier</b>: gold</span>" in html
    assert "<dt>lore</dt><dd>" + "x" * 80 in html
