#!/usr/bin/env python3
"""memory_prime -- assemble the /init expert briefing (deterministic, no LLM tokens).

/init calls this to gather EVERYTHING a fresh session needs to operate as a fluent
`<domain>` co-scientist, so the plugin doesn't have to be re-read each session. It
reads the core method (scientific-method loop, the role table, the integrity rules)
and the active pack (pack.json conventions/scope-traps/threats/M-I-S split/bridges,
the data-access cheatsheet, the landmark SOTA DOIs) and prints two briefing blocks:

  === WRITE MEMORY FILE: praxis-method.md ===        (domain-agnostic; write once)
  === WRITE MEMORY FILE: praxis-domain-<id>.md ===   (this pack's expertise)

The /init command writes each block verbatim into Claude's persistent memory dir
and indexes it in MEMORY.md. Everything here is a file read + reshape -- the few
minutes /init costs is the one-time read/format/ratify, not repeated per session.

  python lib/memory_prime.py <id>     # emit briefings for pack <id>
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _read(path):
    return open(path).read() if os.path.isfile(path) else ""


def _roles_from_claude_md():
    txt = _read(os.path.join(ROOT, "CLAUDE.md"))
    rows = []
    for m in re.finditer(r"^\|\s*(.+?)\s*\|\s*`?([a-z-]+)`?\s*\|\s*(.+?)\s*\|$", txt, re.M):
        role, agent, does = m.group(1), m.group(2), m.group(3)
        if agent in ("Agent", "---") or "Role" in role:
            continue
        rows.append((role, agent, does))
    return rows


def _loop_stages():
    txt = _read(os.path.join(ROOT, "skills", "scientific-method", "SKILL.md"))
    return re.findall(r"^\d+\.\s+\*\*(.+?)\*\*", txt, re.M)


def _integrity_rules():
    txt = _read(os.path.join(ROOT, "rules", "scientific-integrity.md"))
    out = re.findall(r"^\s*\d+\.\s+\*\*(.+?)\*\*", txt, re.M)
    if not out:
        out = re.findall(r"^\s*-\s+\*\*(.+?)\*\*", txt, re.M)
    return out


def method_briefing():
    roles = _roles_from_claude_md()
    stages = _loop_stages()
    rules = _integrity_rules()
    L = ["---",
         "name: praxis-method",
         "description: How Praxis runs the scientific method -- triage, the loop, the roles, the integrity non-negotiables. Recall for ANY investigation, analysis, or 'what does this tell us' request.",
         "metadata:",
         "  type: reference",
         "---",
         "",
         "Praxis is a small lab of specialist agents running an explicit, falsifiable method over real data -- not a single oracle. Do not answer from memory; retrieve with provenance.",
         "",
         "**Triage first.** Tier-0 (a single value, a count, a superlative, or anything asked *briefly*) -> answer fast from the active pack's cache via `pcache.py`, with asymmetric error + DOI, NO subagents. Tier-1 (a claim to test, a dataset, 'what does this mean', a reproduction/extension) -> run the full loop. The instant a Tier-0 answer needs an *inference*, escalate.",
         ""]
    if stages:
        L.append("**The loop:** " + " -> ".join(stages) + ".")
        L.append("")
    if roles:
        L.append("**The roles (subagents):**")
        for role, agent, does in roles:
            L.append(f"- `{agent}` -- {does}")
        L.append("")
    if rules:
        L.append("**Non-negotiables:** " + "; ".join(rules) + ". (see `rules/scientific-integrity.md`)")
        L.append("")
    L.append("Without an active pack this still runs on ANY domain -- retrieve from the field's authoritative source live (WebSearch/WebFetch) with provenance. A pack makes it a domain *expert*: see [[praxis-domain-*]].")
    return "praxis-method.md", "\n".join(L)


def domain_briefing(pid):
    pdir = os.path.join(ROOT, "packs", pid)
    pj = json.loads(_read(os.path.join(pdir, "pack.json")) or "{}")
    dom = pj.get("domain", {})
    cache = pj.get("cache", {})
    oracle = pj.get("oracle", {})
    conv = pj.get("conventions", {})
    mvi = pj.get("measured_vs_inferred", {})
    title = dom.get("title", pid)
    tier = oracle.get("tier")
    cscope = cache.get("cumulative_scope")

    sota = json.loads(_read(os.path.join(pdir, (pj.get("sota") or {}).get("path", "cache/sota.json"))) or "{}")
    papers = sota.get("papers", [])

    L = ["---",
         f"name: praxis-domain-{pid}",
         f"description: Praxis is primed as a {title} co-scientist ({dom.get('band','')}). Recall the conventions, scope traps, threats, and data-access path for any {title} question.",
         "metadata:",
         "  type: reference",
         "---",
         "",
         f"**Praxis is primed as a {title} co-scientist** (`{pid}`, {dom.get('band','')}). Oracle tier **{tier}**"
         + ("  -- live catalog API; cache-first, live on a miss." if tier == "LIVE"
            else "  -- NO live catalog API; cache-only, a miss is an honest absence, never a recall." if tier == "REDERIVE"
            else "  -- LLM-transcribed; every served value carries an UNVERIFIED-CACHE banner.") + " Runs the [[praxis-method]] loop, permeated by this domain.",
         ""]
    if conv.get("frames"):
        L.append("**Conventions:** " + "; ".join(conv["frames"]) + ".")
        L.append("")
    if conv.get("scope_trap"):
        L.append(f"**Scope trap (hard backstop):** {conv['scope_trap']} Cumulative scope for superlatives = `{cscope}`.")
        L.append("")
    if pj.get("skeptic_threats"):
        L.append("**Skeptic threats (mandatory pass):**")
        for t in pj["skeptic_threats"]:
            L.append(f"- {t}")
        L.append("")
    if mvi:
        L.append("**Measured / inferred / speculative:**")
        for k in ("measured", "inferred_under_assumptions", "speculative"):
            if mvi.get(k):
                L.append(f"- *{k.replace('_',' ')}:* " + "; ".join(mvi[k]))
        L.append("")
    if pj.get("open_limits"):
        L.append("**Open limits (license to decline):** " + "; ".join(pj["open_limits"]) + ".")
        L.append("")
    if pj.get("bridges"):
        L.append("**Cross-domain bridges:** " + "; ".join(pj["bridges"]) + ".")
        L.append("")
    # data-access cheatsheet
    cache_path = f"packs/{pid}/{cache.get('path','cache/'+pid+'_snapshot.json')}"
    rp = cache.get("record_params", [])
    L.append("**Data access (Tier-0, zero tokens):**")
    L.append(f"```")
    L.append(f"python lib/pcache.py entity <id> --cache {cache_path}")
    if rp:
        L.append(f"python lib/pcache.py max {rp[0]} --cache {cache_path}   # superlative, scope={cscope}")
    L.append(f"python lib/pcache.py meta --cache {cache_path}")
    L.append(f"```")
    L.append(f"Params in cache: {', '.join(rp)}." if rp else "")
    L.append("")
    if papers:
        L.append("**Landmark literature (SOTA index -- cite these, fetch extraction live):**")
        for p in papers:
            L.append(f"- {p.get('title')} -- {p.get('doi')} ({p.get('status','')})")
        L.append("")
    return f"praxis-domain-{pid}.md", "\n".join(L)


def main():
    if len(sys.argv) < 2:
        sys.exit("usage: python lib/memory_prime.py <pack-id>")
    pid = sys.argv[1]
    if not os.path.isdir(os.path.join(ROOT, "packs", pid)):
        sys.exit(f"no pack packs/{pid}/ -- run with an installed pack id "
                 f"({', '.join(os.listdir(os.path.join(ROOT,'packs'))) if os.path.isdir(os.path.join(ROOT,'packs')) else 'none'})")
    for fname, body in (method_briefing(), domain_briefing(pid)):
        print(f"=== WRITE MEMORY FILE: {fname} ===")
        print(body)
        print(f"=== END {fname} ===\n")


if __name__ == "__main__":
    main()
