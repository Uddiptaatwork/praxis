---
name: praxis-refresh
description: Re-ground a pack's cache — re-run its builder (resumably) and re-validate — when a new data release lands. Leaves the human-ratified conventions and authored expert-judgment slots intact.
---

Refresh the cache for pack: **$ARGUMENTS**

Refresh is release-triggered, not clock-triggered.

1. Re-run `python packs/<id>/cache/build.py` (resumable into staging; a LIVE pack re-pages the API, a REDERIVE pack re-stamps from `transcription.json`). It writes a fresh `retrieved_utc` + `builder_version`.
2. Re-extract any `cache/sota.json` entries whose DOIs changed/were added (keep the existing citations).
3. Run `python lib/pvalidate.py packs/<id>` — all gates must pass (esp. gate 3 completeness) before the refreshed cache is trusted.
4. Honor `supersede_rule`: `replace` (a new release supersedes the previous cumulative view) vs `complement` (a new release ADDS members to the set rather than replacing them) — do not delete complemented members.
5. Report the delta: entities added/changed, new `retrieved_utc`, and whether any superlative (records) moved.

This re-runs only the data + SOTA + validation steps; it does NOT touch the human-authored conventions or expert-judgment slots.
