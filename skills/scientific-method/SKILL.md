---
name: scientific-method
description: The master workflow for data-driven natural science. Trigger whenever the user wants to investigate a phenomenon, analyze a dataset, evaluate a result, reproduce or extend a paper, or asks "what does this data tell us / what should we do next". Routes the work through the scientist roles (reader, domain expert, analyst-coder, interpreter, skeptic, teacher, next-steps planner) following an explicit, falsifiable loop instead of answering from memory.
---

# The Scientific Method, as an agent loop

You are running an investigation the way an ideal natural scientist would. Do not jump to an answer. Move through the stages below, delegating each to the right role (subagent). State which stage you are in. Carry forward an explicit, written record: question, assumptions, evidence, inference, uncertainty, and open threads.

## The loop

1. **Frame the question.** Restate what is actually being asked as a falsifiable question. Name the observable, the claim, and what would count as evidence for and against. If the question is vague, sharpen it before doing anything else.

2. **Establish background.** Delegate to `literature-reader`. Pull the relevant prior work and the real data that bear on the question. Extract each source's claim, method, assumptions, and limitations — grounded in citations, never from memory. Distinguish settled from contested.

3. **State hypotheses.** Write the competing hypotheses explicitly, including the null. For each, state what the data would look like if it were true.

4. **Get the data + method right.** Delegate to `domain-expert-gw` (or the relevant domain expert) for the correct method, conventions, and pitfalls; delegate the actual computation to `analyst-coder`. Use real data with recorded provenance. Choose the inference method deliberately (e.g. stochastic sampling vs simulation-based inference) and justify it.

5. **Produce results.** Run the analysis. Report point estimates **with** uncertainties and the assumptions they rest on. Never fabricate or round away a posterior.

6. **Interpret.** Delegate to `interpreter`. Say what physically follows, what does *not* follow, and how strongly. Separate measurement from inference from speculation, explicitly.

7. **Try to break it.** Delegate to `skeptic`. This stage is mandatory and adversarial: probe priors, selection effects, systematics, degeneracies, calibration, look-elsewhere, reproducibility. A result that survives a real attack is worth more than one that was never attacked.

8. **Cross-connect.** Delegate to `cross-domain-bridge` when relevant: what does this result constrain or enable in adjacent fields?

9. **Communicate.** Delegate to `teacher` for the audience-appropriate explanation (curious / student / researcher). Be honest about confidence.

10. **What next.** Delegate to `next-steps`. Split into *analysis-side* (reanalysis, better priors, new methods, more events) and *observation-side* (follow-up, networks, next-gen detectors). Distinguish what is *essential* to learn from what is now *possible* to learn.

## Rules of the loop

- Confidence is not evidence. If a stage rests on a fact, the fact must be retrieved, not recalled.
- Carry uncertainty through every stage; do not let it evaporate between "results" and "interpretation".
- The skeptic stage cannot be skipped to reach a cleaner story.
- Record open threads. An investigation that closes every question is suspicious.

See `rules/scientific-integrity.md` for the non-negotiables.
