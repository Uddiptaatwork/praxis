# Praxis evaluation methodology (core)

The domain-agnostic half of the eval. It demonstrates, to an expert judge, that the
Praxis harness makes Claude a *better scientist* — not just a more verbose one —
without baking in any one field. The field-specific eval (the S-suite, the live-oracle
diff, worked A/B comparison sets) ships **inside each pack** (e.g. `packs/lvk/eval/`).

## Files here (core)

| File | What it is |
|---|---|
| `README.md` (this file) | Methodology, scoring axes, cost normalization, the two-point enforcement story |
| [`suite-general.md`](suite-general.md) | Tests **G1–G10** — domain-agnostic scientific conduct (transfer to any pack) |
| [`score_core.py`](score_core.py) | The generic scorer: form checks (uncertainty carried, DOI present, citation present) + a `DomainScorer` loader that pulls the field's DOI prefix / entity+catalog patterns / superlative map / live oracle from `packs/<id>/oracle/<id>_oracle.py` |
| [`aggregate.py`](aggregate.py) | Roll-up over runs |

Each pack ships its own `eval/suite-<id>.md` (the S-suite) and its `oracle/<id>_oracle.py`
(the DomainScorer + the tier's ground-truth oracle). Example: `packs/lvk/eval/` carries
`suite-lvk.md`, the live-GWOSC scorer (`score.py`), `run_ab.sh`, and the worked A/B sets.

## The two-point enforcement split (what the eval can and cannot certify)

- **Mechanically enforced (cache + Tier-0 serving).** `pvalidate.py` gates + `pcache.py`'s
  serving filter — certified structurally, not by eval. A cache is complete, DOI-resolvable,
  uncertainty-bearing, scope-landable, or the pack is `red`.
- **Eval-gated (Tier-1 free generation).** Deep-loop synthesis is prose-steered and
  empirically fabricates a non-zero fraction even in the tuned pack. So the only honest
  claim is a **measured per-pack rate**, release-gated (e.g. provenance ≥ threshold over N
  runs) — never "categorically non-fabricating." Report it; don't hide it.

## Scoring axes (generic; a pack maps them onto its data)

Per answer, score **0** (absent/wrong) · **1** (partial) · **2** (strong). `Fabrication`
is a **count** with a hard target of **0**.

| Axis | What it measures | Auto-checkable via |
|---|---|---|
| **Provenance** | numbers carry a resolvable identifier from the field's source | `score_core` generic + pack `DOI_PREFIX` |
| **Uncertainty** | values reported with CIs, asymmetric where appropriate | `score_core.RE_ASYM_ERR` |
| **Retrieval-vs-recall** | numbers match the *current* source, not stale memory | pack oracle live diff (LIVE) / byte-match (REDERIVE) |
| **Scope** | catalog / release scope stated & correct (esp. the cumulative scope) | pack `CATALOG_RE` + oracle |
| **M/I/S separation** | measurement vs inference vs speculation explicitly labeled | LLM-judge (rubric) |
| **Citations** | interpretive claims cite a *resolvable* source that *supports* the claim | resolve + LLM-judge |
| **Skepticism** | systematics / priors / selection surfaced | LLM-judge (rubric) |
| **Fabrication** ⚑ | numeric claims that don't match the oracle, or unresolvable identifiers | pack oracle |

## Cost normalization (price the rigor)

Capture output tokens, wall-clock, and $ per answer, then report: **rigor-per-kilotoken**
(`score / output_ktokens`), **cost per fabrication avoided** (`Δ$ / (A_fab − B_fab)`), and
the **quality–cost frontier** (score vs $, segmented by test class — cheap lookups
shouldn't pay the adversarial tax).

## Protocol

Run each prompt **verbatim and identically** in two shells, same base model, same day:
**A — baseline** (`claude`) vs **B — Praxis** (`claude --plugin-dir praxis --plugin-dir
praxis/packs/<id>`, core first). Validate manifests with `claude plugin validate .` and
`python lib/pvalidate.py packs/<id>` first. Run each prompt **bare** and via
**`/investigate`** separately (retrieval doesn't always fire on a bare prompt), and k≥3
reps for pass@k variance. Ground truth is never stored — it is the oracle query named in
each test.
