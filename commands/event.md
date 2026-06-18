---
name: event
description: Pull a real GW event from GWOSC and produce a full Siren brief — what it taught us, what it's still hiding, and what's next.
---

Produce a Siren brief for GW event: **$ARGUMENTS**

1. Use the `gwosc-data` skill to fetch the event's real parameters (report `best` values with asymmetric errors and provenance).
2. `domain-expert-gw`: classify the source and flag which posteriors are trustworthy vs prior-dominated.
3. `interpreter`: state what is measured, inferred, and speculative — labeled.
4. `skeptic`: list the live threats (priors, selection, systematics, degeneracies) and whether the picture survives.
5. `cross-domain-bridge`: what this constrains or enables in adjacent fields.
6. `next-steps`: analysis-side and observation-side, essential vs possible.
7. `teacher`: close with an explanation at the level the user asked for (default: student).

Never recall parameter values — fetch them. If the short name 404s, retry with the full id.
