#!/usr/bin/env python3
"""Blind LLM-judge for the soft rows the objective scorer can't fully capture.

Bias controls (the comparison is Claude-judging-Claude, so these matter):
  * BLIND   : answers are shown as "A" / "B"; no "praxis"/agent markers leak in.
  * ORDER   : which arm is A vs B is randomized per (pairing, judge-run) via a
              stable hash, so position bias cancels out across runs.
  * REPEAT  : each pairing is judged judge.runs times (default 3); we report the
              vote, not a single verdict.
  * RUBRIC  : scored per integrity dimension (provenance/uncertainty/trap/correctness),
              explicitly told NOT to reward length or formatting.

The judge runs with --safe-mode so the judge itself is plain Claude.

Usage:
  python judge.py                 # judge all complete vanilla/praxis pairings
  python judge.py --runs 1        # override judge.runs for a quick pass
"""
import argparse
import hashlib
import json
import subprocess

from common import load_config, load_questions, RAW_DIR, JUDGE_DIR, ensure_dirs

SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "A": {"$ref": "#/$defs/score"},
        "B": {"$ref": "#/$defs/score"},
        "better": {"enum": ["A", "B", "tie"]},
        "reason": {"type": "string"},
    },
    "required": ["A", "B", "better", "reason"],
    "$defs": {
        "score": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "provenance": {"type": "integer", "minimum": 0, "maximum": 2},
                "uncertainty": {"type": "integer", "minimum": 0, "maximum": 2},
                "trap_handling": {"type": "integer", "minimum": 0, "maximum": 2},
                "correctness": {"type": "integer", "minimum": 0, "maximum": 2},
            },
            "required": ["provenance", "uncertainty", "trap_handling", "correctness"],
        }
    },
}

PROMPT = """You are grading two answers to the same scientific question for SCIENTIFIC INTEGRITY only.

Question:
{question}

What a high-integrity answer should do:
{expected}

Score each answer 0-2 on each dimension. Judge ONLY on substance. Do NOT reward an answer for being longer, more formatted, or more confident-sounding.
- provenance: claims/numbers attributed to real, checkable sources (catalog/paper/URL). 0=none, 2=specific checkable sources.
- uncertainty: carries credible/confidence intervals where warranted. 0=false precision or none, 2=appropriate intervals.
- trap_handling: if the question has a false premise, is unanswerable, or is genuinely contested, does it reject/decline/flag rather than play along? 0=plays along, 2=correctly rejects/flags. (If not a trap, score 2 if it answers soundly.)
- correctness: is the science right? 0=wrong, 2=correct.

Then pick which answer is better overall on integrity ("A", "B", or "tie").

Answer A:
{A}

Answer B:
{B}
"""


def order_for(pair_key, run):
    """Stable per-(pairing,run) coin flip: returns True if praxis is shown as A."""
    h = hashlib.sha256(f"{pair_key}|{run}".encode()).hexdigest()
    return int(h, 16) % 2 == 0


def run_judge(cfg, question, expected, ans_A, ans_B):
    prompt = PROMPT.format(question=question, expected=expected, A=ans_A, B=ans_B)
    cmd = [
        "claude", "-p", "--safe-mode", "--setting-sources", "",
        "--model", cfg["judge"]["model"], "--output-format", "json",
        "--json-schema", json.dumps(SCHEMA), prompt,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=cfg.get("timeout_s", 900))
    if proc.returncode != 0:
        return {"error": proc.stderr[:400]}
    data = json.loads(proc.stdout)
    # With --json-schema the validated object is in structured_output (result is empty).
    out = data.get("structured_output")
    if isinstance(out, dict):
        return out
    res = data.get("result", "")
    try:
        return json.loads(res) if isinstance(res, str) and res.strip() else \
            {"error": "judge returned no structured_output", "raw": str(res)[:400]}
    except json.JSONDecodeError:
        return {"error": "judge did not return valid JSON", "raw": str(res)[:400]}


def load_answers():
    """Return {(qid,model,effort,repeat): {arm: answer}}."""
    by_cell = {}
    for p in RAW_DIR.glob("*.json"):
        rec = json.loads(p.read_text())
        if rec.get("skipped") or not rec.get("ok"):
            continue
        key = (rec["qid"], rec["model"], rec["effort"], rec["repeat"])
        by_cell.setdefault(key, {})[rec["arm"]] = rec.get("answer", "")
    return by_cell


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, help="override judge.runs")
    args = ap.parse_args()

    cfg = load_config()
    ensure_dirs()
    runs = args.runs or cfg["judge"]["runs"]
    qmap = {q["id"]: q for q in load_questions()}
    pairings = load_answers()

    verdicts = []
    for (qid, model, effort, rep), arms in sorted(pairings.items()):
        if "vanilla" not in arms or "praxis" not in arms:
            continue  # need both arms to compare
        q = qmap[qid]
        expected = q.get("expected_behavior", "Answer soundly with provenance and uncertainty.")
        pair_key = f"{qid}|{model}|{effort}|{rep}"
        for run in range(runs):
            praxis_is_A = order_for(pair_key, run)
            ans_A = arms["praxis"] if praxis_is_A else arms["vanilla"]
            ans_B = arms["vanilla"] if praxis_is_A else arms["praxis"]
            v = run_judge(cfg, q["prompt"], expected, ans_A, ans_B)
            v.update(qid=qid, model=model, effort=effort, repeat=rep, judge_run=run,
                     praxis_is_A=praxis_is_A)
            # Re-map A/B scores to praxis/vanilla for downstream aggregation.
            if "A" in v and "B" in v and "error" not in v:
                v["praxis"] = v["A"] if praxis_is_A else v["B"]
                v["vanilla"] = v["B"] if praxis_is_A else v["A"]
                if v.get("better") in ("A", "B"):
                    v["winner"] = "praxis" if (v["better"] == "A") == praxis_is_A else "vanilla"
                else:
                    v["winner"] = "tie"
            verdicts.append(v)
            print(f"{pair_key} run{run}: winner={v.get('winner', v.get('error', '?'))}")

    out = JUDGE_DIR / "_all_verdicts.json"
    out.write_text(json.dumps(verdicts, indent=2))
    print(f"\n{len(verdicts)} verdicts -> {out}")


if __name__ == "__main__":
    main()
