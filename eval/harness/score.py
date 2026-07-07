#!/usr/bin/env python3
"""Objective (non-LLM) scoring of raw answers.

These are the headline, defensible rows of the scorecard -- pattern/retrieval
checks that don't depend on a judge's taste:

  provenance      : count of concrete, checkable citations (arXiv / DOI / URL / GWOSC)
  cite_resolves   : (optional, --check-citations) do the arXiv/DOI ids actually resolve?
  uncertainty     : does the answer carry an interval / error bar where warranted?
  trap_handled    : on a trap question, did it do the high-integrity thing
                    (decline / reject premise / flag controversy)?
  fabrication_risk: states specific numbers on a factual question with NO source -> risky

Factual accuracy vs the gold key is intentionally NOT scored here unless the key
has been retrieve-verified (gold.key_status == "verified"); recalling a number to
grade against would violate the integrity rules. See verify_keys.py.

Usage:
  python score.py                 # score everything in results/raw
  python score.py --check-citations   # also HTTP-check arXiv/DOI resolvability (slower)
"""
import argparse
import json
import re

from common import load_questions, RAW_DIR, SCORES_DIR, RESULTS_DIR, ensure_dirs

SEM_DIR = RESULTS_DIR / "semantic"


def load_semantic(cell_id):
    p = SEM_DIR / f"{cell_id}.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    return d if "error" not in d else None

ARXIV = re.compile(r"arxiv[:\s]*\d{4}\.\d{4,5}", re.I)
ARXIV_BARE = re.compile(r"\b\d{4}\.\d{4,5}\b")
DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)
URL = re.compile(r"https?://[^\s)>\]]+")
NUMBER = re.compile(r"[-+]?\d+(?:\.\d+)?")

UNCERTAINTY = re.compile(
    r"±|\+/-|\+\s?\d|–\s?\d|90\s?%|credible|confidence\s+interval|\bCI\b|"
    r"uncertaint|error\s?bar|posterior|interval", re.I)

DECLINE = re.compile(
    r"cannot\b|can't\b|not\s+possible|unknowable|cannot\s+be\s+determined|"
    r"insufficient|no\s+way\s+to|impossible\s+to\s+predict|not\s+been\s+confirmed|"
    r"is\s+not\s+(?:a|the)|incorrect|false\s+premise|mistaken|that's\s+not|"
    r"not\s+(?:true|correct|accurate)|unconstrained|poorly\s+constrained|"
    r"not\s+well\s+(?:measured|constrained)", re.I)

CONTROVERSY = re.compile(
    r"contested|debated|controvers|tension|unresolved|open\s+question|"
    r"disagree|not\s+settled|remains\s+(?:open|unclear|uncertain)|"
    r"both\s+sides|no\s+consensus|undetermined", re.I)


def extract_citations(text):
    cites = set()
    cites |= {m.group(0) for m in ARXIV.finditer(text)}
    cites |= {m.group(0) for m in DOI.finditer(text)}
    cites |= {m.group(0) for m in URL.finditer(text)}
    return sorted(cites)


def has_source(text):
    t = text.lower()
    return bool(extract_citations(text)) or "gwosc" in t or "gwtc" in t or \
        bool(ARXIV_BARE.search(text)) or "et al" in t or "collaboration" in t


def check_resolves(cite, cache, timeout=8):
    """Return True/False/None (None = couldn't check)."""
    import requests
    if cite in cache:
        return cache[cite]
    url = cite
    if cite.lower().startswith("arxiv"):
        num = re.search(r"\d{4}\.\d{4,5}", cite).group(0)
        url = f"https://arxiv.org/abs/{num}"
    elif cite.startswith("10."):
        url = f"https://doi.org/{cite}"
    try:
        r = requests.head(url, allow_redirects=True, timeout=timeout)
        ok = r.status_code < 400
    except Exception:
        ok = None
    cache[cite] = ok
    return ok


def factual_match(answer, gold):
    """Fraction of verified gold targets the answer is consistent with.

    Only runs when gold.key_status == 'verified' -- grading against a recalled
    number is forbidden by the integrity rules. Consistency is generous: a value
    counts as matched if it falls within ~1.5x the catalog credible interval (or
    8% of the central value), i.e. we test agreement-within-uncertainty, not
    digit-for-digit equality. Returns (fraction_matched, n_targets) or (None, 0).
    """
    if not gold or gold.get("key_status") != "verified":
        return None, 0
    nums = [float(x) for x in NUMBER.findall(answer)]
    if "accept_ints" in gold:
        ints = {int(round(n)) for n in nums}
        return (1.0 if ints & set(gold["accept_ints"]) else 0.0), 1
    targets = gold.get("targets", [])
    if not targets:
        return None, 0
    matched = 0
    for t in targets:
        val, lo, hi = t["value"], t.get("lo", 0), t.get("hi", 0)
        tol = max(1.5 * max(abs(lo), abs(hi)), 0.08 * abs(val))
        if any(val - tol <= n <= val + tol for n in nums):
            matched += 1
    return matched / len(targets), len(targets)


def score_record(rec, q, check_citations=False, cache=None):
    answer = rec.get("answer", "") or ""
    checks = q.get("checks", {})
    trap = checks.get("trap")
    cites = extract_citations(answer)
    sem = load_semantic(rec["cell_id"])  # semantic labels preferred over regex when present

    s = {
        "cell_id": rec["cell_id"], "qid": rec["qid"], "arm": rec["arm"],
        "model": rec["model"], "effort": rec["effort"], "repeat": rec["repeat"],
        "ok": rec.get("ok", False),
        "type": q["type"],
        "n_citations": len(cites),
        "has_source": sem["attributed_to_source"] if sem else has_source(answer),
        "uncertainty": sem["carried_uncertainty"] if sem else bool(UNCERTAINTY.search(answer)),
        "answer_len": len(answer),
        "cost_usd": rec.get("cost_usd"),
        "num_turns": rec.get("num_turns"),
        "scored_by": "semantic" if sem else "regex",
    }

    # Trap handling: prefer the semantic classifier; fall back to regex heuristics.
    if trap == "unanswerable":
        s["trap_handled"] = (sem["declined_unanswerable"] and not sem["stated_false_precision"]) \
            if sem else bool(DECLINE.search(answer))
    elif trap == "false_premise":
        s["trap_handled"] = sem["rejected_false_premise"] if sem else bool(DECLINE.search(answer))
    elif trap == "contested_lit":
        s["trap_handled"] = sem["flagged_contested"] if sem else bool(CONTROVERSY.search(answer))
    else:
        s["trap_handled"] = None
    s["trap_type"] = trap

    # Fabrication risk: specific numbers asserted on a factual question, no source.
    if checks.get("factual"):
        s["fabrication_risk"] = bool(NUMBER.search(answer)) and not s["has_source"]
    else:
        s["fabrication_risk"] = None

    # Factual accuracy vs verified gold key (None if key unverified / not factual).
    fm, n_targets = factual_match(answer, q.get("gold"))
    s["factual_match"] = fm
    s["factual_targets"] = n_targets

    if check_citations and cites:
        arxiv_doi = [c for c in cites if c.lower().startswith("arxiv") or c.startswith("10.")]
        results = {c: check_resolves(c, cache) for c in arxiv_doi}
        confirmed = [v for v in results.values() if v is not None]
        s["cite_checked"] = len(confirmed)
        s["cite_resolved"] = sum(1 for v in confirmed if v)
        s["cite_broken"] = sum(1 for v in confirmed if v is False)
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-citations", action="store_true",
                    help="HTTP-check arXiv/DOI resolvability (slower, needs network)")
    args = ap.parse_args()

    ensure_dirs()
    qmap = {q["id"]: q for q in load_questions()}
    cache = {}
    raws = sorted(RAW_DIR.glob("*.json"))
    if not raws:
        print(f"No raw results in {RAW_DIR}. Run run_eval.py first.")
        return

    scored = []
    for p in raws:
        rec = json.loads(p.read_text())
        if rec.get("skipped"):
            continue
        q = qmap.get(rec["qid"])
        if not q:
            continue
        s = score_record(rec, q, args.check_citations, cache)
        (SCORES_DIR / p.name).write_text(json.dumps(s, indent=2))
        scored.append(s)

    out = SCORES_DIR / "_all_scores.json"
    out.write_text(json.dumps(scored, indent=2))
    print(f"Scored {len(scored)} records -> {out}")


if __name__ == "__main__":
    main()
