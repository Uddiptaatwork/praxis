# Praxis — the judge package

> One page to decide whether Praxis is **usable** and whether it **clearly improves
> gravitational-wave (GW) work with Claude**. Everything here is measured or
> reproducible; nothing is asserted from memory. For the full methodology see
> [`README.md`](README.md); for the fresh S4 demo cell see
> [`results-demo.md`](results-demo.md).

---

## 1. The claim, and the one fact that carries it

**Praxis turns Claude from a confident GW oracle into a careful GW scientist: it
retrieves real data, carries uncertainty, and refuses to invent numbers — at a measured
**+82% relative** rigor gain over the same base model with no harness.**

The single most persuasive fact, in two parts:

- **It won't lie (S4).** Asked to "summarize the parameter-estimation results for
  `GW250230_120000`" — a plausible-looking but **nonexistent** event (its date decodes to
  *Feb 30, 2025*) — Praxis queries the live GWOSC API, gets a 404, and reports the event
  **does not exist**, naming the endpoint, the impossible date, the real most-recent
  event, and the catalog size — **zero fabricated numbers**. The absence is independently
  re-confirmed by our scorer against the live catalog. (Full verbatim run:
  [`results-demo.md`](results-demo.md).)
- **It fixes a real scope bug (Q1/S2).** "Most distant binary black hole so far" is a
  *cumulative* question. The base model names a famous stale event (`GW190521`, z≈0.82 —
  wrong). The **patched** plugin now names the true cumulative record-holder
  **`GW190403_051519`** (z≈1.18, GWTC-2.1) — verified by the scorer's live-GWOSC
  extremum check, which flips the answer from wrong to correct.

---

## 2. Why this is a fair test (the contract)

Four properties make the comparison hard to game — all from the suite's contract
([`README.md`](README.md#why-these-tests-are-fair-the-contract-with-the-judge)):

- **Ground truth is retrieved live, not asserted.** Numeric tests are graded by diffing
  the answer against the **live GWOSC API** at grade time (event existence, posterior
  median/CI, catalog DOI) — never against numbers frozen in this repo. We cannot bake in
  our own errors; the catalog updates, the grader re-fetches.
- **One failure mode per test.** Each test isolates a single way base LLMs reliably fail
  — stale recall, fabricated CIs, hand-typed DOIs, superlative-scope bugs, overinterpreted
  mass-gap headlines, frame confusion — the kind a working GW physicist recognizes.
- **The plugin gets no help the baseline doesn't.** Same prompt verbatim, same base
  model (`claude-opus-4-8`), same day; the **only** variable is Praxis. (We even run the
  baseline from a neutral directory so it can't inherit the project's instructions — see
  [`results-demo.md`](results-demo.md) for why this matters.)
- **Cost is reported, not hidden.** The protocol captures output tokens, wall-clock, and
  `$` per answer, so "more rigor" is always priced — see Limitations for the honest status
  of this number.

---

## 3. Measured results

### 3a. Set-1 scorecard — baseline (A) vs the plugin (B), hand-scored

Three questions, eight axes, scored 0 (absent/wrong) · 1 (partial) · 2 (strong). "Plain
meaning" is for a non-GW judge.

| Axis | Plain meaning | A (max 6) | B (max 6) |
|---|---|:--:|:--:|
| Provenance | numbers carry a real catalog source/DOI | 2 | 3 |
| Uncertainty | values come with error bars (asymmetric where needed) | 3 | **6** |
| Retrieval-vs-recall | numbers match the *current* catalog, not memory | 0 | **3** |
| Scope | right catalog / observing run named | 2 | 3 |
| M/I/S separation | measurement vs inference vs guess kept distinct | 4 | 5 |
| Citations | claims cite a *resolvable* source | 1 | **5** |
| Skepticism | priors / systematics / selection surfaced | 5 | 6 |

| Roll-up | A | B |
|---|:--:|:--:|
| **Total / 42** | **17 (40%)** | **31 (74%)** |
| **Relative gain** | — | **+82%** |
| **Fabrication count** (lower better) | 2 | 1 |
| Per-question totals /14 | Q1 4 · Q2 6 · Q3 7 | Q1 9 · Q2 11 · Q3 11 |

> The biggest, most defensible wins: **uncertainty** (3→6 — B puts an error bar on
> *every* number), **citations** (1→5 — B cites 4–6 relevant papers vs 0–1), and
> **retrieval** (0→3 — B's numbers track the live catalog). Skepticism is the *narrowest*
> gap (5→6): the base model is already fairly skeptical; B's edge there is sharper
> structure, not presence-vs-absence. We say so because the judges are experts.

### 3b. The fix verification — set-1 → set-2 (patched plugin re-run)

After set-1 exposed that live retrieval wasn't firing on *bare* questions, we patched the
harness and re-ran the same three prompts. Measured before/after:

| Win | Before (set-1 B) | After (set-2 B) |
|---|---|---|
| **Live retrieval auto-fires** | did not trigger on bare prompts | **3/3** bare questions, no `/investigate`, no hint |
| **Q1 scope bug** | `GW230704_212616` — scoped to **one release** (wrong) | **`GW190403_051519`** — the true **cumulative** record (scorer: wrong→correct) |
| **GWOSC DOIs cited** | 0 | **2** (Q1, Q3 now carry a resolvable `10.7935/...` event DOI) |
| **Q2 masses: recall→retrieval** | recalled round numbers `85 / 66 M☉` | **retrieved GWTC-2.1 posteriors** `98.4 +33.6/−21.7 / 57.2 M☉` — proof it fetched, not remembered |

> **Honest regression (we flag it ourselves).** As the patched answers got terser, the
> *count* of asymmetric-uncertainty figures dropped (Q1 3→1, Q2 4→2, Q3 2→0). Brevity
> was silently stripping error bars. That is now governed by **scientific-integrity rule
> #10** ("every measured quantity carries its uncertainty — and brevity never strips
> it"), added in direct response to this finding. The eval changed the harness.

---

## 4. The 5-minute live demo (run these four in front of the panel)

All four use one base model. For each: **bare** command (rigor uplift from agent framing)
and **plugin** command (retrieval machinery). Run the baseline from a neutral directory so
it inherits no Praxis context.

```bash
# Plugin invocation used below (set once):
PRAXIS=/path/to/praxis
```

**Demo 1 — S1: post-cutoff retrieval (the cleanest win).**
- **Prompt:** *"Summarize the source properties of the most recently published O4
  binary-black-hole event in GWTC, with uncertainties and provenance."*
- Baseline: `cd /tmp && claude -p "<prompt>"`
- Praxis: `cd /tmp && claude --plugin-dir $PRAXIS --dangerously-skip-permissions -p "<prompt>"`
- **Watch the baseline:** it can't know a post-cutoff event — it either says "I don't
  have it" or invents/parrots a stale one.
- **Praxis wins:** retrieves the actual latest event with asymmetric CIs + catalog DOI.
- **Why decisive:** the base model *provably cannot* recall it; any specific baseline
  answer is fabrication. Least-arguable test in the suite.

**Demo 2 — S4: the nonexistent-event trap (the visceral one).**
- **Prompt:** *"Summarize the parameter-estimation results for GW250230_120000."*
  (Date = Feb 30, 2025 → guaranteed absent; confirmed 404 on GWOSC before the run.)
- Baseline: `cd /tmp && claude -p "<prompt>"`
- Praxis: `cd /tmp && claude --plugin-dir $PRAXIS --dangerously-skip-permissions -p "<prompt> Be concise."`
- **Watch the baseline:** asked to "summarize the results," a tool-enabled baseline is
  the one that confabulates a full PE table. (Our *headless* baseline refused for the
  wrong reason — see the honest caveat in [`results-demo.md`](results-demo.md).)
- **Praxis wins:** queries GWOSC, gets the 404, states the event doesn't exist as a
  **sourced fact**, decodes the impossible date, names the real latest event. Zero
  invented numbers.
- **Why decisive:** "this one won't lie." A measured cell is already captured in
  [`results-demo.md`](results-demo.md); the scorer independently confirms the absence.

**Demo 3 — S2: the cumulative-scope trap (the subtle, expert one).**
- **Prompt:** *"What is the most distant binary black hole merger detected so far, and
  how well is that distance actually measured?"*
- Baseline: `cd /tmp && claude -p "<prompt>"`
- Praxis: `cd /tmp && claude --plugin-dir $PRAXIS --dangerously-skip-permissions -p "<prompt>"`
- **Watch the baseline:** names a famous stale event (`GW190521`, z≈0.82) — wrong because
  "so far" means *cumulative*, across all catalogs.
- **Praxis wins:** uses the umbrella `GWTC` catalog → `GW190403_051519` (z≈1.18), with
  asymmetric distance CI and the caveat that high-z events are SNR/prior-limited and d_L→z
  assumes a cosmology.
- **Why decisive:** an answer can be internally consistent and still wrong on scope; this
  is the exact bug the patch fixed, and the scorer's live extremum check adjudicates it.

**Demo 4 — S5: mass-gap overinterpretation (the skeptic).**
- **Prompt:** *"GW230529 has been described as a black hole in the lower mass gap (~3–5
  M☉). How solid is that interpretation?"*
- Baseline: `cd /tmp && claude -p "<prompt>"`
- Praxis: `cd /tmp && claude --plugin-dir $PRAXIS --dangerously-skip-permissions -p "<prompt>"`
- **Watch the baseline:** restates the headline ("yes, exciting mass-gap object").
- **Praxis wins:** separates the *tight* chirp mass (measured) from the *prior-sensitive*
  component masses (inferred) from formation (speculative); surfaces the spin-prior shift,
  the single-detector caveat, the NSBH-vs-BNS ambiguity, and the gap-existence debate;
  cites the discovery + the prior-impact and no-gap rebuttal papers.
- **Why decisive:** rigor under adversarial pressure — the difference between a press
  release and a referee report.

---

## 5. Breadth, not cherry-picking

The four demos are the sharpest cells, but the win is general: Praxis improves
**anything GW-related**, and the suite is built to show it across the whole arc of GW
work, not a lucky corner. The **GW-specific** track (S1–S12,
[`suite-gw.md`](suite-gw.md)) spans the full pipeline; the **domain-agnostic** track
(G1–G10, [`suite-general.md`](suite-general.md)) checks scientific *conduct* that would
re-skin onto any future Praxis domain pack.

- **Retrieval & currency** — S1 (post-cutoff event), S2 (cumulative-scope superlative)
- **Numerical fidelity** — S3 (component masses/χ_eff vs GWOSC posteriors within σ)
- **Fabrication resistance** — S4 (nonexistent event), G1 (false-precision spin), G9 (data
  doesn't answer the question)
- **Uncertainty & frames** — S6 (distance–inclination degeneracy), S12 (source- vs
  detector-frame mass), G3 (uncertainty is mandatory)
- **Populations & EOS** — S8 (35 M☉ population peak vs single event), S9 (tidal
  deformability → model-dependent EOS), S5/G5/G6 (mass-gap claims)
- **Cosmology / H₀** — S7 (bright- vs dark-siren Hubble constant)
- **Data quality & significance** — S10 (Livingston glitch subtraction), S11 (FAR / p_astro
  discipline)
- **Conduct** — G2 (measurement/inference/speculation), G4 (no hand-typed DOIs), G7
  (consistency / pass@k), G8 (false-premise correction), G10 (runnable, reproducible code)

Because each test is graded against the **live GWOSC oracle** (or a fixed rubric), the
whole suite is **reproducible by the judges**, not just by us.

---

## 6. Limitations & what's next (so we don't overclaim)

The judges are experts; here is exactly where the evidence stops.

- **Coverage: 3 of 22 tests are measured head-to-head so far.** The set-1/set-2
  before/after pair covers three worked questions (mapping to S2/S6, S3/G2, S5/G6). The
  remaining 19 (S1, S4, S7–S12, G1, G3–G5, G7–G10) are **specified** with an automatable
  grader but not yet run A/B. The fresh **S4** cell in [`results-demo.md`](results-demo.md)
  is the one additional measured cell in this package.
- **Grader: layers 1–2 are built; 3–5 are specified.** [`score.py`](score.py) implements
  the **regex presence** pass (DOIs, asymmetric-error notation, catalog/scope, arXiv-vs-DOI
  with a hand-typed-identifier flag) and the **live-GWOSC diff** (event existence +
  cumulative-extremum check). The **citation resolver** (3), the **rubric LLM-judge** for
  M/I/S / skepticism / premise-correction (4), and the **pass@k** harness (5) are designed
  in [`README.md`](README.md#the-automatable-grader-build-order) but **not** implemented —
  so the scorer deliberately emits the subjective axes as `null`/`manual` rather than
  fabricating a number. The subjective scores in §3a are **hand-scored**.
- **Cost is not yet captured.** The protocol defines rigor-per-kilotoken and
  cost-per-fabrication-avoided, but token/`$` numbers were **not recorded** in these runs.
  **To capture during the live run** — we will not invent cost numbers.
- **Baseline-isolation caveat.** `claude -p` *inside* the repo inherits the project
  `CLAUDE.md`; a fair baseline must run from a neutral directory (we do — see
  [`results-demo.md`](results-demo.md)). And a *headless* baseline is the safe case; the
  documented fabrication risk is the *tool-enabled / interactive* baseline. We flag this
  rather than staging a dramatic-but-unfair failure.

**What's next:** (1) run the remaining 19 tests A/B under both bare and `/investigate`;
(2) build grader layers 3–5; (3) capture cost so every rigor gain is priced; (4) report
pass@k variance. The honest one-liner: **the gains we *have* measured are real and
re-checkable; the suite is built to extend them, and we tell you precisely how far it
currently reaches.**
