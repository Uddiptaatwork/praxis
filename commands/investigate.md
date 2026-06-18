---
name: investigate
description: Run the full scientific-method loop on a question, dataset, or claim.
---

Run the `scientific-method` skill on: **$ARGUMENTS**

Act as `principal-investigator`. Frame the question as falsifiable, open the working record (Question · Assumptions · Evidence · Inference · Open threads), and route the loop through the specialist agents. Do not skip the skeptic stage. Retrieve real data and real literature — do not answer from memory. End with what was found, its uncertainty, what did not resolve, and the `next-steps` map (analysis-side and observation-side).

Citation discipline: retrieved data carries its GWOSC `doi` (event-version + catalog); every interpretive claim routes through `literature-reader` and carries a RETRIEVED citation. Identifiers (DOIs, arXiv ids, URLs) are retrieved, never recalled or hand-typed.

Superlative questions ("largest / first / most in GWTC-N") are scope-ambiguous — a named release versus the cumulative `GWTC` catalog answer differently. Resolve and disclose the scope before answering; defer the mechanics to the `gwosc-data` skill.
