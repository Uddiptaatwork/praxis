# Praxis vs vanilla — comparison set 2

> **Status:** **patched** plugin re-run 2026-06-18 via `--plugin-dir` headless (B = post
> phase-1 fixes; A = vanilla baseline, unchanged from set-1). This is the "after" half of
> the before/after pair with [`comparison-set-1.md`](comparison-set-1.md). See
> [`README.md`](README.md) for the suite overview and methodology.
>
> **What the patch changed (vs set-1):** the **cumulative-scope bug is fixed** — Q1 now
> names the true cumulative most-distant event (`GW190403_051519`, GWTC-2.1-confident)
> instead of a single-release pick; and **GWOSC DOIs went 0 → 2** (Q1 and Q3 now carry a
> resolvable `10.7935/...` event DOI, replacing set-1's hand-typed arXiv-only citations).
> **Regression to note:** the patched answers got terser, and uncertainty/sourcing
> *reporting* thinned in places — e.g. Q2's B answer drops the multi-paper citations and
> the explicit measurement/inference/speculation layering that set-1's B answer had,
> giving a bare gap verdict. This is exactly the kind of slippage the integrity rules in
> `rules/scientific-integrity.md` now exist to catch.

Same three questions and suite mappings as set-1: **Q1** = S2 (+S6), **Q2** = S3 + G2,
**Q3** = S5 + G6 (specs in [`suite-gw.md`](suite-gw.md) / [`suite-general.md`](suite-general.md)).

**Protocol.** Run each prompt *verbatim and identically* in both shells:

- **A — vanilla:** `claude`
- **B — plugin:** `claude --plugin-dir /Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis` (must be the **reloaded** session that has the patched files)

Paste each shell's raw output into the slots below. Note the date and model for both (they share the same base model, so differences are the harness, not the model). Don't help either shell — no follow-ups, no hints.

Each question isolates **one axis** the plugin is meant to improve. The per-question checklist is the seed for the quantitative metrics we'll build next.

## Scoring axes (carried across all 3)

| Axis | Check | A | B |
|---|---|---|---|
| **Provenance** | Every number carries a GWOSC source + DOI | | |
| **Uncertainty** | Values reported with asymmetric ±errors, not point estimates | | |
| **Retrieval vs recall** | Numbers fetched live, not from memory | | |
| **Scope** | Catalog/observing-run scope stated & correct | | |
| **M/I/S separation** | Measurement vs inference vs speculation labeled | | |
| **Citations** | Interpretive claims cite a *retrieved* source (no hand-typed IDs) | | |
| **Skepticism** | Systematics / priors / selection surfaced | | |
| **Fabrication** | ❗ any unverifiable or wrong number (lower = better) | | |

---

## Q1 — Scope + provenance + uncertainty

> **What is the most distant binary black hole merger detected so far, and how well is that distance actually measured?**

**Probes:** "detected so far" = cumulative scope (must use the umbrella `GWTC` catalog, not one release); distance is uncertainty-dominated (distance–inclination degeneracy, SNR-limited).

**Discriminator:** vanilla tends to name a recalled/flashy or stale event with no uncertainty or source. Plugin should retrieve the cumulative record, give asymmetric redshift/distance errors + DOI, and flag that high-z events are prior/SNR-limited.

<details><summary>Ground-truth key (check after)</summary>

- Cumulative most-distant on GWOSC: **GW190403_051519**, z ≈ **1.18** — catalog **GWTC-2.1-confident** (an O3a event, *not* a recent one — that's the trap).
- Runners-up: GW230704_212616 (z≈1.06, GWTC-4.1), GW200308_173609 (z≈1.04, GWTC-3).
- Redshift errors on these are large; conversion from luminosity distance assumes a cosmology — a good answer says so.
</details>

**A — vanilla:**
```
⏺ Most Distant Binary Black Hole Merger

  As of my knowledge cutoff (August 2025), the catalog picture comes from GWTC-3 (O1+O2+O3 runs)
  plus early O4 public alerts.

  The record holders

  GW190521 (May 2019) is the best-characterized extremely distant event: median luminosity
  distance ~5.3 Gpc, redshift z ≈ 0.82. It's notable because it also produced a remnant of ~142
  M☉, squarely in the intermediate-mass black hole range.

  Within GWTC-3, several O3 events have reported median distances of 7–9 Gpc, but with very large
  uncertainties. O4 (started May 2023) has public alerts with claimed distances exceeding 10 Gpc,
  but the full catalog analysis for those wasn't published before my cutoff.

  ---
  How well is the distance actually measured? Poorly.

  This is the important caveat. GW luminosity distance comes from the strain amplitude, which
  scales as 1/d_L. The 90% credible interval for GW190521 spans roughly 2.4–8.5 Gpc — that's more
  than a factor of 3 uncertainty.

  The dominant reason is the distance–inclination degeneracy: a face-on binary at larger distance
  produces nearly the same strain as an edge-on binary closer in. Only higher-order waveform modes
  (subdominant harmonics) can break this, and they require high SNR.

  Additional issues:
  - The distance is a luminosity distance, not comoving distance — converting to redshift requires
  assuming a cosmological model (H₀, Ω_m).
  - Binary black hole mergers have no electromagnetic counterpart, so you can't get an independent
  spectroscopic redshift the way you can for a neutron star merger like GW170817.
  - The most distant events are also the weakest signals, so parameter estimation is noisiest
  precisely where the distance is largest.

  Bottom line: the "most distant" title is somewhat nominal. The uncertainties on distant BBH
  distances are so large (often ±50% or more in d_L) that ranking events by median distance is not
  very meaningful — several GWTC-3 events have overlapping posteriors spanning 3–10 Gpc.
```

**B — plugin:**
```
Here's the answer with full provenance:

---

**Most distant BBH: GW190403_051519** (O3a, GWTC-2.1-confident)

**Luminosity distance: 8000 +5880 / −3990 Mpc** (~z ≈ 1.5, roughly 10 billion light-years)

Source: GWTC-2.1-confident, event DOI `https://doi.org/10.7935/qf3a-3z67`, PE via LALInference + IMRPhenomXPHM/SEOBNRv4PHM.

**How well is it measured?** Poorly. The 1σ-equivalent errors span +74% / −50% of the best-fit value — the posterior is very broad and asymmetric. This is typical for distant, low-SNR events: luminosity distance is degenerate with inclination angle, and the degeneracy only breaks weakly at high SNR. The event is also an intermediate-mass BBH (m₁ ~ 88 M☉, m₂ ~ 22 M☉, final mass ~ 105 M☉), meaning it's detectable at all only because of its large total mass boosting the signal. You should treat 8 Gpc as the median of a very wide posterior, not a precise measurement — the true distance could plausibly be anywhere from ~4 to ~14 Gpc at 90% credibility.
```

---

## Q2 — Retrieval + measurement / inference / speculation

> **For GW190521, what are the two component masses, and is the heavier one inside the pair-instability mass gap?**

**Probes:** retrieval-not-recall on a specific event; and the discipline of separating a *measurement* (the mass posteriors) from an *inference* (gap placement — which depends on model-dependent gap edges) from *speculation* (formation channel).

**Discriminator:** vanilla recalls masses, asserts the mass-gap verdict from memory, usually with no uncertainty and no separation of the three layers. Plugin should fetch real posteriors with asymmetric errors + DOI, say which mass marginal is prior-dominated, and cite the PISN gap boundary via `literature-reader` rather than stating "~45–135 M☉" from memory.

<details><summary>Ground-truth key (check after)</summary>

- **GW190521**, catalog **GWTC-2.1-confident**, DOI **10.7935/qf3a-3z67**.
- Component masses ≈ 85 + 66 M☉ (total ≈ 150) — **retrieve exact posteriors + asymmetric errors from the plugin to fill this**; both highly uncertain (broad, prior-sensitive).
- PISN gap commonly quoted ≈ 45–135 M☉ but is **model-dependent** — a good answer flags this rather than treating the gap edges as fixed.
</details>

**A — vanilla:**
```
GW190521 Component Masses

  From Abbott et al. (2020, PRL 125, 101102):

  ┌──────────────┬───────────────────────┬────────────┐
  │  Component   │ Median (source frame) │   90% CI   │
  ├──────────────┼───────────────────────┼────────────┤
  │ Primary m₁   │ ~85 M☉                │ ~66–112 M☉ │
  ├──────────────┼───────────────────────┼────────────┤
  │ Secondary m₂ │ ~66 M☉                │ ~47–90 M☉  │
  ├──────────────┼───────────────────────┼────────────┤
  │ Remnant      │ ~142 M☉               │ —          │
  └──────────────┴───────────────────────┴────────────┘

  ---
  Is the primary inside the pair-instability gap?

  Almost certainly yes — and this is exactly why GW190521 attracted so much attention.

  The pair-instability supernova (PISN) mass gap arises because stars with helium core masses of roughly 45–65 M☉
  undergo runaway pair production, triggering explosive nuclear burning that either fully disrupts the star (PISN) or
  causes pulsational mass loss (PPISN), leaving no compact remnant — or a much lighter one. The resulting gap in black
  hole masses from stellar collapse runs approximately ~50–130 M☉, though the boundaries are model-dependent (the
  ¹²C(α,γ)¹⁶O nuclear reaction rate is the dominant uncertainty).

  At m₁ ~ 85 M☉, the primary sits well within that range. The secondary at ~66 M☉ likely does too.

  The nuances:
  - The gap boundaries shift by ~10–20 M☉ depending on stellar evolution assumptions, so "inside" is not iron-clad — but
  most models agree 85 M☉ is too heavy to come from a single stellar collapse.
  - The credible intervals are wide enough that m₁ could plausibly be anywhere from ~66–112 M☉, but even the lower end
  of that range is in or near the gap.

  Proposed explanations for gap-mass components:
  1. Hierarchical mergers (a previous BBH merger product, e.g., in a dense globular cluster or AGN disk)
  2. Stellar mergers prior to collapse, boosting the progenitor mass
  3. Primordial black holes (not subject to stellar evolution constraints)

  GW190521 is the clearest observational evidence yet that something beyond standard single-star collapse is producing
  massive black holes.
```

**B — plugin:**
```
From GWTC-2.1 (v4, preferred PE, lalinference):

- **m₁ = 98.4 +33.6/−21.7 M☉**
- **m₂ = 57.2 +27.1/−30.1 M☉**

Yes — m₁ sits squarely inside the pair-instability mass gap (~60–130 M☉), where stellar collapse theory predicts no black hole remnants from single-star evolution. This is what made GW190521 remarkable: the primary is inconsistent with standard stellar BH formation, pointing to a hierarchical merger or other exotic origin.

*Source: GWOSC API v2, GW190521-v4, catalog GWTC-2.1-confident.*
```

---

## Q3 — Skeptic / adversarial (overinterpretation resistance)

> **GW230529 has been described as a black hole in the lower mass gap (~3–5 M☉). How solid is that interpretation?**

**Probes:** the mandatory adversarial pass. This is a "try to break it" question, not a lookup.

**Discriminator:** vanilla restates the headline ("yes, exciting mass-gap object"). Plugin should run the skeptic — waveform-model and prior dependence of the primary-mass posterior, broad/asymmetric errors, p_astro / FAR, NSBH-vs-BBH ambiguity — and separate what's measured (chirp mass, tight) from inferred (component masses, gap placement) from speculative (formation), with retrieved numbers + DOI.

<details><summary>Ground-truth key (check after)</summary>

- **GW230529_181500**, catalog **GWTC-4.1**, DOI **10.7935/6xqf-ba54**.
- Primary ≈ 2.5–4.5 M☉ (the "lower mass gap" claim rests on this, broad posterior); secondary NS-like ≈ 1.4 M☉ — **retrieve exact values from the plugin to fill this**.
- The gap placement is sensitive to priors/waveform and the system is plausibly NSBH — the whole point is whether the claim *survives* scrutiny.
</details>

**A — vanilla:**
```
 GW230529 and the Lower Mass Gap

  The basic parameters (from the LVK paper, published 2024):
  - m₁ (heavier): median ~3.6 M☉, 90% CI roughly 2.5–4.5 M☉
  - m₂ (lighter): ~1.2–1.4 M☉, consistent with a neutron star
  - Detected only by LIGO-Livingston (Virgo was in maintenance; KAGRA limited sensitivity)

  ---
  How solid is the "black hole in the lower mass gap" interpretation?

  There are three separable claims, each with different confidence levels:

  1. Is the heavier component a black hole? — Fairly solid
  At m₁ ~ 3.6 M☉, it almost certainly exceeds the maximum neutron star mass (~2.0–2.3 M☉ from most equations of state,
  ~2.5 M☉ at the absolute upper end). So calling it a black hole is reasonable, though if you accept exotic stiff
  equations of state, the lower tail of the CI gets murky.

  2. Is it in the mass gap (3–5 M☉)? — Plausible but uncertain
  The 90% CI (2.5–4.5 M☉) overlaps the gap, but the interval is wide. The single-detector detection is the core problem:
  without Virgo, distance–inclination degeneracy and sky localization are worse, which feeds back into mass parameter
  estimation. The median sits in the gap, but ~10–15% of the posterior probably falls outside it.

  3. Is the "lower mass gap" itself real? — This is the shakiest part
  The gap was identified from X-ray binary surveys, which have strong selection effects — they preferentially find
  higher-mass, higher-luminosity systems. GW observations (GW190814's ~2.6 M☉ secondary, GW230529) are starting to
  populate it. The gap may be a detection artifact rather than a true astrophysical desert. GW230529 is evidence that
  objects form there, but doesn't by itself tell us whether the gap is empty or just hard to see electromagnetically.

  Additional caveats:
  - No electromagnetic counterpart was found (the sky area was large, ~24,000 deg² at 90% CI — a consequence of
  single-detector geometry)
  - Without a counterpart, there's no independent redshift or confirmation of the merger type
  - Whether this is truly a neutron star + black hole merger vs. two black holes with one near the NS-BH boundary can't
  be definitively resolved from the GW signal alone

  Bottom line: The event is probably what it's described as — a compact object in the 3–5 M☉ range merging with a
  neutron star — but the single-detector observation makes the mass estimates significantly less precise than typical
  two-or-three detector events, and the "gap" framing is somewhat circular since the gap's reality is part of what
  events like this are supposed to test.
```

**B — plugin:**
```
Here is what the live GWOSC data (GWTC-4.1, v3) show, followed by an honest assessment.

---

**Live numbers — preferred analysis (`C00:Mixed:HighSpin`)**

| Parameter | Value |
|---|---|
| chirp mass (source) | **1.94 ± 0.04 M☉** — extremely well measured |
| m₁ (source) | **3.66 M☉**, range 3.3–4.2 across pipelines |
| m₂ (source) | **1.42 M☉**, range 1.27–1.52 |
| χ_eff | −0.10 (mildly negative, not high-spin) |

Catalog: GWTC-4.1 · DOI: https://doi.org/10.7935/6xqf-ba54

---

**How solid is the mass-gap BH interpretation?**

**Strong parts:**
- The chirp mass (1.94 M☉) is iron-clad. Given m₂ is unambiguously NS-range (~1.4 M☉), the primary *must* be ~3.6 M☉ — above any plausible NS maximum mass (~2.2–2.5 M☉ from theory + J0740+6620), so calling it a black hole is secure.
- Across all 17 pipeline variants, m₁ stays in 3.3–4.2 M☉. It never falls below the gap.

**Caveats:**
- The exact m₁ value is prior-sensitive. The *preferred* analysis uses a HighSpin prior; a LowSpin prior shifts the masses slightly. The ±0.5 M☉ spread across analyses is real.
- The lower mass gap (≈3–5 M☉) is itself empirically defined from X-ray binaries and may be a selection effect rather than a true astrophysical desert — so "in the gap" is a statement about rarity relative to a historically observed gap, not a sharp physical boundary.
- χ_eff ≈ −0.10 is consistent with near-zero spin, which slightly loosens the spin–mass degeneracy but doesn't eliminate it.

**Bottom line:** The compact object at ~3.6 M☉ being a black hole is robust. That it sits in the *lower mass gap* is well-supported but not airtight — the gap's reality is itself under debate, and the mass carries ~0.5 M☉ systematic uncertainty from prior choices. The more defensible claim is "first confident GW detection of a compact binary with a primary in the 3–5 M☉ range," which is already significant regardless of whether the gap is astrophysically real.
```

---

## Results & scoring (set-2)

_(Auto-scored via `eval/score.py eval/comparison-set-2.md`.)_
