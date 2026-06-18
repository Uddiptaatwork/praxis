#!/usr/bin/env python3
"""
Automated scorer for Praxis vs vanilla A/B comparison sets.

Parses a comparison markdown file (e.g. eval/comparison-set-1.md) and, for each
question and each system (A = vanilla, B = plugin), computes a set of *objective*,
regex/lookup-based metrics plus a live fabrication/correctness check against the
public GWOSC API.

Design constraints (per task spec):
  * Pure Python standard library only (urllib + json). No pip dependencies.
  * Runs on Python 3.13.
  * Graceful network degradation: if the GWOSC API is unreachable, still emit the
    regex-based metrics and mark fabrication checks as "unverified".
  * ONLY auto-score the objective axes. Subjective axes (measurement/inference/
    speculation separation, skepticism quality) are emitted as null / "manual" --
    we never fabricate a score for a human/LLM judge.

Output:
  * Machine-readable JSON to stdout.
  * A rendered markdown table (per-question, A vs B) printed to stderr so it does
    not pollute the JSON on stdout. (Redirect: `python3 score.py file.md 2>table.md`)

Usage:
    python3 eval/score.py [eval/comparison-set-1.md]

If no path is given it defaults to eval/comparison-set-1.md relative to this file.
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Regexes for the objective axes
# ---------------------------------------------------------------------------

# GWOSC DOIs use the prefix 10.7935.  e.g. 10.7935/qf3a-3z67
RE_GWOSC_DOI = re.compile(r"10\.7935/[a-z0-9-]+", re.IGNORECASE)

# Any DOI (used to separate "has a DOI at all" from "arXiv-only").
RE_ANY_DOI = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")

# arXiv identifiers, e.g. arXiv:2508.18082
RE_ARXIV = re.compile(r"arXiv:\d{4}\.\d{4,5}", re.IGNORECASE)

# Asymmetric error notation:  +21/-14   +6.1/-4.2   +0.8 / −1.2  (handles unicode minus)
# We require an explicit "+x / -y" shape so we don't catch plain ranges or single ±.
RE_ASYM_ERR = re.compile(
    r"\+\s*\d+(?:\.\d+)?\s*/\s*[-−]\s*\d+(?:\.\d+)?"
)

# Catalog tokens, e.g. GWTC-3, GWTC-2.1, GWTC-4.0
RE_CATALOG = re.compile(r"GWTC-\d(?:\.\d)?", re.IGNORECASE)

# Event names, e.g. GW190521 or GW230529_181500
RE_EVENT = re.compile(r"GW\d{6}(?:_\d{6})?")

# "Cumulative / umbrella" references -- the umbrella GWTC catalog (no release suffix)
# or the explicit word "cumulative".  We look for the bare token "GWTC" not directly
# followed by a "-<digit>" (that would be a specific release), or the word cumulative.
RE_CUMULATIVE_WORD = re.compile(r"\bcumulative\b", re.IGNORECASE)
RE_GWTC_UMBRELLA = re.compile(r"\bGWTC\b(?!-\d)")


# ---------------------------------------------------------------------------
# GWOSC API client (stdlib only, with retries + graceful failure)
# ---------------------------------------------------------------------------

GWOSC_BASE = "https://gwosc.org/api/v2"
USER_AGENT = "praxis-eval-scorer/1.0 (stdlib urllib)"
# Parameters relevant to the superlative questions in the comparison sets.
SUPERLATIVE_PARAMS = ("total_mass_source", "redshift", "luminosity_distance")


class GwoscClient:
    """Thin GWOSC API client.  Caches the cumulative catalog scan so we only page
    through all events once per run.  Tracks whether the network is reachable so
    callers can degrade gracefully."""

    def __init__(self, timeout: float = 20.0, retries: int = 4):
        self.timeout = timeout
        self.retries = retries
        # SSL context; fall back to an unverified context only if the default fails
        # (some minimal environments lack a CA bundle).  We try verified first.
        self._ctx = ssl.create_default_context()
        self.network_ok: Optional[bool] = None  # None = untested, True/False after first call
        self._catalog_cache: Optional[list[dict]] = None
        self._event_cache: dict[str, Optional[dict]] = {}

    # -- low level GET with retry/backoff on transient errors ---------------
    def _get(self, url: str) -> Optional[dict]:
        last_err: Optional[Exception] = None
        for attempt in range(self.retries):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    self.network_ok = True
                    return data
            except urllib.error.HTTPError as e:
                # 404 is a definitive "not found" -- don't retry, signal via None.
                if e.code == 404:
                    self.network_ok = True
                    return None
                # 502/503/504 are the transient proxy errors the GWOSC API throws.
                last_err = e
                if e.code in (500, 502, 503, 504) and attempt < self.retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                # Other HTTP errors: give up.
                break
            except (urllib.error.URLError, TimeoutError, ssl.SSLError, OSError) as e:
                last_err = e
                if attempt < self.retries - 1:
                    time.sleep(1.0 * (attempt + 1))
                    continue
                break
            except (ValueError, json.JSONDecodeError) as e:
                # Malformed response -- treat as a failed fetch.
                last_err = e
                break
        # All attempts exhausted.
        self.network_ok = False
        return None

    # -- event existence ----------------------------------------------------
    def event_exists(self, name: str) -> Optional[bool]:
        """Return True/False if the event is found, or None if the API is unreachable.

        Tries the name as-given first.  GWOSC accepts both short ("GW190521") and
        full ("GW190521_030229") identifiers; if a 6-digit-only name 404s we cannot
        usefully expand it without guessing the time suffix, so we just report it.
        """
        if name in self._event_cache:
            cached = self._event_cache[name]
            if cached is None and self.network_ok is False:
                return None
            return cached is not None

        url = f"{GWOSC_BASE}/events/{name}"
        data = self._get(url)
        if self.network_ok is False:
            # Network down -- we genuinely don't know.
            return None
        self._event_cache[name] = data
        return data is not None

    # -- cumulative catalog scan -------------------------------------------
    def cumulative_events(self) -> Optional[list[dict]]:
        """Page through the cumulative GWTC catalog with default parameters.

        Returns a list of event rows (each with name + default_parameters), or
        None if the API is unreachable.  Cached after the first successful scan.
        """
        if self._catalog_cache is not None:
            return self._catalog_cache

        rows: list[dict] = []
        url = (
            f"{GWOSC_BASE}/catalogs/GWTC/events"
            "?include-default-parameters=true&page-size=20"
        )
        while url:
            data = self._get(url)
            if data is None:
                # Either 404 (shouldn't happen for the catalog) or network failure.
                if self.network_ok is False:
                    return None
                break
            rows.extend(data.get("results", []))
            url = data.get("next")
        self._catalog_cache = rows
        return rows

    def true_extremum(self, param: str, mode: str = "max") -> Optional[dict]:
        """Find the cumulative-catalog event with the extreme value of `param`.

        Returns {"event": name, "value": v} or None if the catalog can't be read.
        `mode` is "max" or "min".
        """
        rows = self.cumulative_events()
        if rows is None:
            return None
        best_name: Optional[str] = None
        best_val: Optional[float] = None
        for row in rows:
            params = {p["name"]: p for p in row.get("default_parameters", [])}
            p = params.get(param)
            if not p:
                continue
            v = p.get("best")
            if v is None:
                continue
            if best_val is None or (mode == "max" and v > best_val) or (mode == "min" and v < best_val):
                best_val = v
                best_name = row.get("name")
        if best_name is None:
            return None
        return {"event": best_name, "value": best_val, "param": param}


# ---------------------------------------------------------------------------
# Parsing the comparison markdown
# ---------------------------------------------------------------------------

@dataclass
class Question:
    qid: str                       # "Q1"
    title: str                     # "Scope + provenance + uncertainty"
    prompt: str                    # the blockquoted question text
    answer_a: str = ""             # vanilla output
    answer_b: str = ""             # plugin output
    ground_truth: str = ""         # raw text of the <details> key block


def parse_comparison(text: str) -> list[Question]:
    """Parse a comparison-set markdown file into Question objects.

    Structure (per the spec / observed file):
        ## Q1 — <title>
        > <prompt...>
        <details>...ground-truth key...</details>
        **A — vanilla:**
        ```
        <answer A>
        ```
        **B — plugin:**
        ```
        <answer B>
        ```
    We slice the file on the `## Q<N>` headers, then extract pieces within each
    section.  We deliberately stop at the first `---`-after-answers / next `## `
    boundary so the trailing "Results & scoring" section is ignored.
    """
    questions: list[Question] = []

    # Split into top-level sections on H2 headers.  Keep the header line.
    # A question header looks like:  ## Q1 — Scope + provenance + uncertainty
    section_re = re.compile(r"^##\s+(Q\d+)\s*[—-]\s*(.+?)\s*$", re.MULTILINE)
    matches = list(section_re.finditer(text))
    for i, m in enumerate(matches):
        qid = m.group(1)
        title = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[start:end]

        # Prompt: the first blockquote line(s) starting with ">".
        prompt = _extract_prompt(body)

        # Ground-truth key: text inside the <details>...</details>.
        gt = _extract_details(body)

        # Answers: fenced code blocks following the **A — vanilla:** / **B — plugin:** labels.
        answer_a = _extract_labeled_codeblock(body, "A")
        answer_b = _extract_labeled_codeblock(body, "B")

        questions.append(
            Question(
                qid=qid,
                title=title,
                prompt=prompt,
                answer_a=answer_a,
                answer_b=answer_b,
                ground_truth=gt,
            )
        )
    return questions


def _extract_prompt(body: str) -> str:
    lines = []
    for line in body.splitlines():
        s = line.strip()
        if s.startswith(">"):
            lines.append(s.lstrip(">").strip())
        elif lines and not s:
            # blank line after we started collecting -> end of the blockquote
            break
        elif lines:
            break
    return " ".join(l for l in lines if l).strip("* ").strip()


def _extract_details(body: str) -> str:
    m = re.search(r"<details>(.*?)</details>", body, re.DOTALL | re.IGNORECASE)
    if not m:
        return ""
    inner = m.group(1)
    # Strip the <summary>...</summary> tag.
    inner = re.sub(r"<summary>.*?</summary>", "", inner, flags=re.DOTALL | re.IGNORECASE)
    return inner.strip()


def _extract_labeled_codeblock(body: str, system: str) -> str:
    """Find the fenced code block that follows the `**<system> — ...:**` label.

    `system` is "A" or "B".  We match the label then the next ``` ... ``` fence.
    """
    # Label like: **A — vanilla:**   or   **B — plugin:**
    label_re = re.compile(
        r"\*\*\s*" + re.escape(system) + r"\s*[—-].*?:\s*\*\*",
        re.IGNORECASE,
    )
    lm = label_re.search(body)
    if not lm:
        return ""
    after = body[lm.end():]
    # First fenced block after the label.
    fence_re = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)
    fm = fence_re.search(after)
    if not fm:
        return ""
    return fm.group(1).rstrip("\n")


# ---------------------------------------------------------------------------
# Scoring an individual answer
# ---------------------------------------------------------------------------

@dataclass
class AnswerMetrics:
    # 1. Provenance
    gwosc_doi_count: int = 0
    gwosc_dois: list[str] = field(default_factory=list)
    # 2. Uncertainty
    asymmetric_error_count: int = 0
    asymmetric_error_examples: list[str] = field(default_factory=list)
    # 3. Catalog scope
    catalogs_cited: list[str] = field(default_factory=list)
    cumulative_referenced: bool = False
    # 4. Citations
    arxiv_count: int = 0
    arxiv_ids: list[str] = field(default_factory=list)
    doi_count: int = 0
    dois: list[str] = field(default_factory=list)
    hand_typed_identifier_risk: bool = False  # arXiv present but no DOI
    # 5. Fabrication / correctness
    events_mentioned: list[str] = field(default_factory=list)
    event_findings: list[dict] = field(default_factory=list)
    # Subjective axes -- NOT auto-scored.  Always null/"manual".
    measurement_inference_speculation: Optional[str] = None
    skepticism_quality: Optional[str] = None


def _dedup(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def score_answer(
    text: str,
    *,
    is_superlative: bool,
    superlative_param: Optional[str],
    superlative_mode: str,
    client: GwoscClient,
) -> AnswerMetrics:
    """Compute all objective metrics for one answer block.

    `is_superlative` flags Q-type questions where the named event is claimed to be
    an extremum (e.g. "most distant").  For those we additionally check whether the
    named event is actually the catalog extremum via the live API.
    """
    m = AnswerMetrics()

    # 1. Provenance -- GWOSC DOIs
    gwosc = RE_GWOSC_DOI.findall(text)
    m.gwosc_dois = _dedup(gwosc)
    m.gwosc_doi_count = len(gwosc)

    # 2. Uncertainty -- asymmetric error notation
    asym = RE_ASYM_ERR.findall(text)
    # findall returns full match strings since there are no capturing groups now
    asym_matches = [mt.group(0) for mt in RE_ASYM_ERR.finditer(text)]
    m.asymmetric_error_count = len(asym_matches)
    m.asymmetric_error_examples = _dedup(asym_matches)[:10]

    # 3. Catalog scope
    cats = [c.upper() for c in RE_CATALOG.findall(text)]
    m.catalogs_cited = _dedup(cats)
    m.cumulative_referenced = bool(
        RE_CUMULATIVE_WORD.search(text) or RE_GWTC_UMBRELLA.search(text)
    )

    # 4. Citations -- arXiv vs DOI
    arxiv = RE_ARXIV.findall(text)
    m.arxiv_ids = _dedup(arxiv)
    m.arxiv_count = len(arxiv)
    all_dois = RE_ANY_DOI.findall(text)
    m.dois = _dedup(all_dois)
    m.doi_count = len(all_dois)
    # arXiv ids present but zero DOIs => the citations are hand-typed identifiers,
    # which (per the integrity rules) are a "retrieved source?" red flag.
    m.hand_typed_identifier_risk = m.arxiv_count > 0 and m.doi_count == 0

    # 5. Fabrication / correctness -- named events vs the live GWOSC API
    events = _dedup(RE_EVENT.findall(text))
    m.events_mentioned = events

    # Compute the true extremum once (if this is a superlative question).
    true_ext: Optional[dict] = None
    if is_superlative and superlative_param:
        true_ext = client.true_extremum(superlative_param, mode=superlative_mode)

    for ev in events:
        finding: dict[str, Any] = {"event": ev}
        exists = client.event_exists(ev)
        if exists is None:
            finding["exists"] = "unverified"
        else:
            finding["exists"] = bool(exists)

        if is_superlative and superlative_param:
            if true_ext is None:
                finding["is_true_extremum"] = "unverified"
            else:
                finding["is_true_extremum"] = (ev == true_ext["event"])
                finding["true_extremum_event"] = true_ext["event"]
                finding["true_extremum_value"] = true_ext["value"]
                finding["extremum_param"] = true_ext["param"]
        m.event_findings.append(finding)

    return m


# ---------------------------------------------------------------------------
# Per-question configuration: which questions are superlative, and on what param
# ---------------------------------------------------------------------------

# We key off the question id.  This is intentionally small + explicit so the
# scorer stays robust and transparent; extend as new comparison sets are added.
SUPERLATIVE_CONFIG: dict[str, dict[str, str]] = {
    # Q1: "most distant binary black hole merger detected so far"
    "Q1": {"param": "redshift", "mode": "max"},
}


def detect_superlative(q: Question) -> tuple[bool, Optional[str], str]:
    """Decide whether a question is a superlative/extremum question and on which
    parameter.  Uses the explicit config first, then a light heuristic on the
    prompt text as a fallback."""
    cfg = SUPERLATIVE_CONFIG.get(q.qid)
    if cfg:
        return True, cfg["param"], cfg["mode"]

    # Heuristic fallback for unconfigured sets.
    prompt = q.prompt.lower()
    superlative_words = ("most ", "farthest", "furthest", "highest", "largest",
                         "heaviest", "lowest", "smallest", "lightest", "nearest", "closest")
    if any(w in prompt for w in superlative_words):
        if "distant" in prompt or "far" in prompt:
            return True, "redshift", "max"
        if "massive" in prompt or "heavy" in prompt or "mass" in prompt:
            return True, "total_mass_source", "max"
    return False, None, "max"


# ---------------------------------------------------------------------------
# Markdown table rendering
# ---------------------------------------------------------------------------

def _fmt_events(findings: list[dict]) -> str:
    if not findings:
        return "—"
    parts = []
    for f in findings:
        ev = f["event"]
        exists = f.get("exists")
        if exists == "unverified":
            tag = "?"
        elif exists is True:
            tag = "ok"
        else:
            tag = "MISSING"
        s = f"{ev}({tag}"
        if "is_true_extremum" in f:
            ite = f["is_true_extremum"]
            if ite == "unverified":
                s += ",extremum?"
            elif ite is True:
                s += ",extremum=YES"
            else:
                s += f",extremum=NO→{f.get('true_extremum_event')}"
        s += ")"
        parts.append(s)
    return "<br>".join(parts)


def render_markdown(result: dict) -> str:
    lines: list[str] = []
    lines.append(f"# Auto-scored objective metrics — {result['source_file']}")
    lines.append("")
    lines.append(f"_Network to GWOSC API: **{result['network_status']}**_")
    lines.append("")

    # Objective metrics table
    lines.append("## Objective metrics (auto-scored)")
    lines.append("")
    header = (
        "| Metric | "
        + " | ".join(
            f"{q['qid']} A | {q['qid']} B" for q in result["questions"]
        )
        + " |"
    )
    sep = "|---|" + "|".join([":--:"] * (2 * len(result["questions"]))) + "|"
    lines.append(header)
    lines.append(sep)

    def row(label: str, getter) -> str:
        cells = []
        for q in result["questions"]:
            cells.append(str(getter(q["a"])))
            cells.append(str(getter(q["b"])))
        return f"| {label} | " + " | ".join(cells) + " |"

    lines.append(row("GWOSC DOIs (count)", lambda a: a["gwosc_doi_count"]))
    lines.append(row("Asymmetric errors (count)", lambda a: a["asymmetric_error_count"]))
    lines.append(row("Catalogs cited", lambda a: ", ".join(a["catalogs_cited"]) or "—"))
    lines.append(row("Cumulative/umbrella ref", lambda a: "yes" if a["cumulative_referenced"] else "no"))
    lines.append(row("arXiv ids (count)", lambda a: a["arxiv_count"]))
    lines.append(row("DOIs (count)", lambda a: a["doi_count"]))
    lines.append(row("Hand-typed-id risk", lambda a: "RISK" if a["hand_typed_identifier_risk"] else "—"))
    lines.append(row("Events + verification", lambda a: _fmt_events(a["event_findings"])))
    lines.append("")

    # Subjective axes -- explicitly NOT auto-scored
    lines.append("## Subjective axes (NOT auto-scored — need human/LLM judge)")
    lines.append("")
    lines.append("| Axis | Status |")
    lines.append("|---|---|")
    lines.append("| Measurement / inference / speculation separation | manual (emitted as null) |")
    lines.append("| Skepticism quality (priors, systematics, selection) | manual (emitted as null) |")
    lines.append("| Retrieval-vs-recall (was it fetched live?) | not directly observable from text — manual |")
    lines.append("")

    # Fabrication headline
    lines.append("## Fabrication / correctness findings (headline)")
    lines.append("")
    for q in result["questions"]:
        for sys_label, key in (("A (vanilla)", "a"), ("B (plugin)", "b")):
            ans = q[key]
            for f in ans["event_findings"]:
                notes = []
                if f.get("exists") is False:
                    notes.append("EVENT NOT FOUND on GWOSC")
                elif f.get("exists") == "unverified":
                    notes.append("existence unverified (API unreachable)")
                if f.get("is_true_extremum") is False:
                    notes.append(
                        f"NOT the true extremum — true {f.get('extremum_param')} extremum is "
                        f"{f.get('true_extremum_event')} ({f.get('true_extremum_value')})"
                    )
                elif f.get("is_true_extremum") == "unverified":
                    notes.append("extremum check unverified")
                if notes:
                    lines.append(f"- **{q['qid']} {sys_label}** — `{f['event']}`: " + "; ".join(notes))
    if not any(
        f.get("exists") is False or f.get("is_true_extremum") is False
        for q in result["questions"]
        for key in ("a", "b")
        for f in q[key]["event_findings"]
    ):
        lines.append("- (no fabrication issues detected)")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    # Default path: eval/comparison-set-1.md relative to this script.
    default_path = Path(__file__).resolve().parent / "comparison-set-1.md"
    path = Path(argv[1]).resolve() if len(argv) > 1 else default_path

    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    questions = parse_comparison(text)
    if not questions:
        print(f"error: no questions parsed from {path}", file=sys.stderr)
        return 3

    client = GwoscClient()

    out_questions = []
    for q in questions:
        is_sup, param, mode = detect_superlative(q)
        a_metrics = score_answer(
            q.answer_a,
            is_superlative=is_sup,
            superlative_param=param,
            superlative_mode=mode,
            client=client,
        )
        b_metrics = score_answer(
            q.answer_b,
            is_superlative=is_sup,
            superlative_param=param,
            superlative_mode=mode,
            client=client,
        )
        out_questions.append(
            {
                "qid": q.qid,
                "title": q.title,
                "prompt": q.prompt,
                "is_superlative": is_sup,
                "superlative_param": param,
                "superlative_mode": mode if is_sup else None,
                "a": asdict(a_metrics),
                "b": asdict(b_metrics),
            }
        )

    network_status = (
        "ok" if client.network_ok else ("unreachable" if client.network_ok is False else "untested")
    )

    result = {
        "source_file": str(path),
        "scorer_version": "1.0",
        "network_status": network_status,
        "auto_scored_axes": [
            "provenance_gwosc_doi",
            "uncertainty_asymmetric_errors",
            "catalog_scope",
            "citations_arxiv_vs_doi",
            "fabrication_event_verification",
        ],
        "manual_axes": [
            "measurement_inference_speculation",
            "skepticism_quality",
            "retrieval_vs_recall",
        ],
        "questions": out_questions,
    }

    # Markdown table -> stderr (so stdout stays pure JSON).
    print(render_markdown(result), file=sys.stderr)
    # Machine-readable JSON -> stdout.
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
