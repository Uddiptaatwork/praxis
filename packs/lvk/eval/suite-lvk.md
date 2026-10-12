# Suite: GW-specific (Siren)

Tests only an expert would design and only a grounded harness can pass. These exploit the
specific ways base LLMs fail on gravitational-wave questions — stale recall, fabricated
posteriors, hand-typed DOIs, superlative-scope bugs, overinterpreted headlines, frame
confusion — against the one thing that makes GW eval rigorous: **GWOSC is a queryable
oracle**, so fabrication and fidelity are scored by diffing the catalog, not by opinion.

See [`README.md`](README.md) for protocol, axes, cost. Ground truth is the named GWOSC
query, fetched at grade time — never hardcoded here (rule #2/#9).

---

### S1 — Post-cutoff event retrieval ★ demo

> **Summarize the source properties of the most recently published O4 binary-black-hole
> event in GWTC, with uncertainties and provenance.**

- **Axis:** Retrieval-vs-recall, Provenance, Uncertainty, Scope.
- **Why it's decisive:** pick an event published *after* the base model's training cutoff.
  The baseline **cannot** know it — any specific answer is fabrication; the only honest
  baseline answer is "I don't have it." Praxis retrieves it. This is the cleanest,
  least-arguable win in the suite.
- **Typical fail (A):** invents parameters for a recent-sounding event, or names a stale
  pre-cutoff one.
- **Pass (B):** retrieves the actual latest event, params with asymmetric CIs + catalog
  DOI; correctly identifies it as post-cutoff.
- **Ground truth:** GWOSC catalog query for the most recent confident event; grader
  confirms its publication date is after the base model's cutoff.
- **Auto-check:** fabrication if A asserts specific params; B must match GWOSC within σ and
  carry the DOI.

---

### S2 — Cumulative-scope / superlative trap ★ demo

> **What is the most distant binary black hole merger detected so far, and how well is that
> distance actually measured?**

- **Axis:** Scope, Retrieval-vs-recall, Uncertainty, Provenance.
- **Trap:** "so far" = cumulative — must use the umbrella `GWTC` record, not a single
  release. Distance is uncertainty-dominated (distance–inclination degeneracy, SNR-limited).
  This is the exact bug `comparison-set-1.md` caught: a release-scoped answer is wrong even
  if internally consistent.
- **Typical fail (A):** names a famous/flashy stale event (e.g. GW190521) with no source.
- **Also fails (B, if scope rule doesn't fire):** picks the most-distant within *one*
  release instead of cumulative.
- **Pass (B):** cumulative most-distant event with asymmetric redshift/distance CI + DOI;
  flags that high-z events are prior/SNR-limited and that d_L→z assumes a cosmology.
- **Ground truth:** GWOSC max-redshift query across **all** catalogs.
- **Auto-check:** does the named event match the cumulative GWOSC argmax? Catalog-name
  present and correct?

---

### S3 — Numerical fidelity vs GWOSC posteriors

> **Give the source-frame component masses and effective spin of GW190521, with 90%
> credible intervals.**

- **Axis:** Fabrication, Uncertainty, Provenance, Retrieval-vs-recall.
- **Trap:** the temptation to recall round numbers ("85 and 66") without the real
  asymmetric posterior or the source frame / DOI.
- **Pass (B):** values match the GWOSC posterior within σ, asymmetric CIs, source-frame
  stated, catalog DOI attached.
- **Ground truth:** GWOSC GW190521 posteriors (component masses, χ_eff).
- **Auto-check:** σ-distance `|stated − gwosc|/gwosc_σ` for each value; fabrication if any
  CI excludes the GWOSC median or no DOI.

---

### S4 — Nonexistent-event trap ★ demo

> **Summarize the parameter-estimation results for GW230''[absent]''.** *(Use a
> plausible-looking ID the grader has first confirmed is absent from every GWOSC catalog;
> a structurally-impossible date like `GW250230_120000` is the easy variant.)*

- **Axis:** Fabrication, Retrieval-vs-recall, Provenance.
- **Why it's decisive:** the visceral "this one won't lie" demo. A grounded harness reports
  the event isn't in GWOSC; an ungrounded one confabulates a full PE table.
- **Typical fail (A):** invents masses, spins, distance, a DOI — a complete fabricated
  posterior.
- **Pass (B):** states the ID is not found in GWOSC and declines to fabricate; optionally
  suggests close real events.
- **Ground truth:** GWOSC lookup returns empty for the chosen ID (grader verifies absence
  before the run).
- **Auto-check:** any specific PE numbers for the absent ID = fabrication; pass on explicit
  not-found.

---

### S5 — Mass-gap overinterpretation ★ demo

> **GW230529 has been described as a black hole in the lower mass gap (~3–5 M☉). How solid
> is that interpretation?**

- **Axis:** Skepticism, M/I/S separation, Citations, Provenance.
- **Trap:** the claim stacks three uncertain layers — (1) the individual-mass split is
  prior/waveform-dependent and single-detector; (2) BH-vs-heavy-NS is unresolved; (3) the
  gap's very existence is debated.
- **Typical fail (A):** restates the headline ("yes, exciting mass-gap object").
- **Pass (B):** separates the tight chirp mass (measured) from the prior-sensitive
  component masses (inferred) from formation (speculative); surfaces spin-prior shift,
  single-detector caveat, NSBH-vs-BNS ambiguity, and the gap-existence debate; cites the
  discovery + the prior-impact and no-gap rebuttal papers.
- **Ground truth:** GWOSC GW230529 posteriors (chirp mass tight; component masses broad).
- **Auto-check:** rubric for the three layers + caveats; citations resolve and support.

---

### S6 — Distance–inclination degeneracy

> **How well is the luminosity distance of a typical high-redshift BBH actually measured,
> and why?**

- **Axis:** Skepticism, M/I/S separation, Uncertainty.
- **Trap:** distance is degenerate with inclination from the (2,2) mode alone; fractional
  errors are large (often 30–80%).
- **Typical fail (A):** quotes a distance as if precise; omits the mechanism.
- **Pass (B):** explains the degeneracy, what breaks it (higher modes, precession, EM
  counterpart, network geometry) and why it usually doesn't for low-SNR distant events;
  reports realistic fractional uncertainty.
- **Auto-check:** rubric — degeneracy named, breaking mechanisms listed, uncertainty
  quantified.

---

### S7 — Standard-siren H₀ (bright vs dark)

> **What is the Hubble constant from gravitational-wave standard sirens, and how does the
> measurement work?**

- **Axis:** Provenance, Uncertainty, M/I/S separation, Citations.
- **Trap:** conflating the GW170817 *bright*-siren (EM-host) measurement with *dark*-siren
  statistical methods; quoting a value without its (large) CI or its assumptions.
- **Pass (B):** distinguishes bright vs dark siren; gives the value(s) with asymmetric CIs;
  states the method is independent of the cosmic-distance ladder; notes it doesn't yet
  resolve the Hubble tension; cites.
- **Ground truth:** GW170817 H₀ posterior + latest dark-siren combined constraint (via
  literature-reader / GWOSC cosmology products).
- **Auto-check:** value within CI of source; both methods distinguished; citations resolve.

---

### S8 — Population vs single-event inference

> **Is there a peak in the black-hole mass distribution around 35 M☉, and what does it
> mean?**

- **Axis:** M/I/S separation, Skepticism, Citations, Provenance.
- **Trap:** a *population* feature (from a hierarchical fit subject to selection effects)
  must not be argued from individual events; the ~35 M☉ peak is a population-level
  inference, and its interpretation (PPISN pile-up vs other) is contested.
- **Pass (B):** frames it as population inference, names the selection-effect /
  Malmquist-bias caveat, separates the measured feature from its disputed interpretation,
  cites the population paper(s).
- **Auto-check:** rubric — population vs single-event distinction, selection effects named.

---

### S9 — EOS / tidal deformability (measurement vs inference)

> **What did GW170817 tell us about the neutron-star equation of state?**

- **Axis:** M/I/S separation, Uncertainty, Citations, Provenance.
- **Trap:** the *measurement* is the (combined) tidal deformability Λ̃ with an upper
  bound; the *inference* to radius/EOS is model-dependent; stating a radius as measured is
  the error.
- **Pass (B):** reports the Λ̃ constraint (measurement) with its bound, then the
  EOS/radius implication as a model-dependent inference, with the assumptions and a
  citation.
- **Ground truth:** GW170817 tidal-deformability posterior / bound.
- **Auto-check:** Λ̃ value/bound present with CI; radius framed as inference; citations
  resolve.

---

### S10 — Data-quality / detector systematics

> **GW170817 had a loud glitch in Livingston near merger. How was it handled and does it
> affect the science?**

- **Axis:** Skepticism, Reproducibility, Provenance.
- **Trap:** ignoring data-quality entirely; a working analyst knows glitch subtraction and
  its residual-systematic implications.
- **Pass (B):** describes the glitch subtraction, the residual-uncertainty caveat, and
  that it's a recognized systematic in the published analysis; cites the detchar/data-quality
  source.
- **Auto-check:** rubric — glitch handling named + systematic acknowledged + sourced.

---

### S11 — Significance / false-alarm discipline

> **Is [a named marginal/sub-threshold trigger] a real astrophysical event?**

- **Axis:** Skepticism, M/I/S separation, Provenance.
- **Trap:** treating a marginal trigger as a confident detection; ignoring FAR / p_astro
  and the confident-vs-marginal catalog distinction.
- **Pass (B):** cites FAR and p_astro, places it in the right (marginal) catalog, states
  detection confidence rather than asserting reality.
- **Ground truth:** GWOSC p_astro / FAR and catalog membership for the chosen trigger.
- **Auto-check:** does the answer cite p_astro/FAR and the correct catalog tier?

---

### S12 — Frame & units correctness

> **Are the published GW190521 component masses source-frame or detector-frame, and what's
> the difference here?**

- **Axis:** Provenance, M/I/S separation, Uncertainty.
- **Trap:** the redshift correction (`m_source = m_det / (1+z)`) is exactly the kind of
  convention experts use to separate the careful from the sloppy; at z≈0.8 it's a large
  factor.
- **Pass (B):** states the catalog default is source-frame, gives the relation, notes the
  redshift's own uncertainty propagates into the source-frame mass, with provenance.
- **Auto-check:** rubric — correct frame, correct relation, redshift-uncertainty caveat.

---

## Roll-up

The GW suite's headline numbers for a judge:

- **Fabrication count** across S1, S3, S4 (the invention traps) — target B = 0; the
  S4 nonexistent-event result is the single most persuasive cell in the table.
- **Retrieval win** — S1 + S2: fraction correct where the baseline provably *cannot* recall
  (post-cutoff / cumulative-scope). Report bare vs `/investigate` separately.
- **Numerical fidelity** — median σ-distance across S3 (and any other retrievable-value
  test); show the distribution, not just a pass/fail.
- **Provenance + citation validity** — fraction of numbers with resolvable GWOSC DOIs and
  fraction of citations that resolve *and* support the claim.
- **Cost-normalized** — rigor-per-kilotoken and cost-per-fabrication-avoided, A vs B.
