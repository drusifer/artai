# artai — Backlog

Ordered by Cypher after Sprint 1 retro (2026-10-20).

1. ~~**Migration sprint**~~ — done in Sprint 2 (2026-10-20): recard `a1c6fc5`, GlobalHeadsOrTails `35fb018`.
2. **Live provider samples** — one image each from codex, agy and gemini (Story OQ1); recard's sandboxed codex mode is still unproven live.
3. **Warn about missing reference images before a run** — today the item fails mid-run after quota was spent on others (Smith).
4. **Faster test loop** — mark the parity suite slow / add a quick target; it is ~35 s of 47 s on the Pi (Trin).
5. **Fixture refresh** — re-capture `tests/fixtures/` when consumer manifests change (Oracle).
6. **Non-POSIX support** — claims use `fcntl` and `/proc` (Morpheus; only if a Windows user appears).
7. **Quota reset time** — record the provider's reset time in the marker, as GHOT's quota report did (out of scope in Sprint 1).
8. **Release** — bump to 0.2.0 and tag once approved.
9. **Don't overwrite shipped art that has no master** — GlobalHeadsOrTails rangers: 92 packed vs 90 masters; `generate` would repaint the 2 and `pack` overwrite them. Option: `generate --skip-packed` or seed masters from packed files (Smith, Sprint 2).
10. **`artai pack` should skip placeholder masters** unless `--allow-mock` (GHOT Makefile works around it) (Morpheus, Sprint 2).
