# Does Praxis make Claude a better scientist? — the 90-second case

![rigor](https://img.shields.io/badge/rigor_score-%2B82%25-2ea043)
![fabrication](https://img.shields.io/badge/unsupported_claims-2_→_1-2ea043)
![retrieval](https://img.shields.io/badge/live_retrieval-0%2F3_→_3%2F3-2ea043)
![provenance](https://img.shields.io/badge/GWOSC_DOIs-0_→_2-2ea043)
![cost](https://img.shields.io/badge/price_of_rigor-~1.8×_(~$0.08%2Fq)-blue)

**Claim:** same base model, same prompt — Praxis answers GW questions like a careful scientist (live data, real provenance, honest uncertainty), where vanilla Claude answers from memory. The only variable is the plugin.

---

## ⏱️ The 90-second demo — paste this into both shells

```
What were the two source-frame component masses of GW150914,
with 90% credible intervals? Cite the GWOSC source.
```

- **Shell A — vanilla:** `claude`
- **Shell B — Praxis:** `claude --plugin-dir /path/to/praxis`

Both shells *know* GW150914 (it's the famous first detection). Watch what each does with it:

| | **A — vanilla Claude** | **B — Claude + Praxis** |
|---|---|---|
| m₁ | 36.2 M☉ | **34.6 ⁺⁴·⁴⁄₋₂·₆ M☉** |
| m₂ | 29.1 M☉ | **30.0 ⁺²·⁹⁄₋₄·₆ M☉** |
| Source | a hand-typed URL | **DOI `10.7935/qf3a-3z67`** (GWTC-2.1) |
| vs current catalog | the **2016 discovery-paper** values, from memory | **matches GWOSC exactly**, retrieved live |

> One recalls 9-year-old numbers with no source. The other **retrieves the current catalog values and cites a resolvable DOI.** That's the whole pitch in one screen.

*(Tip: paste into the Praxis shell first — it takes ~45s to retrieve while you talk — then paste into vanilla, which answers instantly. Verified live numbers; GWOSC re-fetches at grade time so this can't go stale.)*

---

## 📊 The scorecard (3 head-to-head questions, hand-scored 0–2 per axis)

| Axis | Vanilla (A) | Praxis (B) |
|---|:--:|:--:|
| Provenance (cites a real GWOSC DOI) | 2 | **3** |
| Uncertainty (asymmetric error bars) | 3 | **6** |
| Retrieval vs recall (current, not remembered) | 0 | **3** |
| Scope (right catalog / cumulative) | 2 | **3** |
| Measurement vs inference vs speculation | 4 | **5** |
| Citations (relevant, resolvable papers) | 1 | **5** |
| Skepticism (systematics, priors, selection) | 5 | **6** |
| **Overall** | **17 / 42** | **31 / 42 (+82%)** |
| **Unsupported claims** (lower is better) | **2** | **1** |

Full transcripts and scoring: [`eval/comparison-set-1.md`](eval/comparison-set-1.md).

---

## 🔧 What a round of fixing moved (before → after)

Re-running the same prompts through the patched plugin ([`eval/comparison-set-2.md`](eval/comparison-set-2.md)):

- **Live retrieval auto-fires on 3/3 bare questions** — no special command needed.
- **A scope bug we found *and fixed*:** "most distant BBH so far" now resolves against the *cumulative* catalog and returns the true record-holder `GW190403_051519` — not a release-scoped wrong answer.
- **GWOSC DOIs cited: 0 → 2.** Component masses went from *recalled* to *retrieved*.
- Honest note: terser answers initially reported fewer error bars — now governed by [integrity rule #10](rules/scientific-integrity.md) ("conciseness reduces prose, not uncertainty").

---

## 💵 The price of rigor (real measured cost)

Praxis does real work — it costs more, and we report it rather than hide it.

| | Vanilla (A) | Praxis (B) |
|---|:--:|:--:|
| Cost / question | ~$0.10 | ~$0.18 |
| Wall-clock / question | ~40 s | ~70 s |
| Output tokens | 5,975 | **5,420** (tighter, not more verbose) |

≈ **1.8× the cost, ~8¢ extra per question** — the price to turn an unsourced recalled number into a retrieved, cited one. Detail: [`eval/cost.md`](eval/cost.md).

---

## 🔬 Not cherry-picked — a 22-test benchmark

The three demo questions are worked examples of a full suite spanning the breadth of GW work, each scored against the **live GWOSC API as an oracle** (so fabrication is measured, not judged):

- **[`eval/suite-gw.md`](eval/suite-gw.md)** — S1–S12: post-cutoff retrieval, numerical fidelity, nonexistent-event traps, mass-gap overinterpretation, H₀ standard sirens, neutron-star EOS, populations, data-quality, frames & units.
- **[`eval/suite-general.md`](eval/suite-general.md)** — G1–G10: domain-agnostic scientific conduct (fabrication resistance, mandatory uncertainty, calibration, false-premise correction, reproducibility) that transfers to any future Praxis domain.
- **[`eval/score.py`](eval/score.py)** — the automatable grader (regex + live-GWOSC diff).

---

<details>
<summary><b>Limitations (stated plainly)</b></summary>

- 3 of the 22 suite tests are measured head-to-head so far; the rest are specified with an automatable grader.
- The grader implements layers 1–2 (regex + live-GWOSC diff); layers 3–5 (citation resolver, rubric LLM-judge, pass@k) are specified, not yet built.
- Cost numbers above are from a small live batch on `claude-sonnet-4-6`; the per-question figures are representative, not a large-N average.
- The "won't lie" nonexistent-event demo is real but subtle headless (both refuse; the difference is *why* — vanilla guesses, Praxis checks GWOSC and sources the verdict). The provenance demo above is the more reliable live cell.

Full panel package: [`eval/FOR-JUDGES.md`](eval/FOR-JUDGES.md).
</details>
