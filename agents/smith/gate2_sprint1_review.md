# Gate 2 — Sprint 1 architecture review (Smith, 2026-10-20)

Round 1 verdict: `rubric ARCH: BOUND=S FLOW=S FAIL=A USER=W DECS=S FEAS=S` → **REJECT**

1. USER (W): `--backend mock` as the default is safe for quota but unsafe for the art. An operator who
   forgets `--backend codex` gets 1,000 coloured rectangles written as *valid masters*; resume then
   skips those items forever on the real run, and `pack`/`verify` would ship and pass them. The
   predecessor explicitly forbade counting placeholders ("no placeholders ... counted"). FIX: make
   `--backend` required for `generate`/`regenerate` (no default, message lists the choices); tag
   mock masters (PNG text chunk) so a real-backend run treats them as missing; `status` counts them
   separately; `verify` fails on placeholder art unless `--allow-mock` is given.
2. USER (note, not blocking): document `status` output so "packed" vs "masters" is unambiguous.

Round 2 verdict: `rubric ARCH: BOUND=S FLOW=S FAIL=S USER=A DECS=S FEAS=S` → **APPROVE**. Placeholder rule closes the gap; status lines now named.
