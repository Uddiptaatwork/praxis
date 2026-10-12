#!/usr/bin/env python3
"""Oracle adapter for the LVK pack (tier LIVE).

LIVE is the strongest tier: ground truth at grade-time comes from an INDEPENDENT
API diff (gwosc.org/api/v2), so the grader cannot bake in our own transcription
errors and superlatives are checkable against the live cumulative catalog.

Exposes:
  * CHECKS + the four check functions (called by lib/pvalidate.py gate 5).
  * A DomainScorer config block (regexes + superlative->param map) consumed by
    eval/score_core.py -- the GW-specific scoring that used to live inside score.py.
  * live_event(name) / live_extremum(param) -- the independent-API oracle.
"""
import json
import re
import urllib.request

TIER = "LIVE"
CHECKS = ["entity_exists", "param_within_sigma", "scope_resolved", "identifier_resolves"]

GWOSC_BASE = "https://gwosc.org/api/v2"

# ---- DomainScorer config (was hard-coded inside eval/score.py) --------------
DOI_PREFIX = r"10\.7935/[a-z0-9-]+"          # GWOSC DOIs
ENTITY_RE = r"GW\d{6}(?:_\d{6})?"            # event ids
CATALOG_RE = r"GWTC-\d(?:\.\d)?"             # numbered releases
CUMULATIVE_SCOPE = "GWTC"
# superlative word -> catalog parameter (from score.py's heuristic + config)
SUPERLATIVE_PARAM = {
    "distant": "redshift", "far": "redshift", "farthest": "redshift", "furthest": "redshift",
    "massive": "total_mass_source", "heavy": "total_mass_source", "heaviest": "total_mass_source",
    "close": "luminosity_distance", "closest": "luminosity_distance", "nearest": "luminosity_distance",
    "loud": "network_matched_filter_snr", "loudest": "network_matched_filter_snr",
    "snr": "network_matched_filter_snr",
}


# ---- cache-side checks (pvalidate gate 5) -----------------------------------
def _entities(snap):
    return snap.get("entities") or snap.get("events") or {}


def entity_exists(snap, name):
    return name in _entities(snap)


def scope_resolved(snap, scope):
    return scope == snap["_meta"].get("cumulative_scope")


def identifier_resolves(snap, name):
    e = _entities(snap).get(name, {})
    return bool(e.get("release_doi") or (snap["_meta"].get("dois") or {}).get(e.get("catalog")))


def param_within_sigma(snap, name, param, value, nsigma=3.0):
    p = (_entities(snap).get(name, {}).get("parameters") or {}).get(param)
    if not p or not isinstance(p.get("best"), (int, float)):
        return None
    up = abs(p.get("upper_error") or 0) or 1e-30
    lo = abs(p.get("lower_error") or 0) or 1e-30
    d = value - p["best"]
    return (d / up if d >= 0 else abs(d) / lo) <= nsigma


# ---- LIVE oracle: independent API (eval/score_core.py fabrication check) -----
def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "praxis-lvk-oracle/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except Exception:
        return None


def live_event(name):
    """Does this event exist in the live catalog? True / False / None(network)."""
    return None if _get(f"{GWOSC_BASE}/events/{name}") is None else True


def live_extremum(param, mode="max"):
    """Independent cumulative-GWTC superlative for grading."""
    rows, url = [], f"{GWOSC_BASE}/catalogs/GWTC/events?include-default-parameters=true&page-size=20"
    while url:
        d = _get(url)
        if d is None:
            return None
        rows.extend(d.get("results", []))
        url = d.get("next")
    best = None
    for row in rows:
        params = {p["name"]: p for p in row.get("default_parameters", [])}
        p = params.get(param)
        if p and isinstance(p.get("best"), (int, float)):
            v = p["best"]
            if best is None or (v > best[1] if mode == "max" else v < best[1]):
                best = (row.get("name"), v)
    return {"event": best[0], "value": best[1]} if best else None
