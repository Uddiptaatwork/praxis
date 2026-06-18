# Automated A/B scorer (`score.py`)

> For the suite overview, methodology, scoring axes, and the full five-layer grader
> plan, see [`README.md`](README.md). This file is the concrete how-to for the one piece
> that is **built today**: running `score.py`. In grader terms, `score.py` implements
> layers 1–2 (regex presence + live-GWOSC diff); layers 3–5 (citation resolver, rubric
> LLM-judge, pass@k) are specified in `README.md` but not yet implemented here.

`score.py` is an objective, reproducible scorer for the Praxis-vs-vanilla
comparison sets ([`comparison-set-1.md`](comparison-set-1.md),
[`comparison-set-2.md`](comparison-set-2.md)). It parses the markdown, computes
regex/lookup-based metrics for each question and system, and verifies named GW
events against the **live public GWOSC API**.

It is **stdlib-only** (no `pip install`), runs on **Python 3.13**, and degrades
gracefully when the network is down.

## Usage

```bash
# Default path (eval/comparison-set-1.md):
python3 eval/score.py

# Explicit file:
python3 eval/score.py eval/comparison-set-1.md

# JSON to a file, human-readable table to another:
python3 eval/score.py eval/comparison-set-1.md > result.json 2> table.md
```

- **stdout** = machine-readable JSON (the full result object).
- **stderr** = a rendered markdown table (per-question, A vs B) plus the
  fabrication/correctness findings. It is on stderr so it never pollutes the JSON.

## Input format expected

The scorer slices the file on `## Q<N> — <title>` headers. Within each question
section it extracts:

- the blockquoted prompt (`> ...`),
- the `<details>` "Ground-truth key" block,
- the fenced code block after `**A — vanilla:**` (system A),
- the fenced code block after `**B — plugin:**` (system B).

Anything after the last question (e.g. the "Results & scoring" section) is ignored.

## What is auto-scored (objective only)

Per question, per system:

1. **Provenance — GWOSC DOI present.** Counts GWOSC DOIs (`10.7935/...`).
2. **Uncertainty — asymmetric errors.** Counts asymmetric error notation like
   `+21/−14` or `+6.1/-4.2` (handles unicode minus). Reports examples.
3. **Catalog scope.** Lists `GWTC-<n>(.<m>)` releases cited, and whether the
   cumulative/umbrella `GWTC` catalog (or the word "cumulative") is referenced.
4. **Citations.** Counts arXiv ids and DOIs separately. Flags
   `hand_typed_identifier_risk = true` when arXiv ids are present but **no DOI** is
   — i.e. the citations are hand-typed identifiers with no retrieved source.
5. **Fabrication / correctness (headline).** Extracts event names (`GW######` or
   `GW######_######`) and, via the GWOSC API:
   - checks each event **exists** (`/api/v2/events/<name>`; 404 = not found),
   - for **superlative** questions (e.g. "most distant"), checks whether the named
     event is the **true cumulative extremum** by paging the umbrella catalog
     (`/api/v2/catalogs/GWTC/events?include-default-parameters=true&page-size=20`,
     following `next`), comparing `redshift` / `total_mass_source` /
     `luminosity_distance`. If not, it reports the true extremum event + value.

### Superlative configuration

Which questions are "superlative" (and on which parameter) is set in
`SUPERLATIVE_CONFIG` in `score.py`, keyed by question id. `Q1` is configured as a
`redshift` `max` question. There is also a light prompt-text heuristic fallback for
unconfigured questions. Extend the config when adding new comparison sets.

## What is NOT auto-scored

Subjective axes are **never** given a fabricated score. They are emitted as `null`
in JSON and labeled `manual` in the table:

- Measurement / inference / speculation separation
- Skepticism quality (priors, systematics, selection effects)
- Retrieval-vs-recall (not observable from text alone)

These need a human or an LLM judge — i.e. grader layers 3–5 in
[`README.md`](README.md#the-automatable-grader-build-order), which are specified but not
yet built.

## Network handling

- Uses `urllib` + `json` only.
- Retries transient `5xx` (the GWOSC proxy intermittently returns `502`) with
  backoff; treats `404` as a definitive "not found".
- Caches the cumulative-catalog scan and per-event lookups for the run.
- If the API is unreachable, `network_status` becomes `unreachable`, all
  regex-based metrics are still emitted, and every fabrication check is reported as
  `"unverified"` (never as a pass/fail).

## Known result for comparison-set-1

- GWOSC DOIs: **0** in every block (neither system cited a GWOSC DOI — a finding
  in itself; both rely on arXiv ids, flagged as hand-typed-identifier risk).
- Asymmetric errors: **0/0/0** for A vs **3/4/2** for B (Q1/Q2/Q3) — B reports
  uncertainty, A does not.
- Fabrication headline: **B-Q1's `GW230704_212616` is NOT the cumulative
  most-distant** — the true `redshift` extremum is **`GW190403_051519` (z = 1.18)**.
  A-Q1's `GW190521` is also wrong (z ≈ 0.82). This is the cumulative-scope bug the
  comparison set was designed to catch.
