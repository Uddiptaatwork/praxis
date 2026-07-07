# Praxis A/B evaluation — aggregated results

_Generated: 2026-06-18T15:01:43Z_  
_GWOSC network status: **ok**_  
_Matrix: 3 prompts x 3 reps x 2 harnesses = 18 runs_  

Harnesses: **A = baseline** (`claude -p`), **B = Praxis** (`claude --plugin-dir`). Both run from a neutral cwd so the baseline does not inherit the project CLAUDE.md. All scoring is objective (regex + numeric diff vs the LIVE GWOSC catalog); no LLM-judge.

## Live GWOSC ground truth

| Prompt | Event | Catalog | m1_source | m2_source |
|---|---|---|---|---|
| P1 | GW150914 | GWTC-2.1-confident | 34.6 +4.4/-2.6 | 30.0 +2.9/-4.6 |
| P2 | GW190521 | GWTC-2.1-confident | 98.4 +33.6/-21.7 | 57.2 +27.1/-30.1 |
| P3 | GW230529_181500 | GWTC-4.1 | 3.66 +0.82/-1.21 | 1.42 +0.6/-0.22 |

## Overall per harness (the headline)

| Metric | A (baseline) | B (Praxis) |
|---|:--:|:--:|
| Runs (ok / total) | 9/9 | 9/9 |
| provenance_rate (GWOSC DOI) | 0% (0/9) | 89% (8/9) |
| current_catalog_match_rate | 86% (6/7) | 100% (9/9) |
| asymmetric_uncertainty_rate | 22% (2/9) | 100% (9/9) |
| cost_usd (mean +/- std) | 0.0592 ± 0.0186 | 0.0838 ± 0.0384 |
| duration_s (mean +/- std) | 30.7 ± 8.2 | 27.6 ± 13.7 |
| output_tokens (mean +/- std) | 1286 ± 419 | 918 ± 459 |

## Per-prompt m1 consistency (mean +/- std across 3 reps)

Lower std = more reliable / less drift across repetitions.

| Prompt | Event | A m1 mean+/-std | B m1 mean+/-std | GWOSC m1 |
|---|---|:--:|:--:|:--:|
| P1 | GW150914 | 35.60 ± 0.00 | 34.60 ± 0.00 | 34.6 |
| P2 | GW190521 | 106.80 ± 30.55 | 98.40 ± 0.00 | 98.4 |
| P3 | GW230529 | 4.30 ± 0.70 | 3.66 ± 0.00 | 3.66 |

## Full per-prompt x harness table

| Prompt | Harness | prov_rate | match_rate | asym_rate | m1 mean+/-std | m2 mean+/-std | cost_usd | dur_s | out_tok | statuses |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| P1 | A | 0% (0/3) | 100% (2/2) | 33% (1/3) | 35.60 ± 0.00 | 30.60 ± 0.00 | 0.0393 ± 0.0050 | 27.3 ± 8.4 | 1127 ± 351 | ok,ok,ok |
| P1 | B | 67% (2/3) | 100% (3/3) | 100% (3/3) | 34.60 ± 0.00 | 30.00 ± 0.00 | 0.0672 ± 0.0130 | 26.5 ± 4.5 | 892 ± 190 | ok,ok,ok |
| P2 | A | 0% (0/3) | 67% (2/3) | 33% (1/3) | 106.80 ± 30.55 | 87.33 ± 30.17 | 0.0563 ± 0.0046 | 39.2 ± 1.0 | 1724 ± 167 | ok,ok,ok |
| P2 | B | 100% (3/3) | 100% (3/3) | 100% (3/3) | 98.40 ± 0.00 | 57.20 ± 0.00 | 0.1048 ± 0.0554 | 38.8 ± 17.7 | 1270 ± 603 | ok,ok,ok |
| P3 | A | 0% (0/3) | 100% (2/2) | 0% (0/3) | 4.30 ± 0.70 | 1.40 ± 0.00 | 0.0820 ± 0.0081 | 25.6 ± 4.6 | 1008 ± 286 | ok,ok,ok |
| P3 | B | 100% (3/3) | 100% (3/3) | 100% (3/3) | 3.66 ± 0.00 | 1.42 ± 0.00 | 0.0792 ± 0.0213 | 17.5 ± 0.4 | 592 ± 8 | ok,ok,ok |

## Per-run detail

| Run | status | DOI | asym | m1 | m2 | m1_match | cost_usd | dur_s | out_tok |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| P1_A_1 | ok | - | - | null | null | ? | 0.0330 | 16.7 | 633 |
| P1_A_2 | ok | - | Y | 35.6 | 30.6 | Y | 0.0453 | 37.2 | 1414 |
| P1_A_3 | ok | - | - | 35.6 | 30.6 | Y | 0.0397 | 28.1 | 1334 |
| P1_B_1 | ok | Y | Y | 34.6 | 30.0 | Y | 0.0687 | 26.6 | 822 |
| P1_B_2 | ok | - | Y | 34.6 | 30.0 | Y | 0.0507 | 21.0 | 703 |
| P1_B_3 | ok | Y | Y | 34.6 | 30.0 | Y | 0.0824 | 32.0 | 1152 |
| P2_A_1 | ok | - | - | 150.0 | 130.0 | N | 0.0518 | 38.1 | 1768 |
| P2_A_2 | ok | - | Y | 85.0 | 66.0 | Y | 0.0544 | 39.0 | 1904 |
| P2_A_3 | ok | - | - | 85.4 | 66.0 | Y | 0.0626 | 40.5 | 1501 |
| P2_B_1 | ok | Y | Y | 98.4 | 57.2 | Y | 0.1830 | 63.7 | 2122 |
| P2_B_2 | ok | Y | Y | 98.4 | 57.2 | Y | 0.0615 | 27.4 | 811 |
| P2_B_3 | ok | Y | Y | 98.4 | 57.2 | Y | 0.0700 | 25.2 | 876 |
| P3_A_1 | ok | - | - | 5.0 | null | Y | 0.0718 | 20.0 | 692 |
| P3_A_2 | ok | - | - | 3.6 | 1.4 | Y | 0.0823 | 31.4 | 1385 |
| P3_A_3 | ok | - | - | null | null | ? | 0.0918 | 25.3 | 946 |
| P3_B_1 | ok | Y | Y | 3.66 | 1.42 | Y | 0.0939 | 17.6 | 588 |
| P3_B_2 | ok | Y | Y | 3.66 | 1.42 | Y | 0.0947 | 17.9 | 585 |
| P3_B_3 | ok | Y | Y | 3.66 | 1.42 | Y | 0.0491 | 17.0 | 603 |

## Refused / failed runs

None — all runs returned a non-empty result.
