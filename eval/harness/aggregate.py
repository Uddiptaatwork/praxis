#!/usr/bin/env python3
"""Aggregate objective scores + judge verdicts into a paired scorecard.

Pairing unit = (question, model, effort, repeat): vanilla vs praxis on the
identical cell. We report, per metric: vanilla mean, praxis mean, the paired
mean difference (praxis - vanilla), and a 95% bootstrap CI over pairings.
A difference whose CI crosses 0 is NOT a win -- it is reported as inconclusive,
per the integrity rule "an interval that spans two conclusions is not a discovery".

Outputs:
  results/scorecard.md   human-readable
  results/pairings.csv   one row per pairing (for your own stats)

Usage: python aggregate.py
"""
import csv
import json
import random

from common import load_questions, SCORES_DIR, JUDGE_DIR, RESULTS_DIR

OBJ_METRICS = ["has_source", "uncertainty", "trap_handled", "fabrication_risk",
               "n_citations", "factual_match"]
# Metrics where a LOWER value is better (so a negative paired Δ favors praxis).
REVERSE_CODED = {"fabrication_risk"}
JUDGE_DIMS = ["provenance", "uncertainty", "trap_handling", "correctness"]


def as_num(v):
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    return None


def boot_ci(diffs, n=2000, seed=12345):
    diffs = [d for d in diffs if d is not None]
    if len(diffs) < 2:
        return (None, None)
    rng = random.Random(seed)
    k = len(diffs)
    means = sorted(sum(diffs[rng.randrange(k)] for _ in range(k)) / k for _ in range(n))
    return (round(means[int(0.025 * n)], 3), round(means[int(0.975 * n)], 3))


def verdict(lo, hi, higher_better=True):
    if lo is None:
        return "n/a"
    if higher_better:
        if lo > 0:
            return "praxis better"
        if hi < 0:
            return "vanilla better"
    else:  # lower is better: a significantly negative Δ favors praxis
        if hi < 0:
            return "praxis better"
        if lo > 0:
            return "vanilla better"
    return "inconclusive (CI crosses 0)"


def load_objective():
    p = SCORES_DIR / "_all_scores.json"
    return json.loads(p.read_text()) if p.exists() else []


def load_verdicts():
    p = JUDGE_DIR / "_all_verdicts.json"
    return json.loads(p.read_text()) if p.exists() else []


def pair_objective(scores):
    """{(qid,model,effort,repeat): {arm: score}}"""
    by = {}
    for s in scores:
        key = (s["qid"], s["model"], s["effort"], s["repeat"])
        by.setdefault(key, {})[s["arm"]] = s
    return {k: v for k, v in by.items() if "vanilla" in v and "praxis" in v}


def md_table(rows, header):
    out = ["| " + " | ".join(header) + " |",
           "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) for c in r) + " |")
    return "\n".join(out)


def main():
    scores = load_objective()
    verdicts = load_verdicts()
    if not scores:
        print(f"No scores in {SCORES_DIR}. Run score.py first.")
        return

    paired = pair_objective(scores)
    lines = ["# Praxis eval scorecard\n",
             f"Pairings (question x model x effort x repeat with both arms): **{len(paired)}**\n"]

    # ---- Objective metrics ----
    lines.append("## Objective metrics (paired praxis - vanilla)\n")
    rows = []
    for m in OBJ_METRICS:
        van, prax, diffs = [], [], []
        for v in paired.values():
            a = as_num(v["vanilla"].get(m))
            b = as_num(v["praxis"].get(m))
            if a is None or b is None:
                continue
            van.append(a); prax.append(b); diffs.append(b - a)
        if not diffs:
            rows.append([m, "n/a", "n/a", "n/a", "n/a", "no data"])
            continue
        lo, hi = boot_ci(diffs)
        rows.append([
            m, f"{sum(van)/len(van):.2f}", f"{sum(prax)/len(prax):.2f}",
            f"{sum(diffs)/len(diffs):+.2f}",
            f"[{lo:+.2f}, {hi:+.2f}]" if lo is not None else "n/a",
            verdict(lo, hi, higher_better=(m not in REVERSE_CODED)),
        ])
    lines.append(md_table(rows, ["metric", "vanilla", "praxis", "Δ (paired)", "95% CI", "verdict"]))
    lines.append("\n*Note: for `fabrication_risk`, lower is better — a negative Δ favors praxis.*\n")

    # ---- Breakdown by trap type (where the plugin should shine) ----
    lines.append("## Trap handling by type\n")
    rows = []
    traps = sorted({v["vanilla"].get("trap_type") for v in paired.values()
                    if v["vanilla"].get("trap_type")})
    for t in traps:
        diffs = []
        for v in paired.values():
            if v["vanilla"].get("trap_type") != t:
                continue
            a = as_num(v["vanilla"].get("trap_handled"))
            b = as_num(v["praxis"].get("trap_handled"))
            if a is None or b is None:
                continue
            diffs.append(b - a)
        if diffs:
            lo, hi = boot_ci(diffs)
            rows.append([t, len(diffs), f"{sum(diffs)/len(diffs):+.2f}",
                         f"[{lo:+.2f}, {hi:+.2f}]" if lo is not None else "n/a",
                         verdict(lo, hi)])
    if rows:
        lines.append(md_table(rows, ["trap type", "n", "Δ handled", "95% CI", "verdict"]))
    else:
        lines.append("_No trap pairings yet._")

    # ---- Judge verdicts ----
    if verdicts:
        good = [v for v in verdicts if "error" not in v and "winner" in v]
        lines.append("\n## Blind judge\n")
        wins = {"praxis": 0, "vanilla": 0, "tie": 0}
        for v in good:
            wins[v["winner"]] += 1
        lines.append(f"Verdicts: **praxis {wins['praxis']}** / vanilla {wins['vanilla']} "
                     f"/ tie {wins['tie']}  (n={len(good)})\n")
        rows = []
        for dim in JUDGE_DIMS:
            diffs = [v["praxis"][dim] - v["vanilla"][dim] for v in good
                     if dim in v.get("praxis", {}) and dim in v.get("vanilla", {})]
            if diffs:
                lo, hi = boot_ci(diffs)
                rows.append([dim, f"{sum(diffs)/len(diffs):+.2f}",
                             f"[{lo:+.2f}, {hi:+.2f}]" if lo is not None else "n/a",
                             verdict(lo, hi)])
        if rows:
            lines.append(md_table(rows, ["judge dimension", "Δ (paired)", "95% CI", "verdict"]))
    else:
        lines.append("\n## Blind judge\n_No judge verdicts yet (run judge.py)._")

    out_md = RESULTS_DIR / "scorecard.md"
    out_md.write_text("\n".join(lines) + "\n")

    # ---- Flat CSV of pairings ----
    csv_path = RESULTS_DIR / "pairings.csv"
    with open(csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["qid", "model", "effort", "repeat"] +
                   [f"van_{m}" for m in OBJ_METRICS] + [f"prax_{m}" for m in OBJ_METRICS])
        for (qid, model, effort, rep), v in sorted(paired.items()):
            w.writerow([qid, model, effort, rep] +
                       [v["vanilla"].get(m) for m in OBJ_METRICS] +
                       [v["praxis"].get(m) for m in OBJ_METRICS])

    print(f"Wrote {out_md} and {csv_path}")
    print("\n" + out_md.read_text())


if __name__ == "__main__":
    main()
