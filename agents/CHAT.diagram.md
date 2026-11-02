# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `bobp chat-diagram` (or it regenerates automatically on every `bobp chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Morpheus
    participant Neo
    participant Trin
    participant Tank
    Note over User,Tank: 📅 2026-10-20
    User->>All: "request"
    Note right of User: "*nit make art-gen should<br/>not regenerate files<br/>that already exist<br/>(--force to overwrite)"
    Morpheus->>Neo: "lead decide"
    Note right of Morpheus: "*impl: generate skips<br/>items with a valid<br/>master OR packed image<br/>(fresh clones have<br/>packed but no masters),<br/>pack skips up-to-date<br/>outputs, -…"
    Trin->>All: "qa uat"
    Note right of Trin: "*nit done: generate<br/>skips items with master<br/>OR packed art, pack<br/>skips up-to-date,<br/>--force/FORCE=1 to redo.<br/>UAT: recard fresh clone<br/>0 codex…"
    Note over User,Tank: 📅 2026-11-02
    User->>All: "request"
    Note right of User: "/init bring up tank"
    Tank->>All: "init"
    Note right of Tank: "Activating persona Tank<br/>via harness invocation."
    Tank->>All: "ready"
    Note right of Tank: "Tank online. SDLC<br/>verified at sprint 2<br/>close, no active task.<br/>Pending: release tag<br/>once owner approves<br/>0.2.0. Ready for *devops<br/>commands. W…"
    Tank->>All: "devops"
    Note right of Tank: "Added make build (python<br/>-m build + twine check)<br/>and make release (tag,<br/>push, gh release -> .git<br/>hub/workflows/release.ym<br/>l, PyPI trusted pub…"
```
