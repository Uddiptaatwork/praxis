# Praxis vs vanilla — comparison set 1

> **Status:** baseline vs **original** plugin (pre-patch), **hand-scored** 2026-06-18. This
> is the "before" half of the before/after pair; [`comparison-set-2.md`](comparison-set-2.md)
> re-runs the same three prompts through the patched plugin. See [`README.md`](README.md)
> for the suite overview and methodology.

The three questions below are worked instances of suite tests (full specs in
[`suite-gw.md`](suite-gw.md) and [`suite-general.md`](suite-general.md)):

- **Q1** = **S2** (cumulative-scope trap), relates to **S6** (distance–inclination degeneracy)
- **Q2** = **S3** (numerical fidelity) + **G2** (M/I/S separation)
- **Q3** = **S5** (mass-gap overinterpretation) + **G6** (calibration on a known-unknown)

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
⏺ Here is a concise answer covering both parts.

  ---
  Most Distant BBH Merger Detected

  Based on GWTC-4.0 (released August 2025, covering O4a), the current record-holder is
  GW230704_212616, with an inferred luminosity distance of:

  ▎ 7.2 +6.1 / −4.2 Gpc

  That corresponds to a redshift of roughly z ≈ 1.1–1.2 — meaning the merger happened when the
  universe was less than half its current age. The previous O3 record (from GWTC-3) was around 5–6
  Gpc for the most distant candidates.

  One important caveat: with several events at comparable distances and with overlapping
  posteriors, GW230704_212616 has only a ~22% probability of actually being the farthest source.
  GW231119_075248 (6.7 +5.5/−3.7 Gpc) is close behind at ~15%.

  ---
  How Well Is the Distance Actually Measured?

  Poorly, by most standards. The dominant problem is the distance–inclination degeneracy:

  - GW strain amplitude scales as ~ 1/d_L, but it also depends on the binary's inclination angle
  (face-on binaries are louder for the same distance).
  - From the dominant (2,2) gravitational-wave mode alone, you cannot distinguish "close and
  edge-on" from "far and face-on." The two parameters are strongly correlated in the posterior.

  The practical consequence: fractional uncertainties on d_L for typical BBH events run 30–80%
  (90% credible interval). For GW230704_212616 the quoted +6.1/−4.2 Gpc on a median of 7.2 Gpc is
  a ~85% upper / ~58% lower relative error — the distance could plausibly be anywhere from ~3 Gpc
  to ~13 Gpc.

  What can break the degeneracy?

  ┌─────────────────────────────────┬────────────────────────────────────────────────────────┐
  │             Method              │                         Effect                         │
  ├─────────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Higher-order GW modes (ℓ ≥ 3)   │ 2–15× improvement; requires high SNR or unequal masses │
  ├─────────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Orbital precession              │ Up to 10× improvement; needs asymmetric spins          │
  ├─────────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Electromagnetic counterpart     │ Definitive — but BBH mergers have none                 │
  ├─────────────────────────────────┼────────────────────────────────────────────────────────┤
  │ Network of detectors (geometry) │ Modest improvement via polarization constraints        │
  └─────────────────────────────────┴────────────────────────────────────────────────────────┘

  At cosmological distances the SNR is also low, so the higher-mode approach rarely delivers its
  full benefit for the most distant events. The upshot is that the ~7 Gpc figure is a
  best-estimate median, not a precise measurement.

  ---
  Bottom line: The most distant confirmed BBH candidate sits around 7 Gpc (~z ≈ 1.1), but the 90%
  credible interval spans nearly a factor of four in distance. Distance measurement from
  gravitational waves is fundamentally limited by the degeneracy between how far away and how
  inclined the binary is, and for low-SNR distant events that degeneracy is nearly unbroken.

  Sources:
  - GWTC-4.0 catalog paper (arXiv:2508.18082)
  - GWTC-4.0: Constraints on Cosmic Expansion Rate (arXiv:2509.04348)
  - Constraining inclinations of binary mergers from GW observations (IOPscience)
  - Precessing BBH as better dark sirens (MNRAS Letters)
  - Effect of higher harmonics on GW dark sirens (MNRAS)
  - LIGO GWTC-4.0 announcement

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
⏺ Here is what the data and theory say.

  ---
  GW190521 Component Masses (source frame, 90% CI)

  ┌───────────────┬────────────────────────────────────────┐
  │   Parameter   │                 Value                  │
  ├───────────────┼────────────────────────────────────────┤
  │ m₁ (heavier)  │ 85 +21/−14 M☉                          │
  ├───────────────┼────────────────────────────────────────┤
  │ m₂ (lighter)  │ 66 +17/−18 M☉                          │
  ├───────────────┼────────────────────────────────────────┤
  │ Total         │ 150 +29/−17 M☉                         │
  ├───────────────┼────────────────────────────────────────┤
  │ Final remnant │ ~142 M☉ (intermediate-mass black hole) │
  └───────────────┴────────────────────────────────────────┘

  These are source-frame masses after correcting for redshift (z ≈ 0.82, d_L ≈ 5.3 Gpc).

  ---
  Is m₁ = 85 M☉ Inside the Pair-Instability Gap?

  Almost certainly yes, but with caveats on both the observation and the theory side.

  The gap physics: Stars with helium core masses in a certain range undergo runaway pair-production of electrons and
  positrons, which lowers the radiation pressure holding the star up and triggers explosive oxygen burning. The result
  is either a pulsational pair-instability supernova (PPISN, shedding mass but leaving a remnant) or a full
  pair-instability supernova (PISN, no remnant at all). The predicted black hole mass gap from stellar collapse runs
  roughly:

  - Lower edge: ~45–65 M☉ (theoretically uncertain, depends heavily on the ¹²C(α,γ)¹⁶O nuclear reaction rate, rotation,
  and metallicity)
  - Upper edge: ~120–140 M☉ (above which direct collapse to IMBH may resume)

  With the commonly quoted boundaries of ~50–130 M☉, the primary at 85 M☉ sits comfortably in the middle of the gap.
  Even taking the most conservative (high) lower-edge estimate of ~65 M☉, it is still inside. The secondary at 66 M☉
  straddles the lower boundary depending on which stellar models you use.

  What this implies: Both components, but especially m₁, are hard to explain as the product of single-star collapse. The
  leading explanations are:

  1. Hierarchical mergers — each "component" is itself the remnant of an earlier BBH merger, probably in a dense stellar
  environment like a nuclear star cluster or AGN disk.
  2. Very massive stellar collapse with extreme mass loss suppressed (e.g., very low metallicity or strong magnetic
  fields).
  3. Primordial black holes (more speculative).

  The paper titling it a "straddling binary" (Fishbach & Holz 2020) quantified that both components are consistent with
  being inside the gap, making GW190521 the clearest observational challenge to standard pair-instability theory to
  date.

  One important caveat: The mass posteriors are broad (the +21/−14 M☉ interval on m₁ means it could be as low as ~71 M☉
  or as high as ~106 M☉ at 90% confidence), and the theoretical gap boundaries themselves carry ~10–20 M☉ of uncertainty
  from nuclear physics. The qualitative conclusion — m₁ is in or very near the gap — is robust, but the precise
  statement depends on which stellar models you adopt.

  Sources:
  - GW190521: A Binary Black Hole Merger with a Total Mass of 150 M☉ (arXiv:2009.01075)
  - Properties and astrophysical implications of GW190521 (arXiv:2009.01190)
  - The Pair-Instability Mass Gap for Black Holes (arXiv:2103.07933)
  - Minding the gap: GW190521 as a straddling binary (arXiv:2009.05472)

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
The interpretation is suggestive but has multiple independent layers of uncertainty. Here is an honest accounting of
  each.

  ---
  What Is Actually Well-Measured

  The chirp mass is tight: M_c = 1.94 ± 0.04 M☉. That is robustly measured from the phase evolution of the inspiral and
  is not in dispute.

  Everything else is considerably softer.

  ---
  Layer 1: The Individual Masses Are Prior-Dependent

  The headline numbers — m₁ = 3.6 +0.8/−1.2 M☉, m₂ = 1.4 +0.6/−0.2 M☉ — come from decomposing the chirp mass into
  individual masses using the mass ratio q. But q and the effective spin χ_eff are strongly degenerate in the
  gravitational-wave signal: a higher mass ratio (more unequal) looks similar to a spinning system. The event was
  detected by only one detector (LIGO Livingston, SNR ≈ 11.6), which further limits the constraints.

  Crucially, the paper "Impact of Astrophysical Priors on Parameter Inference for GW230529" showed that swapping the 
  spin prior can shift the inferred m₁ by ~1 M☉, potentially moving it out of the gap entirely. So "3.6 M☉ in the gap"
  is not a prior-independent statement.

  ---
  Layer 2: Is the Primary a Black Hole or a Heavy Neutron Star?

  The LVK cannot tell from this signal alone. The tests:

  - Tidal deformability of the primary peaks at zero (consistent with a BH) but the posterior is too broad to rule out a
  massive NS.
  - Effective spin is marginally negative (projecting onto the orbital axis), which weakly favors a BH (NSs are expected
  to be slow rotators and rarely show negative χ_eff), but is also consistent with zero.
  - A pure binary neutron star interpretation (both components are NSs, with the primary a maximally massive one) has
  been challenged but not definitively excluded.

  So the "black hole" label is the most probable interpretation, not a confirmed one.

  ---
  Layer 3: Does the Lower Mass Gap Even Exist?

  This is the deepest uncertainty. The gap (~2.5–5 M☉) was identified from Galactic X-ray binaries, where the
  lowest-mass dynamically-confirmed BHs cluster around 5–6 M☉. But X-ray binary selection effects are severe:

  - Mass transfer rates and companion types favour certain mass ratios.
  - Low-mass BHs may receive larger natal kicks (making bound binaries rarer).
  - Recent gravitational microlensing surveys find multiple compact-object candidates with masses in the 2.5–5 M☉ range.
  - Population analyses of GWTC-3 found no statistically significant preference for models with or without a gap.

  A 2025 paper ("No Gap and a Peak in the Black-Hole Mass Spectrum") argued the gap may be an artifact of the X-ray
  binary selection function rather than a real feature of the compact-object mass distribution.

  ---
  Summary

  ┌─────────────────────────────────────────────────────┬───────────────────────────────────────────────────────────┐
  │                        Claim                        │                        Robustness                         │
  ├─────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ This is a compact binary merger near the NS/BH      │ Solid                                                     │
  │ boundary                                            │                                                           │
  ├─────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Chirp mass ~1.94 M☉                                 │ Solid                                                     │
  ├─────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Primary mass ~3.6 M☉ (in gap)                       │ Moderate — prior-sensitive, shifts ~1 M☉ with spin        │
  │                                                     │ assumptions                                               │
  ├─────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ Primary is a black hole (not a heavy NS)            │ Weak — tidal deformability uninformative                  │
  ├─────────────────────────────────────────────────────┼───────────────────────────────────────────────────────────┤
  │ This demonstrates the gap is populated              │ Weak — the gap's existence is itself debated              │
  └─────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────┘

  GW230529 is genuinely interesting as an event near the boundary, and it is the most compelling single-event evidence 
  yet for a compact object in the lower mass gap. But characterizing it as "a black hole in the 3–5 M☉ gap" stacks three
  moderately uncertain claims on top of each other. The most honest statement is: it is most likely a NSBH system with
  a primary whose mass probably falls in or near the lower mass gap — but the signal does not nail any of those pieces
  down firmly on its own.

  Sources:
  - GW230529 discovery / Tests of GR paper (arXiv:2406.03568)
  - Impact of Astrophysical Priors on GW230529 (arXiv:2407.08719)
  - Challenging a BNS interpretation of GW230529 (Phys. Rev. D)
  - Possible BNS merger history of GW230529 primary (arXiv:2503.17872)
  - Hiding Out at the Low End: No Gap in BH Mass Spectrum (arXiv:2507.09099)
```

---

## Results & scoring (2026-06-18)

Each axis scored 0 (absent/wrong) · 1 (partial) · 2 (strong), per question. "Unsupported claims" is a count (lower better).

| Axis | Q1 A | Q1 B | Q2 A | Q2 B | Q3 A | Q3 B | **A** | **B** |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Provenance (GWOSC DOI) | 0 | 1 | 1 | 1 | 1 | 1 | **2** | **3** |
| Uncertainty (asym. errors) | 1 | 2 | 1 | 2 | 1 | 2 | **3** | **6** |
| Retrieval vs recall | 0 | 1 | 0 | 1 | 0 | 1 | **0** | **3** |
| Scope (catalog correct) | 0 | 1 | 1 | 1 | 1 | 1 | **2** | **3** |
| Measurement/inference/spec | 1 | 1 | 1 | 2 | 2 | 2 | **4** | **5** |
| Citations | 0 | 1 | 1 | 2 | 0 | 2 | **1** | **5** |
| Skepticism | 2 | 2 | 1 | 2 | 2 | 2 | **5** | **6** |
| **Per-question total / 14** | **4** | **9** | **6** | **11** | **7** | **11** | | |
| Unsupported claims | 2 | 1 | 0 | 0 | 0 | 0 | **2** | **1** |

**Overall: A = 17/42 (40%), B = 31/42 (74%), +82% relative.**

### Judgement

- **B wins broadly on rigor.** Biggest gaps: uncertainty (asymmetric ± errors on every number), citations (4–6 relevant papers vs 0–1), and the measurement/inference/speculation layering (Q3's robustness table is exemplary).
- **The skepticism gap is narrow** — vanilla is already skeptical (Q1 "ranking is nominal", Q3 "three separable claims"). B's edge is sharper structure, not presence vs absence.
- **Q1 is a shared failure.** Ground truth most-distant BBH is GW190403_051519 (z≈1.18, GWTC-2.1). Vanilla named GW190521 (z≈0.82 — not close). **B named GW230704_212616 "based on GWTC-4.0" — it scoped to one release instead of the cumulative `GWTC` catalog: the exact bug we patched.** The superlative/cumulative rule did **not** fire.
- **Mechanism caveat.** Every B answer cites arXiv IDs; **none cite the GWOSC DOIs we wired in**, and Q1 used a single release. This implies the `gwosc-data` skill (live retrieval + DOI + superlative rule) did **not trigger** on these *bare* questions — the prompts weren't `/investigate` or `/event`. B's gains here are the "rigor uplift" from the agent framing, not the retrieval machinery. The arXiv IDs are themselves the hand-typed-identifier risk rule #9 forbids (some are real; none verified-as-retrieved).

### Action items

1. Make retrieval fire on bare questions — strengthen `gwosc-data` triggers or have `scientific-method` auto-invoke it for any event/catalog query.
2. Hoist the cumulative-scope reflex into `domain-expert-gw` (consulted even when the skill doesn't load) so Q1-type scope errors are caught.
3. Re-run this set through `/investigate` to test the full loop (apples-to-apples for the machinery), not bare prompts.
4. Build the automated scorer (below) to remove hand-scoring subjectivity.

## Notes for the metrics pass (later)

- Each axis above can become a 0/1 or 0–2 score per answer → a stacked bar (A vs B) per axis, plus a per-question radar.
- The **Fabrication** row is the headline safety metric — count of numbers that don't match GWOSC ground truth. Aim: B = 0.
- A cheap automatable check: regex the outputs for DOIs / `±`-style error notation / catalog names, and diff named numeric values against the GWOSC API. That's a real test we can script.
