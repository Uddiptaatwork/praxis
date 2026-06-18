---
name: quick
description: Fast, cited GWOSC lookup — one event's parameters, a catalog count, or a superlative — answered from the local snapshot with no heavy loop.
---

Answer quickly and directly: **$ARGUMENTS**

This is a Tier-0 lookup (see the `scientific-method` skill's triage). Do NOT run the scientific-method loop, convene subagents, or run the skeptic stage. Do not answer from memory.

1. Resolve the question to a `gwosc-data` snapshot query and run it (instant, offline, cited):
   - one event's parameters → `python skills/gwosc-data/query_snapshot.py event <id>`
   - "how many" → `python skills/gwosc-data/query_snapshot.py count [--catalog GWTC-N]`
   - "most massive / closest / loudest / …" → `python skills/gwosc-data/query_snapshot.py max|min <param> [--catalog GWTC-N]`
2. Report the `best` value(s) with their **asymmetric errors** and the provenance the helper prints (catalog + DOI + snapshot retrieval date). Carry the uncertainty even in a one-line answer (integrity rule 10); note source-frame where relevant.
3. If the event isn't in the snapshot (the helper exits with code 2), fall back to exactly ONE live `gwosc-data` fetch of the event-version endpoint — no summarizing fetch, no duplicate calls.
4. For a superlative, honor the scope rule: give the cumulative (umbrella `GWTC`) answer and the named-release answer, or ask which scope is meant.

Stay in your lane: **quote the data, do not interpret it.** If the user wants meaning — comparisons, source classification, formation channels, "what does this tell us" — say so in one line and offer `/investigate` or `/event` for the full, skeptic-checked brief.
