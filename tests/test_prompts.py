import json

import pytest

from artai.manifest import load_manifest
from artai.prompts import render
from tests.conftest import write

GHOT = [
    "twelve-clans/manifest",
    "fantasy-heroes/manifest",
    "rangers-history/manifest",
    "rangers-history/champions",
]


@pytest.mark.parametrize("stem", GHOT)
def test_parity_with_ghot_export_prompts(fixtures, in_tmp, stem):
    expected_file = fixtures / "ghot" / f"{stem.replace('/', '__')}.expected_prompts.json"
    expected = json.loads(expected_file.read_text())
    _, items = load_manifest(fixtures / "ghot" / f"{stem}.yaml")
    art_set, _ = load_manifest(fixtures / "ghot" / f"{stem}.yaml")
    got = [{"id": i.id, "resolved_prompt": render(art_set, i).prompt} for i in items]
    assert got == [{"id": e["id"], "resolved_prompt": e["resolved_prompt"]} for e in expected]


def _one(in_tmp, set_yaml, item_yaml):
    text = f"artwork_set: {set_yaml}\nitems: [{item_yaml}]\n"
    art_set, items = load_manifest(write(in_tmp / "m.yaml", text))
    return render(art_set, items[0])


def test_metadata_and_set_tokens(in_tmp):
    item = "{id: a, prompt_template: '{name} in {set_name}. {style}', metadata: {name: Ann}}"
    result = _one(in_tmp, "{name: s, style: inked}", item)
    assert result.prompt == "Ann in s. inked"
    assert result.missing == []


def test_plain_prompt_appends_theme_and_style(in_tmp):
    result = _one(in_tmp, "{name: s, theme: Night, style: inked}", "{id: a, prompt: A cat}")
    assert result.prompt == "A cat Night inked"


def test_unknown_placeholder_kept_and_reported(in_tmp):
    result = _one(in_tmp, "{name: s}", "{id: a, prompt_template: 'Wearing {jersey}'}")
    assert result.prompt == "Wearing {jersey}"
    assert result.missing == ["jersey"]


def test_list_manifest_appends_cli_style(in_tmp):
    art_set, items = load_manifest(write(in_tmp / "j.tsv", "a\tA swamp\n"), style="oil, no text")
    assert render(art_set, items[0]).prompt == "A swamp oil, no text"
