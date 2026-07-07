---
name: init
description: One-time fast priming — cache the whole Praxis plugin + the active domain pack into Claude's persistent memory, so future sessions operate as a fluent domain-expert co-scientist without re-reading. Takes a few minutes, mostly local reads.
---

Prime Praxis as a domain-expert co-scientist. Target pack: **$ARGUMENTS** (if empty, resolve the active pack).

This is the ONE first-run step. It is fast (mostly local file reads + formatting) and one-time — afterward the briefing is recalled as background context every session, so you route the scientific-method loop as a fluent expert without re-reading the plugin. Core works without it; this makes it an *expert*.

1. **Resolve the pack.** Run `python lib/pack_resolver.py list`. If `$ARGUMENTS` names an installed pack, use it. If exactly one pack is installed, use it. If two or more and no argument, ask which domain to prime (or prime each in turn). If zero packs are installed, tell the user Praxis will run as a **generalist** co-scientist (no domain briefing) and stop after writing only `praxis-method.md`.

2. **Gather the briefing (deterministic, zero tokens).** Run `python lib/memory_prime.py <id>`. It prints two blocks delimited by `=== WRITE MEMORY FILE: <name> ===` / `=== END <name> ===`:
   - `praxis-method.md` — the loop, triage tiers, the roles, the integrity non-negotiables (domain-agnostic; write once, reuse across packs).
   - `praxis-domain-<id>.md` — this pack's conventions, scope traps, skeptic threats, measured/inferred/speculative split, the `pcache.py` data cheat-sheet, and the landmark SOTA DOIs.

3. **Write the briefing into your persistent memory.** For each printed block, write its body **verbatim** to a file of that name in your memory directory (the one your system prompt describes, where `MEMORY.md` lives) using the Write tool. Then add one pointer line per file to `MEMORY.md` (e.g. `- [Praxis method](praxis-method.md) — the loop, roles, integrity rules` and `- [Praxis · <title>](praxis-domain-<id>.md) — primed as a <title> co-scientist`). Do not duplicate an existing entry — update it if present.

4. **Mark the pack active.** Write the pack id to `.praxis/active` (create the `.praxis/` dir in the repo/working root if needed) and write a `.praxis/primed` marker file containing the pack id and the current UTC timestamp.

5. **Report.** Print a one-paragraph summary: *"Praxis is now primed as a `<title>` co-scientist (tier `<TIER>`). Tier-0 lookups serve from `<cache>` via `lib/pcache.py`; deep questions run the full loop with `domain-expert-<id>`. Scope trap in force: `<one-line scope_trap>`."* Offer `/quick`, `/investigate`, and (for lvk) `/event` as next steps.

Integrity: everything written comes from the plugin's own files and the pack's provenance-stamped cache/sota — nothing is recalled or invented. The briefing is a compact index into retrieved material, not a substitute for retrieval; Tier-0 answers still run `pcache.py`, and deep answers still retrieve live.
