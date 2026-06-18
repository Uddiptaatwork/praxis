# Evaluation — does praxis actually help?

A controlled comparison of Claude **without** the praxis plugin (*vanilla*) vs. **with** it
(*praxis*), on identical scientific questions, scored on **scientific integrity** rather than
generic helpfulness. The two arms differ in only one variable: the plugin.

![Integrity hexagon: praxis vs vanilla Claude](docs/integrity-hexagon.png)

*Pilot: 12 questions × Haiku × low effort × 2 repeats = 24 paired runs. Larger area = stronger integrity.*

---

## The metrics

### Objective (pattern / retrieval, no LLM)
- **Provenance** — fraction of answers that attribute claims to a real source.
- **Citations** — fraction with ≥1 checkable reference (arXiv / DOI / URL).
- **Factual accuracy** — does the number match the retrieved gold value within its uncertainty
  (only on verified keys).
- **Fabrication avoided** — `1 − risk` of stating an unsourced number on a factual question.

### Semantic classifier (cheap, blind, per answer)
- **Uncertainty quantification** — did it carry intervals / error bars?
- **Trap handling** — on traps, did it reject false premises / decline the unanswerable /
  flag contested topics?

### Blind judge (Opus, scores each answer 0–2)
- **Provenance, Uncertainty, Trap handling, Correctness** — holistic quality,
  blinded + order-randomized.

**Combining:** the hexagon shows the **absolute mean per arm**; the forest plot shows the
**paired praxis − vanilla** difference with a **95% bootstrap CI** — a result counts as a win
**only when the CI clears zero**.

---

## Results (pilot)

Blind judge preferred praxis in **17 of 24** paired runs (vanilla 4, tie 3).

| Result | Metrics | Status |
|---|---|---|
| **Significant** (95% CI excludes 0) | judge provenance (+0.79), judge uncertainty (+0.46), fabrication avoided (risk 0.50 → 0.00) | praxis better |
| **Leaning praxis** (CI touches 0) | provenance rate, factual accuracy (0.83 → 1.00), citations | promising, underpowered |
| **Honest null** | trap handling | wash — vanilla already declines/flags well at this tier |

**Read honestly:** at the cheapest tier the measurable praxis advantage is **provenance,
uncertainty, and fabrication-avoidance** — not trap handling, which vanilla already does. The
factual keys are **retrieved from GWOSC**, never recalled, so factual-accuracy is graded
against real catalog values.

---

## Reproduce / extend

The harness and question set live in the sibling `praxis-test/eval/` setup; the figure is
regenerated from scored results with `make_hexagon.py`. See `HEXAGON_VIZ.md` for the recipe to
pool results across machines (add questions → recompute the six axis means → the chart updates).
