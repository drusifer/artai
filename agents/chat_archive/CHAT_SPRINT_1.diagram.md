# CHAT_SPRINT_1 — Sprint Archive

## Summary

Sprint 1 built artai, one Python CLI that consolidates recard's imagegen and GlobalHeadsOrTails' art_generator (plus its deleted sticker_art/nanobanana tools). Tank wrote the SDLC; stories and arch each passed Smith on round 2 (output dirs/fit defaults; --backend required + tagged mock art). Five phases shipped manifests+prompts (273/273 GHOT parity), the resumable claim-based runner, codex/agy/gemini/command backends, pack/review/verify, regenerate/unlock and docs. UAT/review caught a Ctrl-C hang, a stale-claim race, phone overflow, ignored min_size and an exit-code collision; all fixed. 138 tests; version bump awaits owner.

---

## Planning

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Bob
    participant Oracle
    participant Mouse
    participant Tank
    participant Cypher
    participant Smith
    participant Morpheus
    participant Neo
    Note over User,Neo: 📅 2026-10-20
    User->>All: "request"
    Note right of User: "/init"
    Bob->>All: "ready"
    Note right of Bob: "Bob Protocol<br/>initialized. Team ready."
    User->>All: "request"
    Note right of User: "$sprint: consolidate art<br/>generation tooling from<br/>../recard and<br/>../GlobalHeadsAndTails<br/>into a new tool in artai"
    Oracle->>All: "research"
    Note right of Oracle: "Surveyed sources: recard<br/>tools/imagegen (Node, re<br/>sumable/quota/parallel,<br/>codex+agy), GHOT<br/>tools/art_generator.py<br/>(Python<br/>YAML/templates/aut…"
    Mouse->>Tank: "blocked"
    Note right of Mouse: "Sprint blocked:<br/>docs/SDLC.md is missing.<br/>@Tank *devops sdlc<br/>(needs language/runtime<br/>decision from user)"
    Tank->>All: "devops bootstrap"
    Note right of Tank: "Bootstrap choice:<br/>Python, pyproject.toml<br/>(PEP 621) + stdlib<br/>venv/pip in .venv (no<br/>existing lockfile, so<br/>convention), requires-<br/>python>=3.11,…"
    Tank->>Cypher: "devops handoff"
    Note right of Tank: "SDLC written:<br/>docs/SDLC.md.<br/>Python>=3.11,<br/>pyproject+venv/pip,<br/>targets install/test/lin<br/>t/format/run/clean/distc<br/>lean/help, verified<br/>distclean…"
    Smith->>Cypher: "user reject"
    Note right of Smith: "*user reject rubric<br/>STORIES: OUT=S TEST=W<br/>FAIL=A SCOPE=A SIZE=A<br/>DESIGN=A. Output<br/>location undefined for<br/>TSV/JSON + no default<br/>'fit', 'first…"
    Cypher->>Smith: "pm handoff"
    Note right of Cypher: "Stories revised per Gate<br/>1: output/work dir<br/>defaults + --work/--out<br/>(ART-1 AC7), default fit<br/>per manifest kind +<br/>--fit (ART-4 AC1), 'up<br/>to…"
    Smith->>Morpheus: "user approve"
    Note right of Smith: "*user approve. rubric<br/>STORIES: OUT=S TEST=A<br/>FAIL=S SCOPE=S SIZE=A<br/>DESIGN=A. Stories<br/>approved. @Morpheus<br/>*lead arch sprint"
    Smith->>Morpheus: "user reject"
    Note right of Smith: "*user reject rubric<br/>ARCH: BOUND=S FLOW=S<br/>FAIL=A USER=W DECS=S<br/>FEAS=S. Default<br/>--backend mock writes<br/>placeholder masters that<br/>resume then tr…"
    Morpheus->>Smith: "lead handoff"
    Note right of Morpheus: "Arch revised per Gate 2:<br/>--backend required (no<br/>default), mock masters<br/>tagged artai-<br/>placeholder, real runs<br/>replace them, status<br/>shows place…"
    Smith->>Mouse: "user approve"
    Note right of Smith: "*user approve. rubric<br/>ARCH: BOUND=S FLOW=S<br/>FAIL=S USER=A DECS=S<br/>FEAS=S. Architecture<br/>approved. @Mouse *sm<br/>plan sprint"
    Mouse->>Morpheus: "sm handoff"
    Note right of Mouse: "Sprint planned: 5 phases<br/>x 3 tasks in task.md (P1<br/>manifest/prompts/status+<br/>fixtures, P2 engine, P3<br/>providers, P4<br/>pack/review/verify, P5<br/>rege…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Plan review: phases<br/>follow arch dependency<br/>order (manifest→engine→p<br/>roviders→pack/verify→mai<br/>ntenance), each 2 impl<br/>tasks + gate, ACs<br/>mapped…"
```

---

## Phase 1

Phase 1: manifests, prompts, status + parity fixtures

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-20
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 1 impl complete:<br/>manifest.py<br/>(YAML/TSV/JSON,<br/>validation, defaults,<br/>overrides), prompts.py<br/>(GHOT parity: 273/273<br/>prompts identical), c…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 1 passed:<br/>ART-1 AC1-7 via real CLI<br/>(data_file, TSV+--style,<br/>status up-to-8 + '...<br/>and 74 more', bad TSV<br/>line 2 exit 1 nothing<br/>wri…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 1 review passed:<br/>matches ARCH §3/§5<br/>(manifest/prompts/model<br/>split, ManifestError<br/>before writes, cli exit<br/>codes). Nit fixed (top-<br/>level…"
```

---

## Phase 2

Phase 2: resumable generation engine (imaging, claims, backends base+mock, runner, generate CLI)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-20
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 2 impl complete:<br/>imaging (dimension<br/>validation, placeholder<br/>tag, atomic save),<br/>claims (link-based<br/>exclusive claims, /proc<br/>liveness, s…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 2: AC1-8 pass<br/>via CLI (36/36 mock,<br/>corrupt master<br/>regenerated, 2<br/>concurrent procs over<br/>143 items: 0 duplicates,<br/>0 leftover claims…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 2 review passed<br/>after fix: stale-claim<br/>takeover race (two<br/>takers could delete each<br/>other's new claim) now<br/>serialized by flock,<br/>20-rou…"
```

---

## Phase 3

Phase 3: real providers (command, codex, agy, gemini)

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-20
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 3 impl complete:<br/>command (shlex, per-argv<br/>substitution,<br/>cli_command alias),<br/>codex (workspace-write,<br/>cwd=masters), agy<br/>(scratch claim…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 3 passed:<br/>ART-2 AC9 + ART-3 AC1-6<br/>(tests + CLI with fake<br/>codex on fantasy-heroes:<br/>12 placeholders<br/>replaced, quota exit 2 +<br/>marker…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 3 review passed<br/>(security focus): no<br/>shell anywhere (argv<br/>lists, shlex per-token<br/>substitution, injection<br/>test), key only in<br/>header +…"
```

---

## Phase 4

Phase 4: pack, review, verify

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Neo
    participant Trin
    participant Morpheus
    Note over Neo,Morpheus: 📅 2026-10-20
    Neo->>Trin: "swe handoff"
    Note right of Neo: "Phase 4 impl complete:<br/>imaging fit_contain/fit_<br/>autocrop/save_as,<br/>pack.py, review.py<br/>(contact sheet, verify<br/>w/ size rule, sha256<br/>dupes, plac…"
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 4 passed:<br/>ART-4 AC1-5 + ART-5<br/>AC1-5 (twelve-clans:<br/>pack 512x512 webp,<br/>verify exit 1 listing<br/>missing/placeholder,<br/>--ids sample not…"
    Morpheus->>Neo: "lead handoff"
    Note right of Morpheus: "Phase 4 review passed:<br/>pack/review/verify match<br/>ARCH §4.2 (atomic<br/>writes, judged via<br/>master placeholder tag,<br/>size rule per fit).<br/>Committing…"
```

---

## Phase 5

Phase 5: regenerate/unlock, parity end-to-end, USAGE + MIGRATION docs

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant Trin
    participant Morpheus
    participant Tank
    participant Oracle
    participant Smith
    participant Neo
    participant All
    participant Cypher
    participant Mouse
    Note over Trin,Mouse: 📅 2026-10-20
    Trin->>Morpheus: "qa handoff"
    Note right of Trin: "UAT phase 5 passed:<br/>ART-6 AC1-4 + ART-7<br/>AC1-4, sprint UAT plan d<br/>ocs/sprints/UAT_PLAN_SPR<br/>INT1.md (all 7 stories<br/>pass). Fixed: manifest<br/>min_s…"
    Morpheus->>Tank: "lead handoff"
    Note right of Morpheus: "Phase 5 review passed:<br/>regenerate/unlock all-<br/>or-nothing per ARCH<br/>§4.3, docs match --help.<br/>rubric UAT: COVER=S<br/>STEPS=A FAIL=S DATA=S<br/>EVID=A.…"
    Tank->>Oracle: "devops handoff"
    Note right of Tank: "SDLC check passed: distc<br/>lean→install→test(136)→l<br/>int, imports declared<br/>(PIL, yaml), venv<br/>isolated, targets match,<br/>no side doors, ignores<br/>hol…"
    Oracle->>Smith: "ora handoff"
    Note right of Oracle: "Groomed: docs/LESSONS.md<br/>(3 lessons),<br/>DOCUMENTATION_INDEX<br/>project section. rubric<br/>SDLC: TRUE=S WHOLE=A<br/>CLEAN=S CLASS=A CHECK=S<br/>GAPS=S. rubr…"
    Smith->>Trin: "user bug"
    Note right of Smith: "*user bug CMD: artai<br/>genrate m.yaml / pack<br/>--format gif | EXPECTED:<br/>exit 1 | ACTUAL: exit 2<br/>(argparse) | UX ISSUE: 2<br/>is documented as quota…"
    Trin->>Neo: "qa triage"
    Note right of Trin: "Triage: confirmed, both<br/>in cli.py. Exit-code<br/>contract defect (sev:<br/>medium), hint is minor.<br/>@Neo *swe fix"
    Smith->>All: "user approve"
    Note right of Smith: "User testing passed<br/>(after fix 50406ec).<br/>rubric UAT: COVER=S<br/>STEPS=A FAIL=S DATA=S<br/>EVID=A. Lessons: claims-<br/>takeover WHEN=S WHAT=S<br/>RULE=S CA…"
    Neo->>Cypher: "retro"
    Note right of Neo: "Neo retro: TDD slipped<br/>in phase 3 (providers<br/>coded before tests),<br/>E501 churn from long<br/>strings. Backlog: none<br/>blocking."
    Trin->>Cypher: "retro"
    Note right of Trin: "Trin retro: 138 tests,<br/>instant fakes hid the<br/>Ctrl-C hang and<br/>identical-image case -<br/>fakes now vary. Parity<br/>suite takes ~35s of 47s<br/>on the P…"
    Morpheus->>Cypher: "retro"
    Note right of Morpheus: "Morpheus retro: two-<br/>stage masters/pack +<br/>claims held up, takeover<br/>race caught in review<br/>not tests. Revisit:<br/>Windows support<br/>(fcntll/proc),…"
    Oracle->>Cypher: "retro"
    Note right of Oracle: "Oracle retro: deleted<br/>GHOT tools only found<br/>via git history - now a<br/>lesson. MIGRATION had<br/>one wrong number (973 vs<br/>479 masters) caught by<br/>c…"
    Mouse->>Cypher: "retro"
    Note right of Mouse: "Mouse retro: 5 phases x<br/>3 tasks fit, 2 gate<br/>rejections (stories,<br/>arch) each fixed in one<br/>round, no anti-loop<br/>triggers. Velocity 24<br/>pts / 1…"
    Smith->>Cypher: "retro"
    Note right of Smith: "Smith retro: exit-code<br/>collision found only at<br/>close - add usage-error<br/>case to future AC<br/>templates. Backlog: warn<br/>before a run when<br/>referen…"
    Cypher->>Cypher: "retro"
    Note right of Cypher: "Cypher retro: stories<br/>held, ART-2 AC4 'retried<br/>up to N' read literally<br/>changed recard semantics<br/>(documented in<br/>MIGRATION). Backlog<br/>collecte…"
    Cypher->>All: "pm launch"
    Note right of Cypher: "*pm launch sprint-1.<br/>Sprint complete: artai<br/>CLI (8 commands, 5<br/>backends), 138 tests,<br/>docs. CHANGELOG +<br/>docs/BACKLOG.md written.<br/>Version bum…"
```
