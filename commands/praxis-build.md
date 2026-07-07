---
name: praxis-build
description: The ONE expensive step — transactionally bootstrap a brand-new Praxis domain pack from scratch (discover sources, build a provenance-stamped cache, stamp out the pack). Run as the principal-investigator, under the integrity rules. Not needed for the shipped lvk/pta packs.
---

Bootstrap a new domain pack: **$ARGUMENTS**  (e.g. `/praxis-build exo --archive "NASA Exoplanet Archive" --sota "hot-Jupiter demographics"`)

This is a rigor-governed Praxis investigation ("characterize this field and build its pack"), the only token-hungry / network-heavy operation. It is two-phase and transactional — nothing is promoted until all gates pass. **Print a cost/time estimate for the proposed oracle tier and confirm before the expensive fetch.**

**Phase H (headless, resumable):**
0. Resolve `<domain>` → `id`. Create a **staging dir** and stamp `lib/templates/*.tmpl` into it (status `uninitialized`).
1. `literature-reader` + `skeptic`: discover the field's authoritative data archive(s) + access protocol (→ the achievable oracle **tier**: LIVE if a live API exists, REDERIVE if only static release tables, ASSERTED if only PDFs/tables) and the landmark SOTA papers. **Retrieve every DOI/URL from the source; never recall.** → **CHECKPOINT A:** human ratifies the source list + DOIs + the proposed tier.
2. `literature-reader`: extract conventions, identifier scheme, cumulative/scope model, threat taxonomy, the measured/inferred/speculative split, open limits, and bridge targets — each cited. → **CHECKPOINT B:** human reviews conventions **and authors the irreducible expert-judgment slots** (the BLANK slots block `pvalidate` gate 9).
3. `paper-reading`: write `cache/sota.json` as a citation index (DOI + one-line characterization + status + asserted_utc + source_license).
4. `analyst-coder`: generate `cache/build.py` from the template, specialized to the archive; run it into staging (resumable per page; stamps `results_count_reported`; a value it can't retrieve is null+flag, never guessed).
5. Emit the pack artifacts from templates, *from the cited material*: `agents/domain-expert-<id>.md`, `skills/<id>-data/SKILL.md`, `oracle/<id>_oracle.py` (at the declared tier), `eval/suite-<id>.md`, `pack.json`, `.claude-plugin/plugin.json`.

**Phase R (ratification):**
6. Run `python lib/pvalidate.py packs/<id>` (all gates) + a smoke A/B (3 questions through `pcache.py`; one through the oracle). → **CHECKPOINT C:** on green, atomically move staging → `packs/<id>/`, set `.praxis/active=<id>`, and print install + `/init <id>` instructions. On any red gate, discard staging and report the failure (never ship silently — integrity rule 1).

Refuse to overwrite an initialized pack without `--reinit`.
