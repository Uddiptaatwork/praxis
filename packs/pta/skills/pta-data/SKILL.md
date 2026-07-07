---
name: pta-data
description: How to retrieve real pulsar-timing-array (PTA) / nanohertz gravitational-wave-background values from the cited local snapshot. Use BEFORE answering ANY question about a PTA GWB parameter or release — the GWB characteristic-strain amplitude A (at gamma=13/3 / alpha=-2/3, f_ref=1/yr), the Hellings-Downs correlation significance, the Bayes factor or false-alarm probability, the number of pulsars, or the data timespan — for NANOGrav (15yr / NG15), EPTA (DR2), or IPTA (DR2), or any PTA release tag matching [A-Za-z]+-\w+, or any superlative across the PTA release set (highest/largest GWB amplitude so far, most significant detection). Trigger on the bare question itself, not only inside a command, so the answer comes from the provenance-stamped cache with a release DOI rather than recalled values. Tier REDERIVE means there is NO live PTA catalog API — a cache miss is an honest "not in the cached release set", never a recall and never a live fallback.
---

# PTA data access (tier REDERIVE — cache only, no live API)

Pulsar Timing Arrays detect the nanohertz gravitational-wave background (GWB) by
the correlated timing residuals of an array of millisecond pulsars. **There is no
live PTA catalog REST API** the way GWOSC exposes one for the LVK band. So this
pack is **oracle tier REDERIVE**: every served value is transcribed
deterministically from the published paper abstracts (Zenodo / journal DOIs) into
a frozen, provenance-stamped snapshot, and must byte-match on a second build.

## Cache first — this is the only retrieval path

The snapshot ships at `cache/pta_snapshot.json`. It is **retrieved data with
provenance, not recalled values** — it satisfies the integrity rules ("retrieve,
don't recall"; "identifiers are retrieved"). For any PTA GWB-parameter question,
read the snapshot or call the query helper, and report `best` with its asymmetric
error, the release DOI, the provenance string, the snapshot `retrieved_utc`, and
the scope.

```bash
C=packs/pta/cache/pta_snapshot.json
python lib/pcache.py entity NANOGrav-15yr --cache $C   # a release's parameters + provenance
python lib/pcache.py entity EPTA-DR2 --cache $C
python lib/pcache.py max A_gwb --cache $C              # superlative (scope IPTA-DR2)
python lib/pcache.py catalogs --cache $C               # releases + DOIs
python lib/pcache.py meta --cache $C                   # provenance / snapshot age
```

`lib/pcache.py` is the shared core query engine (no per-pack query code). It
prints each `best +upper/-lower unit`, the release DOI, a provenance string, and
`retrieved_utc`, through the Tier-0 serving filter (no bare numbers, no missing
provenance). The active pack's cache path is auto-resolvable (`PRAXIS_CACHE` /
`.praxis/active`), so `--cache` can be omitted once the pack is active. You may
instead read `cache/pta_snapshot.json` directly — `entities.<release>.parameters.<param>`
carries `best`, `upper_error`, `lower_error` (signed), `unit`, and a `note`; `_meta`
carries `source`, `retrieved_utc`, `dois`, and `cumulative_scope`.

Natural-language → command:
- "GWB amplitude / strain amplitude / A at gamma=13/3" → `A_gwb [release]`
- "how significant / Hellings-Downs significance / sigma" → `hd_significance_sigma [release]`
- "Bayes factor / evidence" → `bayes_factor [release]`; "false alarm probability" → `false_alarm_probability_pct [release]`
- "how many pulsars" → `n_pulsars [release]`; "how long / timespan" → `timespan_yr [release]`
- a release's amplitude/significance → pass the release tag (`NANOGrav-15yr`/`NG15`, `EPTA-DR2`, `IPTA-DR2`)

## What is in the cached release set

| Release | What it is | DOI | HD detection? |
|---|---|---|---|
| `NANOGrav-15yr` (NG15) | NANOGrav 15-year data set, Agazie et al. 2023 ApJL 951 L8 | 10.5281/zenodo.8423265 | yes (~3.5–4 σ frequentist; Bayes factor > 10¹⁴) |
| `EPTA-DR2` | EPTA Data Release 2, Paper III (A&A 678, A50) | 10.5281/zenodo.8091568 | yes on 10.3-yr DR2new subset (BF 60, FAP ~0.1%, ≥3 σ) |
| `IPTA-DR2` | IPTA DR2 **cross-PTA context** (arXiv:2201.03980) | 10.5281/zenodo.8091568 | **NO** — common-spectrum process only, not a confirmed HD GWB |

`cumulative_scope = IPTA-DR2` is the cross-PTA default scope for superlatives.

## The scope trap (non-negotiable)

- **A common-spectrum process (CURN) is NOT a Hellings-Downs detection.** IPTA DR2
  found a common-spectrum process but **no significant HD correlation** — its
  amplitudes are cross-PTA context, never a confirmed GWB. The snapshot flags
  `IPTA-DR2` with `context_only: true`; carry that flag into any answer.
- **Resolve the right release; never naively cross-combine.** Amplitudes are
  reported at different spectral indices (IPTA carries both a free-index
  `A_gwb_free_index = 3.8e-15` and a gamma=13/3 `A_gwb = 2.8e-15`); only compare
  amplitudes at the same spectral index, and always report which release.
- **Report the scope explicitly** with every superlative.

## Tier REDERIVE: a cache miss is an honest absence, never a recall

There is **no live fallback**. If the requested release or parameter is not in the
cached set, `lib/pcache.py` exits non-zero with *"not in the cached release set"* — say
exactly that. Do **not** recall a number, do **not** invent a DOI, do **not** reach
for a live API (there is none). Past the snapshot's hard-expiry, treat the cache as
expired and re-verify rather than serving it as authoritative.

## Provenance rule

Every served value MUST carry: `best` + asymmetric error + unit, the **release
DOI**, the snapshot `retrieved_utc`, and the scope. The query helper composes this;
if you read the JSON directly, compose it the same way.
