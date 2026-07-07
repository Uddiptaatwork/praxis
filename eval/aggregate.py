#!/usr/bin/env python3
"""
aggregate.py — small averaged A/B evaluation for the Praxis GW science harness.

Runs a 3 prompts x 3 reps x 2 harnesses = 18-run matrix of fast single-event
GWOSC lookups, scores each run with cheap objective (regex/diff) metrics against
the LIVE GWOSC catalog values, and aggregates mean +/- std per prompt x harness
and overall per harness. Produces aggregate.json + aggregate.md and saves every
raw answer under eval/runs/.

Design constraints:
  * Python standard library only (urllib + json). No pip dependencies.
  * NO LLM-judge. All scoring is regex / numeric-diff against the live API.
  * No fabricated numbers: ground truth is fetched live; if a run refuses or is
    unparseable we record that honestly rather than inventing a value.
  * macOS has no `timeout`; runs are allowed to finish. These hit the live API.

Harnesses (both invoked from a NEUTRAL cwd so the baseline does not inherit the
project CLAUDE.md):
  A (baseline) : claude -p "<prompt>" --output-format json
  B (Praxis)   : claude --plugin-dir <praxis> --dangerously-skip-permissions
                 -p "<prompt>" --output-format json   (cwd /tmp)

Usage:
    python3 eval/aggregate.py            # run the full matrix, then aggregate
    python3 eval/aggregate.py --aggregate-only   # re-aggregate existing runs/
    python3 eval/aggregate.py --reps 3 --neutral-dir /tmp
"""

from __future__ import annotations

import argparse
import json
import math
import re
import ssl
import statistics
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PRAXIS_DIR = "/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis"
HERE = Path(__file__).resolve().parent
RUNS_DIR = HERE / "runs"

# Prompt id -> (prompt text, event name, catalog)
PROMPTS: dict[str, dict[str, str]] = {
    "P1": {
        "event": "GW150914",
        "catalog": "GWTC-2.1-confident",
        "prompt": (
            "What were the two source-frame component masses of GW150914, with "
            "90% credible intervals? Cite the GWOSC source."
        ),
    },
    "P2": {
        "event": "GW190521",
        "catalog": "GWTC-2.1-confident",
        "prompt": (
            "Give the source-frame component masses of GW190521 with 90% "
            "credible intervals, and cite the GWOSC source."
        ),
    },
    "P3": {
        "event": "GW230529",
        "catalog": "GWTC-4.1",
        "prompt": (
            "What are the component masses of GW230529, with 90% credible "
            "intervals? Cite the GWOSC source."
        ),
    },
}

HARNESSES = ("A", "B")  # A = baseline, B = Praxis


# ---------------------------------------------------------------------------
# Objective-metric regexes
# ---------------------------------------------------------------------------

# GWOSC DOIs use the prefix 10.7935 -- e.g. 10.7935/qf3a-3z67
RE_GWOSC_DOI = re.compile(r"10\.7935/[a-z0-9-]+", re.IGNORECASE)

# Asymmetric error notation: +4.4 / -2.6   +33.6/-21.7   +0.8 / -1.2 (unicode minus ok)
RE_ASYM_ERR = re.compile(r"\+\s*\d+(?:\.\d+)?\s*/\s*[-−]\s*\d+(?:\.\d+)?")

# A number that may carry an asymmetric uncertainty, optionally with M_sun-ish unit.
# We capture the central value; the +/- tail is consumed but not required.
_NUM = r"\d+(?:\.\d+)?"
RE_MASS_WITH_ERR = re.compile(
    r"(" + _NUM + r")"                                  # central value (group 1)
    r"(?:\s*(?:M_?(?:sun|☉|o|\\odot)|M☉|solar))?"  # optional unit
    r"\s*"
    r"(?:"                                              # optional uncertainty tail
        r"(?:\(?\s*\+\s*" + _NUM + r"\s*/\s*[-−]\s*" + _NUM + r"\s*\)?)"  # +x/-y
        r"|(?:\^\{?\+\s*" + _NUM + r"\}?_\{?[-−]\s*" + _NUM + r"\}?)"     # ^{+x}_{-y}
        r"|(?:\s*±\s*" + _NUM + r")"                                       # +/- z
    r")?",
)


# ---------------------------------------------------------------------------
# GWOSC API client (stdlib only, retry + graceful failure)
# ---------------------------------------------------------------------------

GWOSC_BASE = "https://gwosc.org/api/v2"
USER_AGENT = "praxis-aggregate-eval/1.0 (stdlib urllib)"


class GwoscClient:
    def __init__(self, timeout: float = 30.0, retries: int = 5):
        self.timeout = timeout
        self.retries = retries
        self._ctx = ssl.create_default_context()
        self.network_ok: Optional[bool] = None
        # catalog -> {event_name: {m1: {...}, m2: {...}}}
        self._catalog_cache: dict[str, dict[str, dict]] = {}

    def _get(self, url: str) -> Optional[dict]:
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    self.network_ok = True
                    return data
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    self.network_ok = True
                    return None
                # 500/502/503/504 are the transient GWOSC proxy errors -> retry.
                if e.code in (500, 502, 503, 504) and attempt < self.retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as e:
                if attempt < self.retries - 1:
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
            except (ValueError, json.JSONDecodeError):
                break
        self.network_ok = False
        return None

    def _scan_catalog(self, catalog: str) -> dict[str, dict]:
        """Page the catalog events endpoint, returning {event_name: {m1,m2}} with
        each value as {best, upper_error, lower_error}. Cached per catalog."""
        if catalog in self._catalog_cache:
            return self._catalog_cache[catalog]
        out: dict[str, dict] = {}
        url = (
            f"{GWOSC_BASE}/catalogs/{catalog}/events"
            "?include-default-parameters=true&page-size=20"
        )
        while url:
            data = self._get(url)
            if data is None:
                if self.network_ok is False:
                    # network failure mid-scan -- do not cache a partial result
                    return out
                break
            for row in data.get("results", []):
                name = row.get("name", "")
                params = {p["name"]: p for p in row.get("default_parameters", [])}
                m1 = params.get("mass_1_source")
                m2 = params.get("mass_2_source")
                rec: dict[str, Any] = {}
                if m1:
                    rec["m1"] = {
                        "best": m1.get("best"),
                        "upper_error": m1.get("upper_error"),
                        "lower_error": m1.get("lower_error"),
                    }
                if m2:
                    rec["m2"] = {
                        "best": m2.get("best"),
                        "upper_error": m2.get("upper_error"),
                        "lower_error": m2.get("lower_error"),
                    }
                out[name] = rec
            url = data.get("next")
        self._catalog_cache[catalog] = out
        return out

    def ground_truth(self, event: str, catalog: str) -> Optional[dict]:
        """Resolve component masses for `event` in `catalog`.

        Catalogs sometimes hold both a short name (GW190521) and a long one
        (GW190521_074359) -- these are DIFFERENT events. We therefore prefer an
        exact name match, and only fall back to a unique prefix match.
        """
        events = self._scan_catalog(catalog)
        if not events:
            return None
        # 1. exact match
        if event in events and events[event]:
            return {"event_resolved": event, **events[event]}
        # 2. unique prefix match (event name + "_<gps>")
        prefix_hits = [
            n for n in events
            if n == event or n.startswith(event + "_")
        ]
        # Prefer the bare-name event if present among hits (handled above); else
        # only accept a prefix hit if it is unique.
        if len(prefix_hits) == 1 and events[prefix_hits[0]]:
            n = prefix_hits[0]
            return {"event_resolved": n, **events[n]}
        return None


# ---------------------------------------------------------------------------
# Running one claude invocation
# ---------------------------------------------------------------------------

def build_cmd(harness: str, prompt: str) -> list[str]:
    if harness == "A":
        return ["claude", "-p", prompt, "--output-format", "json"]
    elif harness == "B":
        return [
            "claude",
            "--plugin-dir", PRAXIS_DIR,
            "--dangerously-skip-permissions",
            "-p", prompt,
            "--output-format", "json",
        ]
    raise ValueError(f"unknown harness {harness!r}")


def run_one(harness: str, prompt: str, neutral_dir: str) -> dict:
    """Invoke claude once from a neutral cwd, capture the JSON envelope.

    Returns a dict with the extracted fields plus a `status`:
      ok            -- parsed a JSON envelope with a non-empty result
      empty_result  -- envelope parsed but result was empty
      no_json       -- could not parse JSON from stdout
      cli_error     -- the CLI exited non-zero with no usable JSON
    """
    cmd = build_cmd(harness, prompt)
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=neutral_dir,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as e:
        return {
            "status": "cli_error",
            "error": f"claude CLI not found: {e}",
            "wall_s": time.time() - t0,
            "result": "",
        }
    wall = time.time() - t0
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""

    env: Optional[dict] = None
    # The envelope is the JSON object on stdout. Try whole-stdout first, then
    # fall back to the last balanced {...} block (in case of stray prefixes).
    try:
        env = json.loads(stdout.strip())
    except (ValueError, json.JSONDecodeError):
        m = re.search(r"\{.*\}", stdout, re.DOTALL)
        if m:
            try:
                env = json.loads(m.group(0))
            except (ValueError, json.JSONDecodeError):
                env = None

    if env is None:
        return {
            "status": "no_json",
            "error": (stderr or "no JSON on stdout")[:500],
            "returncode": proc.returncode,
            "wall_s": wall,
            "result": "",
            "raw_stdout_head": stdout[:500],
        }

    result_text = env.get("result", "") or ""
    usage = env.get("usage", {}) or {}
    rec = {
        "status": "ok" if result_text.strip() else "empty_result",
        "result": result_text,
        "output_tokens": usage.get("output_tokens"),
        "duration_ms": env.get("duration_ms"),
        "total_cost_usd": env.get("total_cost_usd"),
        "is_error": env.get("is_error"),
        "subtype": env.get("subtype"),
        "num_turns": env.get("num_turns"),
        "session_id": env.get("session_id"),
        "returncode": proc.returncode,
        "wall_s": wall,
    }
    return rec


# ---------------------------------------------------------------------------
# Mass extraction from answer text
# ---------------------------------------------------------------------------

# Heuristic upper bound for a plausible source-frame component mass (M_sun).
# Filters out years (2016), credible-interval "90", catalog numbers, etc.
MASS_MIN = 0.5
MASS_MAX = 250.0


def _candidate_masses(text: str) -> list[float]:
    """Pull plausible component-mass values out of the answer text, in order.

    Strategy: find every number that is immediately followed by an asymmetric /
    +- uncertainty OR an M_sun-style unit -- those are almost always the masses
    -- and keep them in plausible-mass range. This avoids grabbing "90%", years,
    DOIs, or the "1"/"2" subscripts of m1/m2.
    """
    vals: list[float] = []
    spans: list[tuple[int, int]] = []
    for m in RE_MASS_WITH_ERR.finditer(text):
        whole = m.group(0)
        # Require that the match actually carried a unit or an uncertainty tail;
        # a bare number alone is too ambiguous.
        has_unit = bool(re.search(r"M_?(?:sun|☉|o|\\odot)|solar", whole, re.IGNORECASE))
        has_err = bool(re.search(r"[+±−^]", whole)) and whole != m.group(1)
        if not (has_unit or has_err):
            continue
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if MASS_MIN <= v <= MASS_MAX:
            vals.append(v)
            spans.append(m.span(1))

    # Fallback for prose like "36 and 29 solar masses" or "34.6 and 30.0 M_sun",
    # where two numbers share a single trailing unit (so only the second number is
    # adjacent to the unit and the first is otherwise missed). Insert the leading
    # number ahead of the unit-bearing one, preserving textual order.
    pair_re = re.compile(
        r"(" + _NUM + r")\s*(?:and|&|/|,|to)\s*(" + _NUM + r")\s*"
        r"(?:M_?(?:sun|☉|o|\\odot)|M☉|solar)",
        re.IGNORECASE,
    )
    for pm in pair_re.finditer(text):
        try:
            a = float(pm.group(1)); b = float(pm.group(2))
        except ValueError:
            continue
        if not (MASS_MIN <= a <= MASS_MAX and MASS_MIN <= b <= MASS_MAX):
            continue
        # Only add `a` if we don't already have a value at its span.
        a_span = pm.span(1)
        if not any(s[0] <= a_span[0] < s[1] for s in spans):
            vals.append(a)
            spans.append(a_span)
        b_span = pm.span(2)
        if not any(s[0] <= b_span[0] < s[1] for s in spans):
            vals.append(b)
            spans.append(b_span)

    # Return values in textual order so m1/m2 fallback ordering is stable.
    order = sorted(range(len(vals)), key=lambda i: spans[i][0])
    return [vals[i] for i in order]


def extract_m1_m2(text: str, gt: Optional[dict]) -> tuple[Optional[float], Optional[float]]:
    """Best-effort extraction of (m1, m2) component masses from answer text.

    Returns (m1, m2) as floats, or None for any that cannot be parsed. By
    convention m1 >= m2 (primary >= secondary), which is how GWOSC reports them.
    """
    # Prefer values explicitly attached to m1 / m_1 / primary, and m2 / secondary.
    def near(label_re: str) -> Optional[float]:
        for lm in re.finditer(label_re, text, re.IGNORECASE):
            window = text[lm.end(): lm.end() + 60]
            cands = _candidate_masses(window)
            if cands:
                return cands[0]
        return None

    m1 = near(r"(?:m_?1|primary|larger|heavier|more\s+massive)\b")
    m2 = near(r"(?:m_?2|secondary|smaller|lighter|less\s+massive)\b")

    # Fallback: take the first two plausible masses in the whole answer.
    if m1 is None or m2 is None:
        cands = _candidate_masses(text)
        if m1 is None and len(cands) >= 1:
            m1 = cands[0]
        if m2 is None and len(cands) >= 2:
            # pick the first candidate distinct from m1
            for c in cands[1:]:
                if m1 is None or abs(c - m1) > 1e-9:
                    m2 = c
                    break

    # Normalise ordering to m1 >= m2.
    if m1 is not None and m2 is not None and m2 > m1:
        m1, m2 = m2, m1
    return m1, m2


# ---------------------------------------------------------------------------
# Scoring one run
# ---------------------------------------------------------------------------

def score_run(answer: str, gt: Optional[dict]) -> dict:
    """Objective metrics for one answer text against live ground truth `gt`."""
    has_doi = bool(RE_GWOSC_DOI.search(answer))
    has_asym = bool(RE_ASYM_ERR.search(answer))
    m1, m2 = extract_m1_m2(answer, gt)

    m1_match: Optional[bool] = None
    m2_match: Optional[bool] = None
    if gt and gt.get("m1") and gt["m1"].get("best") is not None and m1 is not None:
        gm1 = gt["m1"]["best"]
        tol1 = max(1.5, abs(gt["m1"].get("upper_error") or 0.0))
        m1_match = abs(m1 - gm1) <= tol1
    if gt and gt.get("m2") and gt["m2"].get("best") is not None and m2 is not None:
        gm2 = gt["m2"]["best"]
        tol2 = max(1.5, abs(gt["m2"].get("upper_error") or 0.0))
        m2_match = abs(m2 - gm2) <= tol2

    return {
        "has_gwosc_doi": has_doi,
        "has_asym_err": has_asym,
        "stated_m1": m1,
        "stated_m2": m2,
        "m1_current_match": m1_match,
        "m2_current_match": m2_match,
        "gwosc_dois": sorted(set(RE_GWOSC_DOI.findall(answer))),
    }


# ---------------------------------------------------------------------------
# Aggregation helpers
# ---------------------------------------------------------------------------

def _mean_std(xs: list[float]) -> dict:
    xs = [x for x in xs if x is not None and not (isinstance(x, float) and math.isnan(x))]
    if not xs:
        return {"mean": None, "std": None, "n": 0}
    mean = statistics.fmean(xs)
    std = statistics.pstdev(xs) if len(xs) > 1 else 0.0
    return {"mean": mean, "std": std, "n": len(xs)}


def _rate(bools: list[Optional[bool]]) -> dict:
    """Mean of boolean flags over the runs where the flag is defined (not None)."""
    defined = [1.0 if b else 0.0 for b in bools if b is not None]
    n_total = len(bools)
    n_defined = len(defined)
    rate = statistics.fmean(defined) if defined else None
    return {"rate": rate, "n_true": int(sum(defined)), "n_defined": n_defined, "n_total": n_total}


def aggregate_cell(runs: list[dict]) -> dict:
    """Aggregate the list of scored runs for one prompt x harness cell."""
    parseable = [r for r in runs if r["scored"].get("stated_m1") is not None]
    statuses = [r["run"]["status"] for r in runs]
    return {
        "n_runs": len(runs),
        "statuses": statuses,
        "n_ok": sum(1 for s in statuses if s == "ok"),
        "n_refused_or_unparseable": sum(1 for s in statuses if s != "ok"),
        "provenance_rate": _rate([r["scored"]["has_gwosc_doi"] for r in runs]),
        "asymmetric_uncertainty_rate": _rate([r["scored"]["has_asym_err"] for r in runs]),
        "current_catalog_match_rate": _rate([r["scored"]["m1_current_match"] for r in runs]),
        "m1": _mean_std([r["scored"]["stated_m1"] for r in runs]),
        "m2": _mean_std([r["scored"]["stated_m2"] for r in runs]),
        "cost_usd": _mean_std([r["run"].get("total_cost_usd") for r in runs]),
        "output_tokens": _mean_std([r["run"].get("output_tokens") for r in runs]),
        "duration_s": _mean_std(
            [(r["run"].get("duration_ms") / 1000.0) if r["run"].get("duration_ms") is not None else None
             for r in runs]
        ),
        "n_parseable_masses": len(parseable),
    }


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def _ms(d: dict, prec: int = 2, pct: bool = False) -> str:
    if d.get("mean") is None:
        return "n/a"
    m = d["mean"]; s = d.get("std") or 0.0
    if pct:
        return f"{m*100:.0f}% ± {s*100:.0f}%"
    return f"{m:.{prec}f} ± {s:.{prec}f}"


def _rate_str(d: dict) -> str:
    if d.get("rate") is None:
        return f"n/a (0/{d['n_total']})"
    return f"{d['rate']*100:.0f}% ({d['n_true']}/{d['n_defined']})"


def render_md(report: dict) -> str:
    L: list[str] = []
    L.append("# Praxis A/B evaluation — aggregated results")
    L.append("")
    L.append(f"_Generated: {report['generated_utc']}_  ")
    L.append(f"_GWOSC network status: **{report['network_status']}**_  ")
    L.append(f"_Matrix: {report['matrix']['n_prompts']} prompts x "
             f"{report['matrix']['n_reps']} reps x "
             f"{report['matrix']['n_harnesses']} harnesses = "
             f"{report['matrix']['n_runs']} runs_  ")
    L.append("")
    L.append("Harnesses: **A = baseline** (`claude -p`), "
             "**B = Praxis** (`claude --plugin-dir`). Both run from a neutral cwd "
             "so the baseline does not inherit the project CLAUDE.md. All scoring "
             "is objective (regex + numeric diff vs the LIVE GWOSC catalog); no LLM-judge.")
    L.append("")

    # --- Ground truth -----------------------------------------------------
    L.append("## Live GWOSC ground truth")
    L.append("")
    L.append("| Prompt | Event | Catalog | m1_source | m2_source |")
    L.append("|---|---|---|---|---|")
    for pid, gt in report["ground_truth"].items():
        ev = PROMPTS[pid]["event"]; cat = PROMPTS[pid]["catalog"]
        if gt is None:
            L.append(f"| {pid} | {ev} | {cat} | _unresolved_ | _unresolved_ |")
            continue
        def fmt(x):
            if not x or x.get("best") is None:
                return "n/a"
            return f"{x['best']} +{x.get('upper_error')}/{x.get('lower_error')}"
        L.append(f"| {pid} | {gt.get('event_resolved', ev)} | {cat} | "
                 f"{fmt(gt.get('m1'))} | {fmt(gt.get('m2'))} |")
    L.append("")

    # --- Overall per harness ---------------------------------------------
    L.append("## Overall per harness (the headline)")
    L.append("")
    L.append("| Metric | A (baseline) | B (Praxis) |")
    L.append("|---|:--:|:--:|")
    oa = report["overall"]["A"]; ob = report["overall"]["B"]
    L.append(f"| Runs (ok / total) | {oa['n_ok']}/{oa['n_runs']} | {ob['n_ok']}/{ob['n_runs']} |")
    L.append(f"| provenance_rate (GWOSC DOI) | {_rate_str(oa['provenance_rate'])} | {_rate_str(ob['provenance_rate'])} |")
    L.append(f"| current_catalog_match_rate | {_rate_str(oa['current_catalog_match_rate'])} | {_rate_str(ob['current_catalog_match_rate'])} |")
    L.append(f"| asymmetric_uncertainty_rate | {_rate_str(oa['asymmetric_uncertainty_rate'])} | {_rate_str(ob['asymmetric_uncertainty_rate'])} |")
    L.append(f"| cost_usd (mean +/- std) | {_ms(oa['cost_usd'], 4)} | {_ms(ob['cost_usd'], 4)} |")
    L.append(f"| duration_s (mean +/- std) | {_ms(oa['duration_s'], 1)} | {_ms(ob['duration_s'], 1)} |")
    L.append(f"| output_tokens (mean +/- std) | {_ms(oa['output_tokens'], 0)} | {_ms(ob['output_tokens'], 0)} |")
    L.append("")

    # --- Per-prompt consistency story ------------------------------------
    L.append("## Per-prompt m1 consistency (mean +/- std across 3 reps)")
    L.append("")
    L.append("Lower std = more reliable / less drift across repetitions.")
    L.append("")
    L.append("| Prompt | Event | A m1 mean+/-std | B m1 mean+/-std | GWOSC m1 |")
    L.append("|---|---|:--:|:--:|:--:|")
    for pid in PROMPTS:
        ev = PROMPTS[pid]["event"]
        a = report["per_cell"][pid]["A"]["m1"]; b = report["per_cell"][pid]["B"]["m1"]
        gt = report["ground_truth"].get(pid)
        gtm1 = (gt or {}).get("m1") or {}
        gstr = f"{gtm1.get('best')}" if gtm1.get("best") is not None else "n/a"
        L.append(f"| {pid} | {ev} | {_ms(a)} | {_ms(b)} | {gstr} |")
    L.append("")

    # --- Full per prompt x harness table ---------------------------------
    L.append("## Full per-prompt x harness table")
    L.append("")
    L.append("| Prompt | Harness | prov_rate | match_rate | asym_rate | "
             "m1 mean+/-std | m2 mean+/-std | cost_usd | dur_s | out_tok | statuses |")
    L.append("|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|")
    for pid in PROMPTS:
        for h in HARNESSES:
            c = report["per_cell"][pid][h]
            L.append(
                f"| {pid} | {h} | {_rate_str(c['provenance_rate'])} | "
                f"{_rate_str(c['current_catalog_match_rate'])} | "
                f"{_rate_str(c['asymmetric_uncertainty_rate'])} | "
                f"{_ms(c['m1'])} | {_ms(c['m2'])} | {_ms(c['cost_usd'],4)} | "
                f"{_ms(c['duration_s'],1)} | {_ms(c['output_tokens'],0)} | "
                f"{','.join(c['statuses'])} |"
            )
    L.append("")

    # --- Per-run detail ---------------------------------------------------
    L.append("## Per-run detail")
    L.append("")
    L.append("| Run | status | DOI | asym | m1 | m2 | m1_match | cost_usd | dur_s | out_tok |")
    L.append("|---|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for r in report["runs"]:
        s = r["scored"]; rn = r["run"]
        dur = f"{rn['duration_ms']/1000:.1f}" if rn.get("duration_ms") is not None else "n/a"
        cost = f"{rn['total_cost_usd']:.4f}" if rn.get("total_cost_usd") is not None else "n/a"
        L.append(
            f"| {r['prompt']}_{r['harness']}_{r['rep']} | {rn['status']} | "
            f"{'Y' if s['has_gwosc_doi'] else '-'} | {'Y' if s['has_asym_err'] else '-'} | "
            f"{s['stated_m1'] if s['stated_m1'] is not None else 'null'} | "
            f"{s['stated_m2'] if s['stated_m2'] is not None else 'null'} | "
            f"{'Y' if s['m1_current_match'] else ('N' if s['m1_current_match'] is False else '?')} | "
            f"{cost} | {dur} | {rn.get('output_tokens')} |"
        )
    L.append("")

    # --- Failures ---------------------------------------------------------
    fails = [r for r in report["runs"] if r["run"]["status"] != "ok"]
    L.append("## Refused / failed runs")
    L.append("")
    if not fails:
        L.append("None — all runs returned a non-empty result.")
    else:
        for r in fails:
            L.append(f"- `{r['prompt']}_{r['harness']}_{r['rep']}` — status="
                     f"{r['run']['status']}; {r['run'].get('error','')[:160]}")
    L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_matrix(reps: int, neutral_dir: str) -> list[dict]:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    runs: list[dict] = []
    total = len(PROMPTS) * len(HARNESSES) * reps
    i = 0
    for pid, meta in PROMPTS.items():
        for h in HARNESSES:
            for rep in range(1, reps + 1):
                i += 1
                tag = f"{pid}_{h}_{rep}"
                print(f"[{i}/{total}] running {tag} ...", file=sys.stderr, flush=True)
                rec = run_one(h, meta["prompt"], neutral_dir)
                # Save the raw answer text.
                (RUNS_DIR / f"{tag}.txt").write_text(rec.get("result", ""), encoding="utf-8")
                # Save the full run record (minus the bulky raw text) as JSON too.
                meta_rec = {k: v for k, v in rec.items() if k != "result"}
                (RUNS_DIR / f"{tag}.json").write_text(
                    json.dumps(meta_rec, indent=2), encoding="utf-8"
                )
                runs.append({"prompt": pid, "harness": h, "rep": rep, "run": rec})
                print(f"    -> status={rec['status']} cost={rec.get('total_cost_usd')} "
                      f"dur_ms={rec.get('duration_ms')} out_tok={rec.get('output_tokens')}",
                      file=sys.stderr, flush=True)
    return runs


def load_existing_runs(reps: int) -> list[dict]:
    """Re-load runs from eval/runs/ for --aggregate-only."""
    runs: list[dict] = []
    for pid in PROMPTS:
        for h in HARNESSES:
            for rep in range(1, reps + 1):
                tag = f"{pid}_{h}_{rep}"
                txt_p = RUNS_DIR / f"{tag}.txt"
                json_p = RUNS_DIR / f"{tag}.json"
                if not txt_p.exists():
                    continue
                result = txt_p.read_text(encoding="utf-8")
                meta = {}
                if json_p.exists():
                    try:
                        meta = json.loads(json_p.read_text(encoding="utf-8"))
                    except (ValueError, json.JSONDecodeError):
                        meta = {}
                rec = dict(meta)
                rec["result"] = result
                rec.setdefault("status", "ok" if result.strip() else "empty_result")
                runs.append({"prompt": pid, "harness": h, "rep": rep, "run": rec})
    return runs


def build_report(runs: list[dict], client: GwoscClient, reps: int) -> dict:
    # Fetch ground truth per prompt (live).
    ground_truth: dict[str, Optional[dict]] = {}
    for pid, meta in PROMPTS.items():
        gt = client.ground_truth(meta["event"], meta["catalog"])
        ground_truth[pid] = gt
        if gt is None:
            print(f"WARNING: could not resolve ground truth for {pid} "
                  f"({meta['event']} in {meta['catalog']})", file=sys.stderr)

    # Score every run.
    for r in runs:
        gt = ground_truth.get(r["prompt"])
        r["scored"] = score_run(r["run"].get("result", ""), gt)

    # Per-cell aggregation.
    per_cell: dict[str, dict[str, dict]] = {}
    for pid in PROMPTS:
        per_cell[pid] = {}
        for h in HARNESSES:
            cell_runs = [r for r in runs if r["prompt"] == pid and r["harness"] == h]
            per_cell[pid][h] = aggregate_cell(cell_runs)

    # Overall per harness.
    overall: dict[str, dict] = {}
    for h in HARNESSES:
        overall[h] = aggregate_cell([r for r in runs if r["harness"] == h])

    network_status = (
        "ok" if client.network_ok else ("unreachable" if client.network_ok is False else "untested")
    )

    return {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scorer": "praxis-aggregate-eval/1.0",
        "network_status": network_status,
        "scoring_note": "Objective only (regex + numeric diff vs live GWOSC). No LLM-judge.",
        "matrix": {
            "n_prompts": len(PROMPTS),
            "n_reps": reps,
            "n_harnesses": len(HARNESSES),
            "n_runs": len(runs),
            "prompts": {pid: {"event": m["event"], "catalog": m["catalog"], "prompt": m["prompt"]}
                        for pid, m in PROMPTS.items()},
            "harnesses": {
                "A": "baseline: claude -p <prompt> --output-format json (neutral cwd)",
                "B": ("praxis: claude --plugin-dir " + PRAXIS_DIR +
                      " --dangerously-skip-permissions -p <prompt> --output-format json (cwd /tmp)"),
            },
        },
        "metric_definitions": {
            "has_gwosc_doi": r"regex 10\.7935/ present in answer",
            "has_asym_err": r"regex +x / -y asymmetric error present",
            "m1_current_match": "abs(stated_m1 - gwosc_m1) <= max(1.5, gwosc_m1_upper_error)",
            "provenance_rate": "mean(has_gwosc_doi)",
            "asymmetric_uncertainty_rate": "mean(has_asym_err)",
            "current_catalog_match_rate": "mean(m1_current_match) over parseable runs",
        },
        "ground_truth": ground_truth,
        "overall": overall,
        "per_cell": per_cell,
        "runs": [
            {
                "prompt": r["prompt"],
                "harness": r["harness"],
                "rep": r["rep"],
                "run": {k: v for k, v in r["run"].items()
                        if k not in ("result", "raw_stdout_head")},
                "scored": r["scored"],
            }
            for r in runs
        ],
    }


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Praxis A/B averaged evaluation + aggregation")
    ap.add_argument("--reps", type=int, default=3, help="reps per prompt x harness (default 3)")
    ap.add_argument("--neutral-dir", default="/tmp", help="neutral cwd for claude runs (default /tmp)")
    ap.add_argument("--aggregate-only", action="store_true",
                    help="skip running claude; re-aggregate existing eval/runs/")
    args = ap.parse_args(argv[1:])

    if args.aggregate_only:
        print("aggregate-only: loading existing runs from eval/runs/ ...", file=sys.stderr)
        runs = load_existing_runs(args.reps)
        if not runs:
            print("error: no existing runs found in eval/runs/", file=sys.stderr)
            return 2
    else:
        runs = run_matrix(args.reps, args.neutral_dir)

    client = GwoscClient()
    report = build_report(runs, client, args.reps)

    (HERE / "aggregate.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (HERE / "aggregate.md").write_text(render_md(report), encoding="utf-8")

    # Console summary.
    print("\n=== DONE ===", file=sys.stderr)
    print(f"wrote {HERE/'aggregate.json'}", file=sys.stderr)
    print(f"wrote {HERE/'aggregate.md'}", file=sys.stderr)
    oa = report["overall"]["A"]; ob = report["overall"]["B"]
    print(f"\nA provenance={_rate_str(oa['provenance_rate'])} "
          f"match={_rate_str(oa['current_catalog_match_rate'])} "
          f"asym={_rate_str(oa['asymmetric_uncertainty_rate'])}", file=sys.stderr)
    print(f"B provenance={_rate_str(ob['provenance_rate'])} "
          f"match={_rate_str(ob['current_catalog_match_rate'])} "
          f"asym={_rate_str(ob['asymmetric_uncertainty_rate'])}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
