---
name: event
description: Pull a real GW event from GWOSC and produce a full Siren brief — what it taught us, what it's still hiding, and what's next.
---

Produce a Siren brief for GW event: **$ARGUMENTS**

1. Use the `lvk-data` skill to fetch the event's real parameters (report `best` values with asymmetric errors and provenance). The data table must carry the GWOSC `doi` retrieved from the API — both the event-version `doi` and its catalog `doi` — as provenance. Never hand-type an identifier.
2. `domain-expert-lvk`: classify the source and flag which posteriors are trustworthy vs prior-dominated. Any statement beyond the raw retrieved numbers — classification context, comparisons to other events, formation-channel / mass-gap / IMBH claims — must route through the `literature-reader` subagent and carry a RETRIEVED citation. No claim from memory; no hand-typed arXiv ids, DOIs, or URLs.
3. `interpreter`: state what is measured, inferred, and speculative — labeled.
4. `skeptic`: list the live threats (priors, selection, systematics, degeneracies) and whether the picture survives.
5. `cross-domain-bridge`: what this constrains or enables in adjacent fields.
6. `next-steps`: analysis-side and observation-side, essential vs possible.
7. `teacher`: close with an explanation at the level the user asked for (default: student).

Never recall parameter values — fetch them. If the short name 404s, retry with the full id.
