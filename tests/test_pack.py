import pytest
from PIL import Image

from artai.cli import main
from artai.imaging import save_png
from artai.manifest import load_manifest
from artai.pack import pack
from tests.conftest import write


def master(art_set, item_id, size=(1024, 1536), colour="navy", background=None):
    image = Image.new("RGB", size, background or colour)
    if background:  # a subject in the middle of a plain background
        w, h = size
        image.paste(Image.new("RGB", (w // 4, h // 2), colour), (w // 2 - w // 8, h // 4))
    save_png(image, art_set.masters_dir / f"{item_id}.png")


@pytest.fixture
def tsv(in_tmp):
    return load_manifest(write(in_tmp / "j.tsv", "a\tA\nb\tB\nc\tC\n"))


def test_contain_preserves_aspect(tsv):
    art_set, items = tsv
    master(art_set, "a", (1024, 1536))
    summary = pack(art_set, items)
    assert (summary.packed, summary.total, summary.skipped) == (1, 1, [])
    with Image.open(art_set.output_dir / "a.webp") as image:
        assert image.size == (341, 512) and image.format == "WEBP"


def test_autocrop_centres_subject_on_exact_canvas(in_tmp):
    path = write(
        in_tmp / "m.yaml",
        "artwork_set: {name: s, resolution: [300, 200], pad: 10}\nitems: [{id: a, prompt: p}]",
    )
    art_set, items = load_manifest(path)
    master(art_set, "a", (800, 800), colour=(200, 0, 0), background=(250, 250, 240))
    pack(art_set, items)
    with Image.open(art_set.output_dir / "a.webp") as image:
        assert image.size == (300, 200)
        rgb = image.convert("RGB")
        corner, centre = rgb.getpixel((2, 2)), rgb.getpixel((150, 100))
    assert all(abs(c - e) < 12 for c, e in zip(corner, (250, 250, 240), strict=True))
    assert centre[0] > 150 and centre[1] < 60
    # subject (a 1:2 box) scaled to fill the 180px available height
    column = [rgb.getpixel((150, y))[1] < 100 for y in range(200)]
    assert column.index(True) <= 12 and 200 - column[::-1].index(True) >= 188


@pytest.mark.parametrize(("fmt", "pil"), [("png", "PNG"), ("jpeg", "JPEG"), ("webp", "WEBP")])
def test_format_override_and_names(tsv, fmt, pil):
    art_set, items = tsv
    master(art_set, "b", (600, 600))
    from dataclasses import replace

    pack(replace(art_set, format=fmt, quality=70), items)
    with Image.open(art_set.output_dir / f"b.{fmt}") as image:
        assert image.format == pil


def test_output_filename_honoured(in_tmp):
    text = "artwork_set: {name: s}\nitems: [{id: a, prompt: p, output_filename: hero.webp}]"
    art_set, items = load_manifest(write(in_tmp / "m.yaml", text))
    master(art_set, "a", (600, 600))
    pack(art_set, items)
    assert (art_set.output_dir / "hero.webp").is_file()


def test_unopenable_master_skipped_and_old_output_kept(tsv):
    art_set, items = tsv
    master(art_set, "a", (600, 600))
    art_set.masters_dir.joinpath("b.png").write_bytes(b"\x89PNG garbage")
    art_set.output_dir.mkdir(parents=True)
    (art_set.output_dir / "b.webp").write_bytes(b"previous good output")
    summary = pack(art_set, items)
    assert (summary.packed, summary.total, summary.skipped) == (1, 2, ["b"])
    assert (art_set.output_dir / "b.webp").read_bytes() == b"previous good output"
    assert not [p for p in art_set.output_dir.iterdir() if p.name.startswith(".")]


def test_pack_cli_exit_codes_and_overrides(tsv, in_tmp, capsys):
    art_set, _ = tsv
    master(art_set, "a", (900, 600))
    manifest = str(in_tmp / "j.tsv")
    assert main(["pack", manifest, "--size", "300", "--format", "png"]) == 0
    assert "packed 1/1" in capsys.readouterr().out
    with Image.open(art_set.output_dir / "a.png") as image:
        assert image.size == (300, 200)
    art_set.masters_dir.joinpath("c.png").write_bytes(b"bad")
    assert main(["pack", manifest]) == 1
    out = capsys.readouterr().out
    assert "packed 1/2" in out and "c" in out


def test_pack_cli_bad_quality(tsv, in_tmp, capsys):
    assert main(["pack", str(in_tmp / "j.tsv"), "--quality", "500"]) == 1
    assert "--quality" in capsys.readouterr().err
