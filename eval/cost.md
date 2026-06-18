# Praxis — 90-second judge demo + real cost numbers

> **Captured:** 2026-06-18 against the **live** GWOSC API (`https://gwosc.org/api/v2`).
> **Base model:** `claude-sonnet-4-6` (default model in both shells; see `modelUsage` in the
> JSON envelope — Praxis also spins up `claude-haiku-4-5` for cheap subagent/skill steps).
> Both shells share the same base model, so every difference below is the **harness**, not the model.
>
> **Cost source:** the `--output-format json` envelope's `total_cost_usd` (real billed cost,
> incl. cache + subagents), `usage.output_tokens`, and `duration_ms`. No prices were invented;
> all `$` figures are read straight from `total_cost_usd`. Reproduce with `eval/run_ab.sh`.

---

## How the two shells were run

- **A — baseline (vanilla):** `claude -p "<prompt>" --output-format json`, run from a **clean
  empty directory** (`/tmp/praxis_baseline_clean`). A bare `claude -p` *inside* the repo inherits
  the project `CLAUDE.md` and reads stray local files, so it stops behaving like a clean baseline —
  the clean dir keeps A honest.
- **B — Praxis:** `cd /tmp && claude --plugin-dir /Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis
  --dangerously-skip-permissions -p "<prompt>" --output-format json`. Run from `/tmp` so the plugin
  is the only thing loaded.

macOS has no `timeout`; every run was allowed to finish.

---

## Step 1 — picking the demo prompt

Three candidates, both shells, live API. Wall-clock is to the **completed** answer (`duration_ms`).

| Cand. | Prompt (one line) | A secs | B secs | Contrast in ~30 s? |
|---|---|---|---|---|
| **C1** | source-frame masses of **GW150914** + 90% CIs, cite GWOSC | 27.6 | **47.5** | **Yes — starkest.** B = live API + real DOI + asymmetric CIs that *match* GWOSC; A = stale recalled numbers + hand-typed URL, no DOI. |
| C2 | masses + χ_eff of **GW190521** + 90% CIs, cite GWOSC | 44.1 | 57.3 | Yes, but B is near the 90 s edge; A's recall is "right-ish", so the gap is subtler than C1. |
| C3 | summarize PE for **GW250230_120000** (Feb 30 — impossible) | 81.9 | 35.5 | No clear *visible* win: **both refuse correctly.** Confirmed 404 at `https://gwosc.org/api/v2/events/GW250230_120000`. The difference is *why* each refuses (see `results-demo.md` S4) — too subtle for a 30 s glance, and A was the slowest of all runs. |

### Winner: **C1 — GW150914 component masses**

> **`What were the two source-frame component masses of GW150914, with 90% credible intervals? Cite the GWOSC source.`**

**Why C1 wins.** It is the single most *visually obvious* and most *reliable* contrast, and B still
answers inside a demo-usable ~47 s:

- **Provenance you can see.** B retrieves **live** from
  `https://gwosc.org/api/v2/event-versions/GW150914-v4/parameters` and prints a real
  **event-version DOI `10.7935/qf3a-3z67`** + posterior-samples DOI `10.5281/zenodo.6513631`.
  A prints only a hand-typed `eventapi/html/...` URL and **no DOI**.
- **The numbers actually differ, and B is right.** Ground-truth from the GWOSC API
  (default GWTC-2.1 version) is **m₁ = 34.6 ⁺⁴·⁴/₋₂·₆ M☉, m₂ = 30.0 ⁺²·⁹/₋₄·₆ M☉**.
  **B matches exactly.** A returns **m₁ = 36.2, m₂ = 29.1 M☉** — the *2016 detection-paper*
  values, which no longer match the current GWOSC preferred posterior. That is a live,
  pointable "**stale recall vs. live retrieval**" moment a non-expert grasps instantly.
- **Asymmetric CIs.** B's intervals are the genuinely asymmetric API values; A's reconstructed
  intervals are plausible but ungrounded.

C2 and C3 are kept below as the two fast comparison prompts for the cost table.

### Recommended 90-second demo prompt — verbatim A and B

**Prompt (paste verbatim into both shells):**

```
What were the two source-frame component masses of GW150914, with 90% credible intervals? Cite the GWOSC source.
```

**A — baseline output (verbatim), 27.6 s, $0.0802:**

```
I don't have web access approved, so I'll answer from my training knowledge (which covers the published LIGO results) and point you to the authoritative source.

**GW150914 — source-frame component masses (90% credible intervals)**

| Parameter | Value |
|---|---|
| Primary mass *m*₁ | **36.2 ⁺⁵·²/₋₃.₈ M☉** |
| Secondary mass *m*₂ | **29.1 ⁺³·⁷/₋₄.₄ M☉** |

These are from the initial detection paper (Abbott et al. 2016, *PRL* 116, 061102). Note that the GWTC-1 reanalysis (2019) yielded slightly updated values (m₁ = 35.6 ⁺⁴·⁷/₋₃.₀ M☉, m₂ = 30.6 ⁺³·⁰/₋₄.₆ M☉); the GWOSC event page reflects the most current posterior.

**Canonical GWOSC source to verify:**
`https://gwosc.org/eventapi/html/GWTC-1-confident/GW150914/`

The GWOSC event page links directly to the posterior samples and parameter-estimation results for each catalog release. The numbers above may differ slightly from what GWOSC currently lists if the preferred analysis has been updated, so I'd recommend checking that page directly.
```

**B — Praxis output (verbatim), 47.5 s, $0.1519:**

```
Here are the source-frame component masses for GW150914, from the latest GWOSC parameter estimation (v4, GWTC-2.1 re-analysis):

| Parameter | Best | 90% CI |
|---|---|---|
| *m*₁ (primary) | 34.6 M☉ | +4.4 / −2.6 M☉ |
| *m*₂ (secondary) | 30.0 M☉ | +2.9 / −4.6 M☉ |

**Provenance:**
- Event version: GW150914-v4
- Catalog: GWTC-2.1-confident (O1+O2 re-analysis with updated waveform models)
- PE pipeline: LALInference, waveform family C01:Mixed
- Event-version DOI: [10.7935/qf3a-3z67](https://doi.org/10.7935/qf3a-3z67)
- Posterior samples: [10.5281/zenodo.6513631](https://doi.org/10.5281/zenodo.6513631)
- Retrieved live from `https://gwosc.org/api/v2/event-versions/GW150914-v4/parameters`

These supersede the original GWTC-1 values (35.6/30.6 M☉) — the GWTC-2.1 re-analysis applied improved waveform models to the O1 data.
```

**Ground-truth check (GWOSC API, default version GW150914-v4):**
`mass_1_source = 34.6 +4.4/−2.6 M_sun`, `mass_2_source = 30.0 +2.9/−4.6 M_sun` — **B matches; A does not.**

---

## Step 2 — cost table

Three prompts: the **demo** (GW150914) plus two fast single-event comparisons
(**GW190521** masses+spin, **GW230529** mass-gap). All single-event = one primary API lookup,
all demo-fast. A = baseline, B = Praxis.

### A-vs-B per prompt — output tokens / seconds / $

| Prompt | A tok | A secs | A $ | B tok | B secs | B $ | Δ$ (B−A) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Demo — GW150914 masses** | 1188 | 27.6 | 0.0802 | 1556 | 47.5 | 0.1519 | **+0.0717** |
| Cmp — GW190521 masses+χ_eff | 2184 | 44.1 | 0.0964 | 1361 | 57.3 | 0.1569 | +0.0605 |
| Cmp — GW230529 mass-gap | 2603 | 50.8 | 0.1286 | 2503 | 110.7 | 0.2335 | +0.1048 |
| **TOTAL** | **5975** | **122.6** | **0.3052** | **5420** | **215.7** | **0.5422** | **+0.2370** |

**Honest read — this is the price of rigor, not a free lunch.** Praxis costs **~1.78×** the
baseline in $ over these three prompts (**+$0.2370**) and roughly **1.8×** the wall-clock, because
it actually does retrieval (hits the live GWOSC API, runs skill/subagent steps, attaches DOIs).
Interestingly Praxis used *fewer* total output tokens here (5420 vs 5975) — its answers are tighter —
so the extra $ is mostly cache/subagent/tool overhead from the retrieval machinery, not verbosity.
The deliverable B buys is a **grounded, DOI-cited, ground-truth-matching** answer instead of a
confident recall.

### Rigor-per-kilotoken

Rigor scores come from the eval suite (hand-scored **set-1**), not from these cost runs, so the
demo prompt's rigor is marked accordingly. Below: **cost per 1k output tokens** (from this run) and
the rigor axis (from set-1 where it exists).

| Prompt | A $/ktok-out | B $/ktok-out | Rigor (set-1) |
|---|---:|---:|---|
| **Demo — GW150914** | 0.0675 | 0.0976 | n/a (cost run only; see set-1 for the rigor uplift pattern) |
| Cmp — GW190521 | 0.0441 | 0.1153 | from set-1: B wins broadly on rigor (uncertainty, citations, layering) |
| Cmp — GW230529 | 0.0494 | 0.0933 | from set-1: B wins (separates measured chirp mass vs inferred component masses vs speculative formation) |

Reading: a Praxis output token costs ~1.4–2.6× a baseline token here, because each B token is
"backed" by a retrieval/verification step. Per-ktok cost is the closest cost-only proxy for
"rigor density"; the actual rigor scores live in `comparison-set-1.md` / `score.py`.

### Cost per fabrication avoided

> **Estimate — read the caveats.** Uses the **measured set-1 fabrication delta (A = 2, B = 1
> → 1 fabrication removed)** as the reference, combined with the **$ delta measured in this run**.
> Set-1 fabrication counts and this run's $ come from *different* prompt sets, so this is an
> order-of-magnitude figure, not a controlled per-prompt measurement.

- **Δ$ over the 3 cost prompts = $0.2370** (B − A).
- **Set-1 fabrications removed = 1** (A = 2 → B = 1).
- **Cost per fabrication avoided ≈ $0.2370 / 1 ≈ $0.24** (over a 3-prompt batch).
- Per single prompt, the average Δ$ is **$0.0790**, so on the order of **~$0.08 of extra spend per
  prompt** is what buys the fabrication-safety + provenance uplift.

Framed for judges: **for roughly a dime per prompt, Praxis turns a confident-but-stale recall into
a DOI-cited, ground-truth-matching answer and removes a fabrication.** That is the price of rigor.

---

## Reproduce

```bash
bash eval/run_ab.sh        # runs all 3 prompts × {A baseline, B Praxis}, prints the summary table
```

Raw JSON envelopes land in `/tmp/praxis_eval/*.json`; parse `total_cost_usd`,
`usage.output_tokens`, `duration_ms`.
