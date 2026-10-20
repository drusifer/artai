# CHAT.md — Conversation Flow

Auto-generated from `agents/CHAT.md` by `bobp chat-diagram`. Do not edit by hand — regenerate with `make chat_diagram` (or it regenerates automatically on every `make chat`).

```mermaid
%%{init: {"sequence": {"messageFontSize": 14, "noteFontSize": 18, "actorFontSize": 14}}}%%
sequenceDiagram
    autonumber
    participant User
    participant All
    participant Oracle
    participant Tank
    participant Bob
    Note over User,Bob: 📅 2026-10-20
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
```
