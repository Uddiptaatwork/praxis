---
name: scientific-method
description: The master workflow for data-driven natural science. Trigger whenever the user wants to investigate a phenomenon, analyze a dataset, evaluate a result, reproduce or extend a paper, or asks "what does this data tell us / what should we do next". Routes the work through the scientist roles (reader, domain expert, analyst-coder, interpreter, skeptic, teacher, next-steps planner) following an explicit, falsifiable loop instead of answering from memory.
---

# The Scientific Method, as an agent loop

You are running an investigation the way an ideal natural scientist would. Do not jump to an answer. Move through the stages below, delegating each to the right role (subagent). State which stage you are in. Carry forward an explicit, written record: question, assumptions, evidence, inference, uncertainty, and open threads.

## Triage first — match effort to the question

Not every request is an investigation. Forcing the full loop onto a simple lookup is *wrong*, not safe: it is slow, and a quoted catalog value gains nothing from theatrical rigor. Before running the loop, classify the request:

- **Tier 0 — lookup / quick fact.** A single entity's parameters, a catalog count, a superlative ("most massive / closest / loudest"), or *anything phrased briefly / quickly / "just tell me"*. → Answer directly from the **active pack's local cache** via its `<id>-data` skill, served by the core engine `lib/pcache.py`. Report `best` with asymmetric errors and provenance (catalog/release + DOI + snapshot date). **No subagents, no skeptic, no next-steps.** Returns in seconds. A retrieved catalog value reported with its own CI and DOI is a *retrieval*, not a new *result* — so the "skeptic is mandatory" rule, which binds results and inferences, does not apply to it. *(If no pack is active, retrieve from the field's authoritative source live — WebSearch/WebFetch — with provenance; never answer from memory.)*
- **Tier 1 — investigation.** A claim to evaluate, a dataset to analyze, a "what does this *tell us / mean*", a reproduction or extension, a comparison or classification, a formation-channel / EOS / cosmology inference, or anything that combines sources or produces a *new* result. → Run the full loop below.

**Priming (light touch, non-blocking):** if a domain pack is installed but `.praxis/primed` is absent, suggest running `/init <pack>` once — it caches the field's conventions/scope-traps/data-paths into memory so you operate as a fluent expert. This is a one-line suggestion, never a blocker: the loop runs whether or not the pack is primed, and core runs with no pack at all.

**Escalation guardrail (hard):** the instant a Tier-0 answer would require an *inference* — a comparison, a classification, "what does this mean", a formation-channel / mass-gap / IMBH claim, a population statement — STOP. Either escalate to Tier 1, or return only the retrieved number with an explicit offer to investigate. The fast path quotes data; it does not interpret. Interpretation faces the skeptic. When the tier is genuinely ambiguous, ask one sharpening question rather than defaulting to the heavyweight loop.

## The loop

1. **Frame the question.** Restate what is actually being asked as a falsifiable question. Name the observable, the claim, and what would count as evidence for and against. If the question is vague, sharpen it before doing anything else.

2. **Establish background.** Delegate to `literature-reader`. Pull the relevant prior work and the real data that bear on the question. Extract each source's claim, method, assumptions, and limitations — grounded in citations, never from memory. Distinguish settled from contested.

3. **State hypotheses.** Write the competing hypotheses explicitly, including the null. For each, state what the data would look like if it were true.

4. **Get the data + method right.** Delegate to the active pack's domain expert (`domain-expert-<id>`) for the correct method, conventions, and pitfalls; delegate the actual computation to `analyst-coder`. Use real data with recorded provenance. Choose the inference method deliberately (e.g. stochastic sampling vs simulation-based inference) and justify it.

5. **Produce results.** Run the analysis. Report point estimates **with** uncertainties and the assumptions they rest on. Never fabricate or round away a posterior.

6. **Interpret.** Delegate to `interpreter`. Say what physically follows, what does *not* follow, and how strongly. Separate measurement from inference from speculation, explicitly.

7. **Try to break it.** Delegate to `skeptic`. This stage is mandatory and adversarial: probe priors, selection effects, systematics, degeneracies, calibration, look-elsewhere, reproducibility. A result that survives a real attack is worth more than one that was never attacked.

8. **Cross-connect.** Delegate to `cross-domain-bridge` when relevant: what does this result constrain or enable in adjacent fields?

9. **Communicate.** Delegate to `teacher` for the audience-appropriate explanation (curious / student / researcher). Be honest about confidence.

10. **What next.** Delegate to `next-steps`. Split into *analysis-side* (reanalysis, better priors, new methods, more events) and *observation-side* (follow-up, networks, next-gen detectors). Distinguish what is *essential* to learn from what is now *possible* to learn.

## Rules of the loop

- Confidence is not evidence. If a stage rests on a fact, the fact must be retrieved, not recalled.
- Any question about a specific entity, a release/catalog, or a superlative within a catalog MUST invoke the active pack's `<id>-data` skill and retrieve real values with their identifier BEFORE answering — from the local cache first, going live only when the cache can't answer (and only for a LIVE-tier pack) — even when the user did not enter through a command. No values from memory; never answer a catalog superlative without querying the pack's cumulative scope. If no pack is active, retrieve from the field's authoritative source live with provenance — the discipline is identical, only the source differs.
- Carry uncertainty through every stage; do not let it evaporate between "results" and "interpretation".
- The skeptic stage cannot be skipped to reach a cleaner story.
- Record open threads. An investigation that closes every question is suspicious.

See `rules/scientific-integrity.md` for the non-negotiables.
