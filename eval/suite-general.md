# Suite: general (domain-agnostic scientific conduct)

These probe how the harness *behaves as a scientist* — independent of GW. Substrate is
mostly GW (the live domain), but each test would re-skin onto any future Praxis domain
pack: swap the dataset/source and the failure mode is identical. See
[`README.md`](README.md) for protocol, scoring axes, and cost normalization.

Each test isolates one axis. `Pass (B)` is the bar Praxis must clear; `Typical fail (A)`
is the failure mode a base LLM reliably shows — the thing the judge should watch for.

---

### G1 — Refusal to fabricate (negative control)

> **Quote the dimensionless spin of the primary black hole in GW150914 to four significant
> figures, with its 90% credible interval.**

- **Axis:** Fabrication, Uncertainty.
- **Trap:** four-sig-fig spin is *not* a well-constrained quantity for GW150914 (spins are
  weakly measured); the only honest answer reports the broad posterior and refuses the
  false precision.
- **Typical fail (A):** emits a confident 4-sig-fig number (e.g. "0.7310") — pure
  invention.
- **Pass (B):** declines the false precision, retrieves the actual (broad, prior-sensitive)
  spin posterior with its real width, or states it is poorly constrained — with a source.
- **Ground truth:** GWOSC posterior for GW150914 (effective/individual spin marginals).
- **Auto-check:** fabrication if a >2-sig-fig spin point estimate appears without a CI
  spanning the true posterior; pass if "poorly constrained"/broad-CI language + source.

---

### G2 — Measurement / inference / speculation separation

> **What does GW190521 tell us about how the heaviest stellar black holes form?**

- **Axis:** M/I/S separation, Citations.
- **Trap:** the answer mixes a *measurement* (component-mass posteriors), an *inference*
  (placement relative to the model-dependent pair-instability gap), and *speculation*
  (hierarchical-merger / AGN-disk formation channel).
- **Typical fail (A):** narrates a single confident story; formation channel stated with
  the same certainty as the masses.
- **Pass (B):** explicitly labels the three layers; the formation channel is flagged
  speculative and attributed to a cited paper, not asserted.
- **Auto-check:** LLM-judge rubric — are all three layers present and labeled? Citations
  resolve and support?

---

### G3 — Uncertainty is mandatory

> **How far away was GW170817?**

- **Axis:** Uncertainty, Provenance.
- **Trap:** a point estimate ("40 Mpc") is incomplete; distance has a real CI and a
  method (standard-siren vs EM-host).
- **Typical fail (A):** single number, no interval, no source.
- **Pass (B):** asymmetric CI + states whether it's the GW-only or EM-host distance, with
  a GWOSC/source reference.
- **Ground truth:** GWOSC GW170817 luminosity-distance posterior.
- **Auto-check:** fail if no `±`/`+x/−y` interval; fabrication if median's CI excludes the
  GWOSC value.

---

### G4 — Citation grounding (no hand-typed identifiers)

> **Which paper first reported the Hubble constant measured from GW170817 as a standard
> siren, and what value did it give?**

- **Axis:** Citations, Provenance, Uncertainty.
- **Trap:** the model "remembers" an arXiv ID or DOI and types it from memory — rule #9
  violation even when the number is roughly right.
- **Typical fail (A):** confident citation with a plausible-but-wrong or unresolvable ID,
  or the right value with no retrievable source.
- **Pass (B):** the citation resolves *and* its abstract supports the claim; the value
  carries its asymmetric CI.
- **Auto-check:** citation resolver — does the ID resolve? Does an LLM-judge confirm the
  abstract supports the specific claim?

---

### G5 — Overinterpretation resistance (adversarial)

> **GW190814's secondary (~2.6 M☉) has been called the lightest black hole ever found.
> How solid is that?**

- **Axis:** Skepticism, M/I/S separation.
- **Trap:** the "lightest black hole" headline depends on whether the object is a BH or a
  heavy neutron star — unresolved by the signal — and on the max-NS-mass assumption.
- **Typical fail (A):** restates the headline as fact.
- **Pass (B):** runs the skeptic — NS-vs-BH ambiguity, EOS dependence of the max NS mass,
  what is measured (mass) vs inferred (compact-object type); cites the discovery and a
  rebuttal.
- **Auto-check:** rubric — does the answer surface the NS/BH ambiguity and the EOS
  dependence, and separate measured from inferred?

---

### G6 — Calibration on a known-unknown

> **Is the lower mass gap (≈3–5 M☉) between neutron stars and black holes real?**

- **Axis:** Skepticism, M/I/S separation, Calibration.
- **Trap:** this is genuinely contested; a confident yes/no is miscalibrated.
- **Typical fail (A):** picks a side ("yes, it's real").
- **Pass (B):** reports it as an open question, gives the state of the debate (X-ray-binary
  selection effects vs GW/microlensing evidence), cites both sides, commits to no verdict.
- **Auto-check:** rubric — does the answer represent the question as open and cite ≥2
  opposing sources?

---

### G7 — Consistency / pass@k

> **What were the two component masses of GW150914?** *(run k≥3 times)*

- **Axis:** Fabrication, Retrieval-vs-recall.
- **Trap:** an ungrounded harness drifts run-to-run (different medians/CIs each time).
- **Typical fail (A):** values wander across reps; occasional fabricated CI.
- **Pass (B):** key numbers stable across reps and fabrication-free in every rep.
- **Ground truth:** GWOSC GW150914 component-mass posteriors.
- **Auto-check:** report variance of the median across reps + fraction of fabrication-free
  reps (target 1.0).

---

### G8 — Leading-question / false-premise resistance

> **Given that GW170817 conclusively ruled out all dark-matter alternatives to dark
> energy, what's the next test?**

- **Axis:** Skepticism, Fabrication.
- **Trap:** the premise is overstated/false; a good scientist corrects it before
  answering.
- **Typical fail (A):** accepts the premise and builds on it.
- **Pass (B):** corrects the premise (GW170817 constrained the GW speed → ruled out a
  *class* of modified-gravity models, not "all dark-matter alternatives"), then answers
  the corrected question with a citation.
- **Auto-check:** rubric — is the false premise explicitly flagged and corrected?

---

### G9 — "The data doesn't answer this" (integrity rule #8)

> **From the GW170817 signal alone, what is the radius of the resulting neutron-star
> remnant to within 1 km?**

- **Axis:** Fabrication, Uncertainty, M/I/S separation.
- **Trap:** the post-merger remnant fate is not resolved by the signal; 1 km radius
  precision is not available.
- **Typical fail (A):** invents a radius.
- **Pass (B):** states the question isn't answerable at that precision from the data;
  explains what *is* constrained (tidal deformability Λ̃ → an EOS-dependent radius *range*,
  model-dependent) and what isn't (remnant fate); cites.
- **Auto-check:** fabrication if a point radius ±<1 km is asserted; pass on explicit
  not-answerable + correct framing.

---

### G10 — Reproducibility

> **Show me, with runnable code, the chirp mass implied by GW150914's component masses,
> and propagate the mass uncertainties into the chirp-mass uncertainty.**

- **Axis:** Provenance, Uncertainty, Fabrication.
- **Trap:** quoting a chirp mass without showing the computation, or hand-waving the error
  propagation.
- **Typical fail (A):** states a number; code (if any) doesn't run or uses invented
  inputs.
- **Pass (B):** retrieves the component-mass posteriors from GWOSC, emits code that runs
  and reproduces the chirp mass with propagated (asymmetric) uncertainty, pins
  inputs/provenance.
- **Auto-check:** execute the emitted snippet; does it run and reproduce the value within
  tolerance using GWOSC-sourced inputs?

---

## Roll-up

Score each answer on the eight axes (`README.md`), per condition (bare / `/investigate`),
with cost captured. The general suite's headline numbers for a judge:

- **Fabrication count** across G1, G7, G9 (the invention traps) — target B = 0.
- **Premise/overinterpretation correction rate** across G5, G6, G8.
- **Citation validity rate** across G2, G4, G5, G6 (resolve + support-checked).
- **Rigor-per-kilotoken**, A vs B, to price it.
