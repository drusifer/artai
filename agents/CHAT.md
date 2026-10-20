# Chat Message Template:

Agents **must** use this for every message posted to CHAT.md:


> ## [{msg_num}]: From: @{AgentName}, Subject: {Subject}
> 
> {TLDR(LastStep)};
> 
> ### Request: { An '@' or '*' targeted command  for a specic purpose like 'perform this task Y' or 'help me with X}

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_1.md` (2026-10-20 14:47:47) — Sprint 1 built artai, one Python CLI that consolidates recard's imagegen and GlobalHeadsOrTails' art_generator (plus its deleted sticker_art/nanobanana tools). Tank wrote the SDLC; stories and arch each passed Smith on round 2 (output dirs/fit defaults; --backend required + tagged mock art). Five phases shipped manifests+prompts (273/273 GHOT parity), the resumable claim-based runner, codex/agy/gemini/command backends, pack/review/verify, regenerate/unlock and docs. UAT/review caught a Ctrl-C hang, a stale-claim race, phone overflow, ignored min_size and an exit-code collision; all fixed. 138 tests; version bump awaits owner.

---

> **Previous sprint archived:** `agents/chat_archive/CHAT_SPRINT_2.md` (2026-10-20 15:43:31) — Sprint 2 moved recard and GlobalHeadsOrTails onto artai, pip-installed editable from ../artai (recard .venv, GHOT .venv-art to avoid hijacking its workspace PYTHON). Existing masters were reused (132 recard, 36+90+37 GHOT), so no quota was spent; recard re-pack was byte-identical. GHOT's pre-existing work was committed first (434 MB tar excluded and ignored). Every old tool, test, doc and reference was removed from both repos (grep-verified), and artai's migration guide/survey with them; ADR-0006 records the install route. Nothing pushed.

---
