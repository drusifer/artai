# Gate 1 — Sprint 1 stories review (Smith, 2026-10-20)

Round 1 verdict: `rubric STORIES: OUT=S TEST=W FAIL=A SCOPE=A SIZE=A DESIGN=A` → **REJECT**

1. TEST (W): STORY-ART-4 gives no default when a manifest omits `fit`, and STORY-ART-1 AC2 lets TSV/JSON
   lists (which carry no `output_dir`) be used by every command without saying where masters and packed
   files go. A tester cannot predict the output location. FIX: state defaults — `fit` defaults to
   `autocrop` for YAML sets (GHOT behaviour) and `contain` for TSV/JSON lists (recard behaviour);
   `--work`/`--out` options with stated defaults.
2. TEST (W): STORY-ART-1 AC4 "the first missing ids" has no count. FIX: "up to 8".
3. SCOPE: STORY-ART-7 lists three GHOT manifests; there is a fourth, `rangers-history/champions.yaml`.
   `rangers-history/cards.json` has 143 records (not 1,162), so Open Question 2 is moot — keep all.

Round 2 verdict: `rubric STORIES: OUT=S TEST=A FAIL=S SCOPE=S SIZE=A DESIGN=A` → **APPROVE**. All three findings fixed; failure ACs name message, exit code and state left behind.
