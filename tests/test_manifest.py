import json
from pathlib import Path

import pytest

from artai.errors import ManifestError
from artai.manifest import load_manifest
from tests.conftest import write

YAML_INLINE = """
artwork_set:
  name: demo
  theme: Dark forest
  style: oil painting
items:
  - id: fox-1
    prompt: A red fox
    metadata: {name: Fox}
  - id: owl-1
    prompt_template: "{name} on a branch. {style}"
    metadata: {name: Owl}
"""


def test_yaml_inline_items(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "m.yaml", YAML_INLINE))
    assert art_set.name == "demo" and art_set.kind == "yaml"
    assert [i.id for i in items] == ["fox-1", "owl-1"]
    assert items[0].metadata == {"name": "Fox"}


def test_yaml_defaults(in_tmp):
    art_set, _ = load_manifest(write(in_tmp / "m.yaml", YAML_INLINE))
    assert art_set.work_dir == (in_tmp / "build/artai/demo").resolve()
    assert art_set.output_dir == (in_tmp / "build/artai/demo/out").resolve()
    assert art_set.review_dir == art_set.work_dir / "review"
    assert art_set.fit == "autocrop"
    assert art_set.resolution == (512, 512)
    assert (art_set.format, art_set.quality, art_set.pad, art_set.min_size) == ("webp", 92, 10, 512)


def test_yaml_autocrop_false_maps_to_contain(in_tmp):
    text = "artwork_set: {name: x, autocrop: false}\nitems: [{id: a, prompt: p}]\n"
    art_set, _ = load_manifest(write(in_tmp / "m.yaml", text))
    assert art_set.fit == "contain"


def test_yaml_explicit_fit_and_resolution_string(in_tmp):
    text = "artwork_set: {name: x, fit: contain, resolution: 640x480, size: 300}\nitems: [{id: a, prompt: p}]"
    art_set, _ = load_manifest(write(in_tmp / "m.yaml", text))
    assert (art_set.fit, art_set.resolution, art_set.size) == ("contain", (640, 480), 300)


def test_yaml_data_file_with_item_template(in_tmp):
    write(
        in_tmp / "set/cards.json",
        json.dumps(
            [
                {"id": "a-1", "name": "Ann", "level": 1},
                {"id": "a-2", "name": "Bo", "level": 2, "prompt_template": "Custom {name}"},
            ]
        ),
    )
    write(
        in_tmp / "set/m.yaml",
        "artwork_set: {name: s}\ndata_file: cards.json\n"
        "item_template: {prompt_template: '{name} level {level}'}\n",
    )
    _, items = load_manifest(in_tmp / "set/m.yaml")
    assert items[0].prompt_template == "{name} level {level}"
    assert items[0].metadata["level"] == 1
    assert items[1].prompt_template == "Custom {name}"


def test_data_file_dict_with_items_key(in_tmp):
    write(in_tmp / "d.json", json.dumps({"items": [{"id": "z", "prompt": "zed"}]}))
    write(in_tmp / "m.yaml", "artwork_set: {name: s}\ndata_file: d.json\nitem_template: '{prompt}'\n")
    _, items = load_manifest(in_tmp / "m.yaml")
    assert [i.id for i in items] == ["z"]


def test_reference_image_resolved_against_manifest_dir(in_tmp):
    text = "artwork_set: {name: s}\nitems: [{id: a, prompt: p, reference_image: refs/a.png}]\n"
    write(in_tmp / "set/m.yaml", text)
    _, items = load_manifest(in_tmp / "set/m.yaml")
    assert items[0].reference_image == (in_tmp / "set/refs/a.png").resolve()


def test_tsv_manifest(in_tmp):
    path = write(in_tmp / "jobs.tsv", "# comment\n\nrtg-1\tA swamp\twith a tab\nrtg-2\tA hill\n")
    art_set, items = load_manifest(path)
    assert art_set.kind == "list" and art_set.name == "jobs"
    assert [(i.id, i.prompt) for i in items] == [("rtg-1", "A swamp\twith a tab"), ("rtg-2", "A hill")]
    assert art_set.work_dir == (in_tmp / "build/artai/jobs").resolve()
    assert art_set.output_dir == art_set.work_dir / "out"
    assert (art_set.fit, art_set.size, art_set.quality) == ("contain", 512, 88)


def test_json_list_manifest_and_style_override(in_tmp):
    path = write(in_tmp / "jobs.json", json.dumps([{"id": "a", "prompt": "Apple"}]))
    art_set, items = load_manifest(path, style="watercolour")
    assert art_set.style == "watercolour" and items[0].prompt == "Apple"


def test_overrides(in_tmp):
    art_set, _ = load_manifest(write(in_tmp / "m.yaml", YAML_INLINE), work="w", out="o", fit="contain")
    assert art_set.work_dir == (in_tmp / "w").resolve()
    assert art_set.output_dir == (in_tmp / "o").resolve()
    assert art_set.fit == "contain"


@pytest.mark.parametrize(
    ("name", "text", "needle"),
    [
        (
            "dup.yaml",
            "artwork_set: {name: x}\nitems: [{id: a, prompt: p}, {id: a, prompt: q}]",
            "duplicate id",
        ),
        ("unsafe.yaml", "artwork_set: {name: x}\nitems: [{id: ../evil, prompt: p}]\n", 'unsafe id "../evil"'),
        ("noid.yaml", "artwork_set: {name: x}\nitems: [{prompt: p}]\n", "item 1: missing id"),
        ("bad.yaml", "artwork_set: [unclosed\n", "not valid YAML"),
        ("nodata.yaml", "artwork_set: {name: x}\ndata_file: gone.json\n", "gone.json"),
        ("bad.tsv", "ok\tfine\nno-tab-here\n", "line 2"),
        ("dup.tsv", "a\tone\na\ttwo\n", 'duplicate id "a"'),
        ("bad.json", '{"id": "a"}', "JSON list"),
        ("noprompt.json", '[{"id": "a"}]', "entry 1: missing prompt"),
        ("bad.fit.yaml", "artwork_set: {name: x, fit: squash}\nitems: [{id: a, prompt: p}]\n", "fit"),
    ],
)
def test_invalid_manifests_name_file_and_problem(in_tmp, name, text, needle):
    path = write(in_tmp / name, text)
    with pytest.raises(ManifestError) as err:
        load_manifest(path)
    assert needle in str(err.value)
    assert name in str(err.value)
    assert not (in_tmp / "build").exists()


def test_missing_manifest_file(in_tmp):
    with pytest.raises(ManifestError, match="not found"):
        load_manifest(Path("nope.yaml"))


def test_unknown_extension(in_tmp):
    with pytest.raises(ManifestError, match="unsupported"):
        load_manifest(write(in_tmp / "m.csv", "a,b\n"))
