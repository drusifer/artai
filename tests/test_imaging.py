from PIL import Image

from artai.imaging import is_placeholder, is_valid, save_png


def test_is_valid_by_dimensions_not_bytes(tmp_path):
    small_bytes = tmp_path / "flat.png"
    save_png(Image.new("RGB", (800, 600), "white"), small_bytes)  # compresses to a few hundred bytes
    assert small_bytes.stat().st_size < 5000
    assert is_valid(small_bytes, 512)
    assert not is_valid(small_bytes, 700)


def test_is_valid_rejects_missing_and_corrupt(tmp_path):
    assert not is_valid(tmp_path / "nope.png", 1)
    (tmp_path / "junk.png").write_bytes(b"not a png")
    assert not is_valid(tmp_path / "junk.png", 1)


def test_placeholder_tag_round_trip(tmp_path):
    save_png(Image.new("RGB", (10, 10)), tmp_path / "p.png", placeholder="mock")
    save_png(Image.new("RGB", (10, 10)), tmp_path / "r.png")
    assert is_placeholder(tmp_path / "p.png")
    assert not is_placeholder(tmp_path / "r.png")
    assert not is_placeholder(tmp_path / "missing.png")


def test_save_is_atomic_no_temp_left(tmp_path):
    save_png(Image.new("RGB", (10, 10)), tmp_path / "sub/a.png")
    assert [p.name for p in (tmp_path / "sub").iterdir()] == ["a.png"]
