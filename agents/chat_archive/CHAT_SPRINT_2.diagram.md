# CHAT_SPRINT_2 — Sprint Archive

## Summary

Sprint 2 moved recard and GlobalHeadsOrTails onto artai, pip-installed editable from ../artai (recard .venv, GHOT .venv-art to avoid hijacking its workspace PYTHON). Existing masters were reused (132 recard, 36+90+37 GHOT), so no quota was spent; recard re-pack was byte-identical. GHOT's pre-existing work was committed first (434 MB tar excluded and ignored). Every old tool, test, doc and reference was removed from both repos (grep-verified), and artai's migration guide/survey with them; ADR-0006 records the install route. Nothing pushed.

---

## Planning

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    participant Tank
    participant Bob
    participant Cypher
    participant Smith
    participant Mouse
    participant Morpheus
    Note over User,Morpheus: 📅 2026-10-20
    User->>All: "request"
    Note right of User: "/oracle groom docs"
    Oracle->>Tank: "ora handoff"
    Note right of Oracle: "Groom done: ARCH +<br/>ADR-0004 synced to code,<br/>stories closed, README<br/>TOC, pip install<br/>documented (verified in<br/>fresh venv), 5 dead<br/>index links…"
    User->>All: "request"
    Note right of User: "go tank"
    Tank->>Oracle: "devops sdlc"
    Note right of Tank: "SDLC §7 updated: artai<br/>pip-installable from<br/>source (pip install<br/>/path/to/artai or<br/>git+url@tag), runtime<br/>deps only, verified in<br/>clean venv a…"
    User->>All: "request"
    Note right of User: "/oracle good now?"
    Oracle->>Tank: "ora review"
    Note right of Oracle: "rubric SDLC: TRUE=S<br/>WHOLE=A CLEAN=S CLASS=A<br/>CHECK=W GAPS=S. CHECK:<br/>item 5 forbids bare pip<br/>in docs, but §7 now<br/>documents 'pip install<br/>/path…"
    Tank->>Oracle: "devops sdlc"
    Note right of Tank: "SDLC item 5 rescoped<br/>(dev-only, §7 consumer<br/>pip lines allowed),<br/>check passes. @Oracle<br/>re-review"
    Oracle->>All: "ora review"
    Note right of Oracle: "Re-review: rubric SDLC:<br/>TRUE=S WHOLE=A CLEAN=S<br/>CLASS=A CHECK=A GAPS=S.<br/>Docs consistent: 0<br/>broken links, no stray<br/>rubrics, pip route in<br/>READ…"
    Bob->>All: "checkpoint"
    Note right of Bob: "Checkpoint saved in<br/>agents/bob/state.md.<br/>Sprint 1 done (384d3d7,<br/>not pushed). Next: ask<br/>owner re 0.2.0 release,<br/>live provider samples,<br/>migr…"
    User->>All: "request"
    Note right of User: "$sprint migrate recard<br/>and GlobalHeadsVsTails<br/>to use artai"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Sprint 2 doc ready (Tier<br/>2, story+arch): docs/spr<br/>ints/SPRINT2_MIGRATION.m<br/>d. @Smith *user review"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject rubric<br/>STORIES: OUT=S TEST=W<br/>FAIL=A SCOPE=S SIZE=A<br/>DESIGN=A. MIG-3 AC2 grep<br/>misses old target names<br/>(sticker-art-<br/>generate/pack…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "MIG-3 AC2 pattern<br/>extended to old sticker-<br/>art-*/sticker-production<br/>targets, STICKER_ART,<br/>rangers-reference-index,<br/>gallery excluded.<br/>@Smith…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. rubric<br/>STORIES: OUT=S TEST=A<br/>FAIL=A SCOPE=S SIZE=A<br/>DESIGN=A, rubric ARCH:<br/>BOUND=S FLOW=A FAIL=A<br/>USER=A DECS=A FEAS=S.<br/>@Mouse…"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint 2 planned: Phase<br/>0 (Tank: GHOT baseline +<br/>commit WIP), P1 recard,<br/>P2 GHOT, P3 artai<br/>cleanup. @Morpheus *lead<br/>review sprint plan"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "rubric PLAN: SIZE=A<br/>GATE=A VERIF=A ALIGN=S<br/>OWNER=A. Approved. @Tank<br/>phase 0"
```

---

## Phase 0

Phase 0: GHOT baseline + commit pre-existing work

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Tank
    participant Neo
    Note over Tank,Neo: 📅 2026-10-20
    Tank->>Neo: "devops handoff"
    Note right of Tank: "Phase 0 done: GHOT pre-<br/>existing work committed<br/>(149 files) except<br/>ntag424 dist (434MB tar)<br/>+ build, now gitignored<br/>(owner OK). Baseline:<br/>sh…"
```

---

## Phase 1

Phase 1: recard on artai

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Morpheus
    participant Neo
    Note over Morpheus,Neo: 📅 2026-10-20
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 (recard) done:<br/>art via artai, 132<br/>masters reused (0 codex<br/>calls), pack byte-<br/>identical, verify<br/>132/132, check-fast<br/>1267/1267, old to…"
```

---

## Phase 2

Phase 2: GlobalHeadsOrTails on artai

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Morpheus
    participant Oracle
    Note over Morpheus,Oracle: 📅 2026-10-20
    Morpheus->>Oracle: "lead handoff"
    Note right of Morpheus: "Phase 2 (GHOT) done: art<br/>via artai in .venv-art<br/>(root .venv would hijack<br/>PYTHON for all targets),<br/>masters reused, verify<br/>36/36, mock never…"
```

---

## Phase 3

Phase 3: artai doc cleanup + ADR-0006

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Oracle
    participant Tank
    participant Smith
    participant All
    participant Mouse
    participant Cypher
    Note over Oracle,Cypher: 📅 2026-10-20
    Oracle->>Tank: "ora handoff"
    Note right of Oracle: "Phase 3 done: artai<br/>MIGRATION.md + survey<br/>deleted, refs updated,<br/>ADR-0006, CHANGELOG,<br/>SDLC §7 consumers<br/>(Tank). rubric DECISION<br/>ADR-0006: C…"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed (docs-<br/>only artai change,<br/>consumers verified from<br/>clean). @Oracle *ora<br/>groom"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Groomed: 2 lessons (venv<br/>auto-detect trap, dry-<br/>run before committing<br/>others' trees). @Smith<br/>*user test sprint-2"
    Smith->>All: "user approve"
    Note right of Smith: "User testing passed<br/>(recard + GHOT via their<br/>own docs, 0 codex calls,<br/>clear errors). Note:<br/>rangers 92 packed vs 90<br/>masters - art-generate<br/>w…"
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Retro (team): Neo -<br/>Makefile-only migration,<br/>byte-identical recard<br/>pack. Trin - baseline-<br/>first made GHOT's pre-<br/>broken suites provable.<br/>Morp…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-2.<br/>recard +<br/>GlobalHeadsOrTails run<br/>on artai, old<br/>tools/docs/refs gone in<br/>both, no quota spent.<br/>Commits: recard a1c6fc5<br/>(d…"
```
