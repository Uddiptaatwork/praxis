#!/usr/bin/env python3
"""Oracle adapter for the PTA pack (tier REDERIVE).

REDERIVE is categorically weaker than LIVE: there is NO live PTA catalog API, so
ground truth cannot be diffed against an independent source. Instead the cache is
built DETERMINISTICALLY from the published release tables (Zenodo/journal DOIs)
and must BYTE-MATCH on a second build -- this catches transcription drift and
partial-build corruption, NOT semantic error. A human-signed transcription audit
(pack.json oracle.transcription_audit) is required before the pack is 'verified';
until then it serves as community/unverified.

Exposes CHECKS + check functions (pvalidate gate 5) and a DomainScorer config.
"""
import hashlib
import json

TIER = "REDERIVE"
CHECKS = ["entity_exists", "param_within_sigma", "scope_resolved", "identifier_resolves"]

# ---- DomainScorer config ----------------------------------------------------
DOI_PREFIX = r"10\.(5281/zenodo|3847|1051)/[-._;()/:a-z0-9]+"   # Zenodo / ApJL / A&A
ENTITY_RE = r"(?:NANOGrav|EPTA|IPTA|PPTA|CPTA|MPTA)[- ]?\w+"
CATALOG_RE = r"(?:NANOGrav-15yr|EPTA-DR2|IPTA-DR2)"
CUMULATIVE_SCOPE = "IPTA-DR2"
SUPERLATIVE_PARAM = {
    "amplitude": "A_gwb", "strain": "A_gwb", "largest": "A_gwb", "highest": "A_gwb",
    "significant": "hd_significance_sigma", "significance": "hd_significance_sigma",
}


def _entities(snap):
    return snap.get("entities") or {}


def entity_exists(snap, name):
    ents = _entities(snap)
    if name in ents:
        return True
    nl = name.lower()
    return any(nl in [a.lower() for a in (e.get("id_aliases") or [])] for e in ents.values())


def scope_resolved(snap, scope):
    return scope == snap["_meta"].get("cumulative_scope")


def identifier_resolves(snap, name):
    e = _entities(snap).get(name, {})
    return bool(e.get("release_doi") or (snap["_meta"].get("dois") or {}).get(name))


def param_within_sigma(snap, name, param, value, nsigma=3.0):
    p = (_entities(snap).get(name, {}).get("parameters") or {}).get(param)
    if not p or not isinstance(p.get("best"), (int, float)):
        return None
    up = abs(p.get("upper_error") or 0) or 1e-30
    lo = abs(p.get("lower_error") or 0) or 1e-30
    d = value - p["best"]
    return (d / up if d >= 0 else abs(d) / lo) <= nsigma


# ---- REDERIVE oracle: byte-match a deterministic rebuild --------------------
def cache_fingerprint(snap):
    """Canonical hash of the entities+records payload (excludes retrieved_utc so a
    re-run at a different clock still byte-matches the SCIENCE)."""
    payload = {"entities": snap.get("entities"), "records": snap.get("records"),
               "record_params": snap["_meta"].get("record_params")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def rederive_matches(snap_a, snap_b):
    return cache_fingerprint(snap_a) == cache_fingerprint(snap_b)
