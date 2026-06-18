#!/usr/bin/env python3
"""Build a frozen local mirror of the cumulative GWOSC GWTC catalog.

Run this ONCE PER GWTC RELEASE (catalog data only changes when a new GWTC
paper/catalog is published). It pages the public v2 API (no auth, CORS-enabled),
collects every event's catalog-level default parameters, resolves each numbered
catalog's DOI, precomputes simple superlatives, and writes
``data/gwtc_snapshot.json`` with full provenance (source URL, UTC retrieval
time, per-catalog DOIs).

The ``gwosc-data`` skill reads this snapshot instead of live-querying on every
question. The snapshot is *retrieved* data with provenance, not recalled values
-- it satisfies the integrity rules "retrieve, don't recall" and "identifiers
are retrieved, never recalled."

Usage:
    python build_snapshot.py            # refresh the snapshot in ./data/

Per-event ``parameters`` come from the catalog list endpoint's
``default_parameters``. Events that lack full PE there (typically the newest
events) are still recorded -- the skill falls back to the live event-version
endpoint for those specific gaps.
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BASE = "https://gwosc.org/api/v2"
UMBRELLA = "GWTC"  # cumulative current-best view across all runs
EVENTS_URL = f"{BASE}/catalogs/{UMBRELLA}/events?include-default-parameters=true"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "data", "gwtc_snapshot.json")
UA = {"User-Agent": "praxis-gwosc-snapshot/1.0"}

# Parameters we precompute argmax/argmin records for (superlative questions).
RECORD_PARAMS = [
    "total_mass_source", "mass_1_source", "mass_2_source", "chirp_mass_source",
    "final_mass_source", "luminosity_distance", "redshift",
    "network_matched_filter_snr",
]
# Subfields kept for each parameter (carry the asymmetric errors + flags).
PARAM_FIELDS = ("best", "upper_error", "lower_error", "unit",
                "is_upper_limit", "is_lower_limit", "decimal_places")


def get(url, tries=5):
    """GET JSON with retry/backoff. The v2 API is throttled and 502s on load."""
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
            wait = 2 * (i + 1)
            print(f"  retry {i + 1}/{tries} after {e} (sleep {wait}s)", file=sys.stderr)
            time.sleep(wait)
    raise SystemExit(f"FAILED after {tries} tries: {url}\n  last error: {last}")


def params_to_dict(plist):
    out = {}
    for p in plist or []:
        name = p.get("name")
        if not name:
            continue
        out[name] = {k: p.get(k) for k in PARAM_FIELDS}
    return out


def main():
    events = {}
    url = EVENTS_URL
    page = 0
    expected = None
    while url:
        page += 1
        d = get(url)
        if expected is None:
            expected = d.get("results_count")
            print(f"catalog '{UMBRELLA}': {expected} events across {d.get('num_pages')} pages")
        for row in d.get("results", []):
            name = row.get("name")
            if not name:
                continue
            events[name] = {
                "shortName": row.get("shortName"),
                "gps": row.get("gps"),
                "version": row.get("version"),
                "catalog": row.get("catalog"),
                "detectors": row.get("detectors"),
                "parameters": params_to_dict(row.get("default_parameters")),
            }
        print(f"  page {page}/{d.get('num_pages')}: +{len(d.get('results', []))} (total {len(events)})")
        url = d.get("next")
        time.sleep(0.3)  # be polite to the throttled API

    # Resolve each numbered catalog's DOI (the umbrella GWTC has doi: null).
    cats = sorted({e["catalog"] for e in events.values() if e.get("catalog")})
    catalog_dois = {}
    for c in cats:
        try:
            catalog_dois[c] = get(f"{BASE}/catalogs/{c}").get("doi")
        except SystemExit:
            catalog_dois[c] = None
        time.sleep(0.2)

    # Precompute simple superlatives so the skill answers them with zero work.
    records = {}
    for pname in RECORD_PARAMS:
        vals = [
            (n, e["parameters"][pname]["best"])
            for n, e in events.items()
            if pname in e["parameters"]
            and isinstance(e["parameters"][pname].get("best"), (int, float))
        ]
        if not vals:
            continue
        hi = max(vals, key=lambda t: t[1])
        lo = min(vals, key=lambda t: t[1])
        records[pname] = {
            "max": {"event": hi[0], "best": hi[1], "catalog": events[hi[0]]["catalog"]},
            "min": {"event": lo[0], "best": lo[1], "catalog": events[lo[0]]["catalog"]},
            "n_with_value": len(vals),
        }

    snapshot = {
        "_meta": {
            "source": EVENTS_URL,
            "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "umbrella_catalog": UMBRELLA,
            "n_events": len(events),
            "results_count_reported": expected,
            "catalog_dois": catalog_dois,
            "record_params": RECORD_PARAMS,
            "note": (
                "Frozen mirror of the cumulative GWTC catalog from the GWOSC v2 API. "
                "Catalog data changes only when a new GWTC release is published; refresh "
                "by re-running build_snapshot.py. Per-event 'parameters' are the "
                "catalog-level default_parameters; events lacking full PE here (typically "
                "the newest) fall back to the live event-version endpoint."
            ),
        },
        "records": records,
        "events": events,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(snapshot, f, indent=1, sort_keys=True)

    print(f"\nwrote {OUT}")
    print(f"  events: {len(events)} (reported {expected})")
    print(f"  catalogs + DOIs: {catalog_dois}")
    if "total_mass_source" in records:
        r = records["total_mass_source"]["max"]
        print(f"  most massive (total_mass_source): {r['event']} = {r['best']} M_sun [{r['catalog']}]")
    if "luminosity_distance" in records:
        r = records["luminosity_distance"]["min"]
        print(f"  closest (luminosity_distance): {r['event']} = {r['best']} Mpc [{r['catalog']}]")


if __name__ == "__main__":
    main()
