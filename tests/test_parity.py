"""STORY-ART-7: both projects' current art inputs run through the whole artai pipeline unchanged."""

import json

import pytest

from artai.cli import main

CASES = [
    ("ghot/twelve-clans/manifest.yaml", 36),
    ("ghot/fantasy-heroes/manifest.yaml", 12),
    ("ghot/rangers-history/manifest.yaml", 143),
    ("ghot/rangers-history/champions.yaml", 82),
    ("recard/rtg_jobs.tsv", 12),
    ("recard/rtg_jobs.json", 6),
]


@pytest.mark.parametrize(("fixture", "count"), CASES, ids=[c[0] for c in CASES])
def test_parity_full_pipeline(fixtures, in_tmp, capsys, fixture, count):
    manifest = str(fixtures / fixture)
    style = ["--style", "high fantasy oil painting, no text"] if fixture.startswith("recard") else []
    steps = [
        ["status", manifest],
        ["prompts", "--json", manifest, *style],
        ["generate", manifest, "--backend", "mock", "--parallel", "8", *style],
        ["pack", manifest],
        ["review", manifest],
        ["verify", manifest, "--allow-mock"],
    ]
    for step in steps:
        assert main(step) == 0, step
        out = capsys.readouterr().out
        if step[0] == "prompts":
            assert len(json.loads(out)) == count
        if step[0] == "verify":
            assert f"{count}/{count} verified" in out
    assert main(["verify", manifest]) == 1  # placeholder art never passes the real gate
