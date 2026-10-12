---
name: quick
description: Fast, cited lookup from the active pack's local cache — one entity's parameters, a catalog count, or a superlative — answered with no heavy loop.
---

Answer quickly and directly: **$ARGUMENTS**

This is a Tier-0 lookup (see the `scientific-method` skill's triage). Do NOT run the scientific-method loop, convene subagents, or run the skeptic stage. Do not answer from memory.

1. Resolve the active pack (`python lib/pack_resolver.py active`), then resolve the question to a `lib/pcache.py` query against that pack's cache and run it (instant, offline, cited). The cache path auto-resolves from the active pack (or pass `--cache <path>`):
   - one entity's parameters → `python lib/pcache.py entity <id>`
   - "how many" → `python lib/pcache.py count [--catalog <release>]`
   - "most massive / closest / loudest / …" → `python lib/pcache.py max|min <param> [--catalog <release>]`
2. Report the `best` value(s) with their **asymmetric errors** and the provenance the engine prints (release/catalog + DOI + snapshot retrieval date). Carry the uncertainty even in a one-line answer (integrity rule 10); note frame/convention where relevant.
3. If the entity isn't in the cache (`pcache.py` exits with code 2): for a **LIVE-tier** pack, fall back to exactly ONE live fetch of the source's per-entity endpoint — no summarizing fetch, no duplicate calls; for a **REDERIVE/ASSERTED** pack, report the honest absence ("not in the cached release set"), never a recall.
4. For a superlative, honor the scope rule: give the pack's cumulative-scope answer and the named-release answer, or ask which scope is meant. With ≥2 packs installed, disambiguate the domain first.
5. If no pack is active, retrieve the value live from the field's authoritative source (WebSearch/WebFetch) with provenance — the discipline is identical, only the source differs.

Stay in your lane: **quote the data, do not interpret it.** If the user wants meaning — comparisons, classification, formation channels, "what does this tell us" — say so in one line and offer `/investigate` for the full, skeptic-checked brief.
