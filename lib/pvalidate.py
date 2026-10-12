#!/usr/bin/env python3
"""pvalidate -- the teeth. Validates a Praxis domain pack against the contract.

A directory packs/<id>/ is a VALID pack iff pack.json + the cache + the oracle +
the authored expert conform. Gates split into two severities:

  FAIL  -- structural / integrity violations. The pack is `red`; it may not be
           marked initialized and may not advertise integrity claims.
  WARN  -- human-attestation gaps (no named expert signed off; no transcription
           audit). The pack is `green-unverified`: it works and its cache is
           well-formed, but it is flagged community/unverified in the marketplace.

  python lib/pvalidate.py packs/lvk            # validate one pack
  python lib/pvalidate.py packs/lvk packs/pta  # validate several
  python lib/pvalidate.py --online packs/lvk   # also HEAD-resolve DOIs over the network

Exit 0 = green or green-unverified; exit 1 = red (a FAIL fired).
"""
import json
import os
import re
import sys
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
DOI_RE = re.compile(r"^(https?://(dx\.)?doi\.org/)?10\.\d{4,9}/[-._;()/:A-Za-z0-9]+$")
UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
PLACEHOLDER_RE = re.compile(r"\[(FILL|TODO|PLACEHOLDER)[^\]]*\]|\[AUTHORED-STUB[^\]]*to fill[^\]]*\]",
                            re.IGNORECASE)


class Report:
    def __init__(self, pack):
        self.pack = pack
        self.fails = []
        self.warns = []
        self.oks = []

    def gate(self, gate_id, ok, msg, severity="FAIL"):
        line = f"gate {gate_id}: {msg}"
        if ok:
            self.oks.append(line)
        elif severity == "WARN":
            self.warns.append(line)
        else:
            self.fails.append(line)
        return ok

    @property
    def status(self):
        if self.fails:
            return "red"
        return "green-unverified" if self.warns else "green"

    def render(self):
        for l in self.oks:
            print(f"  OK   {l}")
        for l in self.warns:
            print(f"  WARN {l}")
        for l in self.fails:
            print(f"  FAIL {l}")
        print(f"  => {self.pack}: {self.status.upper()}")


def _load_json(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except (OSError, json.JSONDecodeError) as e:
        return None, str(e)


def _well_formed_doi(v):
    return isinstance(v, str) and bool(DOI_RE.match(v.strip()))


def _head_resolves(doi):
    try:
        import urllib.request
        url = doi if doi.startswith("http") else f"https://doi.org/{doi}"
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "praxis-pvalidate/1.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status < 400
    except Exception:
        return False


def validate(pack_dir, online=False):
    pid = os.path.basename(pack_dir.rstrip("/"))
    r = Report(pid)

    # ---- gate 1: manifest schema + contract + tier
    pj_path = os.path.join(pack_dir, "pack.json")
    pj, err = _load_json(pj_path)
    if not r.gate("1", pj is not None, f"pack.json loads ({err or 'ok'})"):
        r.render(); return r
    dom = pj.get("domain", {})
    oracle = pj.get("oracle", {})
    tier = oracle.get("tier")
    r.gate("1", str(pj.get("praxis_contract", "")).startswith("1."), "praxis_contract major == 1")
    r.gate("1", re.match(r"^[a-z0-9-]+$", dom.get("id", "")) is not None, f"domain.id well-formed ({dom.get('id')})")
    r.gate("1", tier in ("LIVE", "REDERIVE", "ASSERTED"), f"oracle.tier valid ({tier})")

    # ---- gate 2: expert agent + data skill exist, frontmatter, trigger vocab
    exp = os.path.join(pack_dir, pj.get("expert_agent", ""))
    skl = os.path.join(pack_dir, pj.get("data_skill", ""))
    exp_txt = open(exp).read() if os.path.isfile(exp) else ""
    skl_txt = open(skl).read() if os.path.isfile(skl) else ""
    r.gate("2", bool(exp_txt), f"expert agent exists ({pj.get('expert_agent')})")
    r.gate("2", bool(skl_txt), f"data skill exists ({pj.get('data_skill')})")
    r.gate("2", "model:" in exp_txt and "tools:" in exp_txt, "expert frontmatter declares model + tools")
    id_field = (pj.get("cache") or {}).get("id_field", "")
    r.gate("2", (id_field and id_field in skl_txt) or dom.get("id", "") in skl_txt,
           "data-skill description triggers on the domain identifier")

    # ---- gate 3: cache exists, validates, completeness
    cache_rel = (pj.get("cache") or {}).get("path", "")
    cache_path = os.path.join(pack_dir, cache_rel)
    snap, cerr = _load_json(cache_path)
    if not r.gate("3", snap is not None, f"cache loads ({cerr or cache_rel})"):
        r.render(); return r
    meta = snap.get("_meta", {})
    ents = snap.get("entities") or snap.get("events") or {}
    r.gate("3", UTC_RE.match(meta.get("retrieved_utc", "")) is not None,
           f"_meta.retrieved_utc parseable ({meta.get('retrieved_utc')})")
    rcr = meta.get("results_count_reported")
    r.gate("3", rcr == len(ents), f"completeness: len(entities)={len(ents)} == results_count_reported={rcr}")

    # ---- gate 4: every sources + cache DOI resolves (null-with-flag ok, empty-string FAIL)
    doi_problems = []
    src_dois = []
    for s in ((pj.get("sources") or {}).get("primary") or []):
        if "doi" in s:
            src_dois.append(("sources", s.get("name"), s.get("doi")))
    for k, v in (meta.get("dois") or {}).items():
        src_dois.append(("cache.dois", k, v))
    doi_status = meta.get("doi_status") or {}
    for where, name, v in src_dois:
        if v is None or v == "":
            if v == "":
                doi_problems.append(f"{where}:{name} empty-string DOI (use null + doi_status)")
            elif name not in doi_status and where == "cache.dois":
                doi_problems.append(f"{where}:{name} null DOI without doi_status flag")
        elif not _well_formed_doi(v):
            doi_problems.append(f"{where}:{name} malformed DOI {v!r}")
        elif online and not _head_resolves(v):
            doi_problems.append(f"{where}:{name} DOI did not resolve online: {v}")
    r.gate("4", not doi_problems, "DOIs well-formed/resolvable" + (f" -- {doi_problems}" if doi_problems else ""))

    # ---- gate 5: oracle importable, exposes checks; tier bookkeeping
    ora_rel = oracle.get("adapter", "")
    ora_path = os.path.join(pack_dir, ora_rel)
    ok_import, checks_ok = False, False
    if os.path.isfile(ora_path):
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"_ora_{pid}", ora_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            ok_import = True
            need = set(oracle.get("checks", []))
            have = set(getattr(mod, "CHECKS", []))
            checks_ok = need.issubset(have) if need else True
        except Exception as e:
            r.warns.append(f"gate 5: oracle import raised {e}")
    r.gate("5", ok_import, f"oracle adapter importable ({ora_rel})")
    r.gate("5", checks_ok, "oracle exposes the declared checks")
    audit = oracle.get("transcription_audit")
    if tier in ("REDERIVE", "ASSERTED"):
        r.gate("5", bool(audit), "transcription_audit present (tier REDERIVE/ASSERTED)", severity="WARN")

    # ---- gate 6: cumulative_scope lands in the cache
    cscope = (pj.get("cache") or {}).get("cumulative_scope")
    cats = {e.get("catalog") for e in ents.values()} | {e.get("release_tag") for e in ents.values()}
    r.gate("6", bool(cscope) and (cscope == meta.get("cumulative_scope") or cscope in cats or cscope in ents),
           f"cumulative_scope resolves ({cscope})")

    # ---- gate 7: record_params subset of what the cache carries
    present = set()
    for e in ents.values():
        present |= set((e.get("parameters") or {}).keys())
    present |= set((snap.get("records") or {}).keys())
    rp = set((pj.get("cache") or {}).get("record_params", []))
    missing_rp = rp - present
    r.gate("7", not missing_rp, "record_params ⊆ cache params" + (f" -- missing {missing_rp}" if missing_rp else ""))

    # ---- gate 8: sota index cited + license-gated
    sota_rel = (pj.get("sota") or {}).get("path", "cache/sota.json")
    sota_path = os.path.join(pack_dir, sota_rel)
    sota, serr = _load_json(sota_path)
    if sota is None:
        r.gate("8", False, f"sota.json present ({serr or sota_rel})", severity="WARN")
    else:
        open_only = pj.get("corpus_license") == "open-only"
        bad = []
        for p in sota.get("papers", []):
            if not _well_formed_doi(p.get("doi") or ""):
                bad.append(f"{p.get('id')}: malformed/missing DOI")
            if not p.get("asserted_utc"):
                bad.append(f"{p.get('id')}: no asserted_utc")
            if open_only and not p.get("source_license"):
                bad.append(f"{p.get('id')}: open-only corpus but no source_license")
        r.gate("8", not bad, "sota entries cited + license-gated" + (f" -- {bad}" if bad else ""))

    # ---- gate 9: no unfilled expert-judgment placeholder
    ph = PLACEHOLDER_RE.findall(exp_txt)
    r.gate("9", not ph, "no unfilled expert-judgment slots" + (f" -- {ph}" if ph else ""))

    # ---- gate 10: scope-rule drift (pack.json scope <-> expert prose)
    r.gate("10", (cscope or "") and (cscope in exp_txt),
           f"expert prose encodes cumulative_scope ({cscope})", severity="WARN")

    # ---- gate 11: tier consistency
    srcs = pj.get("sources") or {}
    if tier == "LIVE":
        r.gate("11", bool(srcs.get("live_api")) and bool(srcs.get("latest_release_probe")),
               "tier LIVE supplies live_api + latest_release_probe")
    else:
        hard = ((pj.get("sota") or {}).get("refresh") or {}).get("hard_expiry")
        r.gate("11", bool(hard), f"tier {tier} without live probe declares sota.refresh.hard_expiry")

    r.render()
    return r


def main():
    online = "--online" in sys.argv
    packs = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not packs:
        sys.exit("usage: pvalidate.py [--online] packs/<id> [packs/<id> ...]")
    worst = 0
    for p in packs:
        print(f"validating {p} ...")
        rep = validate(p, online=online)
        if rep.status == "red":
            worst = 1
        print()
    sys.exit(worst)


if __name__ == "__main__":
    main()
