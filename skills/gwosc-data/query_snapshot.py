#!/usr/bin/env python3
"""Query the frozen local GWTC snapshot -- the fast path for GWOSC lookups.

This reads ``data/gwtc_snapshot.json`` (built by build_snapshot.py) and answers
single-event lookups, counts, and superlatives instantly, with provenance, and
WITHOUT any network call. Use this for quick/factual questions instead of
live-querying the v2 API.

Every answer carries the asymmetric uncertainty (+upper/-lower) and provenance
(catalog + DOI + snapshot retrieval time), per the scientific-integrity rules.

    python query_snapshot.py event GW150914
    python query_snapshot.py count [--catalog GWTC-5.0]
    python query_snapshot.py max total_mass_source [--catalog GWTC-5.0]
    python query_snapshot.py min luminosity_distance
    python query_snapshot.py list --catalog GWTC-5.0 [--limit 30]
    python query_snapshot.py catalogs
    python query_snapshot.py meta

Add --json to any command for machine-readable output (for analyst-coder).
Exit code 2 means "not in snapshot, fall back to the live v2 API."

When to fall back to LIVE (build_snapshot.py docs / gwosc-data SKILL.md):
  - the event is newer than the snapshot's retrieved_utc (not found here);
  - you need full posteriors or strain (snapshot holds catalog-level params);
  - the catalog DOI is empty and full provenance is required (one event-version
    fetch fills it);
  - the user explicitly asks to re-verify against the live catalog.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "data", "gwtc_snapshot.json")

# Friendly-term -> (param, reducer) so the skill can map natural language.
COMMON_ORDER = [
    "chirp_mass_source", "total_mass_source", "mass_1_source", "mass_2_source",
    "final_mass_source", "chi_eff", "final_spin", "luminosity_distance",
    "redshift", "network_matched_filter_snr", "far", "p_astro",
]


def load():
    if not os.path.exists(SNAP):
        sys.exit(f"snapshot missing: {SNAP}\nRun: python {os.path.join(HERE, 'build_snapshot.py')}")
    with open(SNAP) as f:
        return json.load(f)


def doi_for(snap, catalog):
    d = (snap["_meta"].get("catalog_dois") or {}).get(catalog)
    return d if d else None


def provenance(snap, catalog):
    doi = doi_for(snap, catalog)
    cite = f"{catalog}, {doi}" if doi else f"{catalog} (catalog DOI not exposed by GWOSC v2 -- live event-version fetch for per-event DOI)"
    return f"{cite}; snapshot retrieved {snap['_meta'].get('retrieved_utc')}"


def fmt_param(name, p):
    best = p.get("best")
    if best is None:
        return f"  {name}: (no value in catalog list)"
    unit = p.get("unit") or ""
    unit = f" {unit}".rstrip()
    up, lo = p.get("upper_error"), p.get("lower_error")
    if p.get("is_upper_limit"):
        body = f"< {best}{unit}"
    elif p.get("is_lower_limit"):
        body = f"> {best}{unit}"
    elif up is not None and lo is not None:
        # GWOSC stores lower_error already signed; normalize to +up/-lo display.
        body = f"{best} +{abs(up)}/-{abs(lo)}{unit}"
    else:
        body = f"{best}{unit} (no CI in catalog list -- live fetch for full posterior)"
    return f"  {name} = {body}"


def resolve(snap, q):
    """Return (name, data) or exit. Match full id, shortName, or alias prefix."""
    events = snap["events"]
    if q in events:
        return q, events[q]
    ql = q.lower()
    cands = []
    for name, data in events.items():
        if name.lower() == ql or (data.get("shortName") or "").lower() == ql:
            return name, data
        if name.lower().startswith(ql + "_") or name.lower().startswith(ql):
            cands.append(name)
    if len(cands) == 1:
        return cands[0], events[cands[0]]
    if len(cands) > 1:
        sys.exit(f"'{q}' is ambiguous: {', '.join(sorted(cands))}\nUse the full id.")
    # Not found -> signal the caller to fall back to the live API.
    print(f"NOT IN SNAPSHOT: '{q}'. It may be newer than {snap['_meta'].get('retrieved_utc')} "
          f"-- fall back to the live v2 API (https://gwosc.org/api/v2/events/{q}).", file=sys.stderr)
    sys.exit(2)


def cmd_event(snap, a):
    name, data = resolve(snap, a.id)
    if a.json:
        print(json.dumps({"name": name, **data,
                          "provenance": provenance(snap, data.get("catalog"))}, indent=1))
        return
    params = data.get("parameters", {})
    print(f"{name}  (shortName {data.get('shortName')}, version {data.get('version')})")
    print(f"  catalog: {data.get('catalog')}   detectors: {data.get('detectors')}   gps: {data.get('gps')}")
    print("  --- parameters (best +upper/-lower) ---")
    seen = set()
    for k in COMMON_ORDER:
        if k in params:
            print(fmt_param(k, params[k]))
            seen.add(k)
    for k in sorted(params):
        if k not in seen:
            print(fmt_param(k, params[k]))
    print(f"  PROVENANCE: {provenance(snap, data.get('catalog'))}")


def _numeric_events(snap, param, catalog=None):
    out = []
    for n, e in snap["events"].items():
        if catalog and e.get("catalog") != catalog:
            continue
        p = e.get("parameters", {}).get(param)
        if p and isinstance(p.get("best"), (int, float)):
            out.append((n, e, p))
    return out


def cmd_extremum(snap, a, which):
    rows = _numeric_events(snap, a.param, a.catalog)
    if not rows:
        sys.exit(f"no events carry numeric '{a.param}'"
                 + (f" in {a.catalog}" if a.catalog else "")
                 + " in the snapshot -- check the param name or fall back to live.")
    pick = (max if which == "max" else min)(rows, key=lambda t: t[2]["best"])
    n, e, p = pick
    scope = a.catalog or snap["_meta"].get("umbrella_catalog")
    if a.json:
        print(json.dumps({"which": which, "param": a.param, "scope": scope, "event": n,
                          "value": p, "provenance": provenance(snap, e.get("catalog"))}, indent=1))
        return
    print(f"{which.upper()} {a.param} in {scope} ({len(rows)} events have this param):")
    print(f"  {n}: {fmt_param(a.param, p).strip()}")
    print(f"  PROVENANCE: {provenance(snap, e.get('catalog'))}")
    if not a.catalog:
        print("  NOTE: this is the cumulative (umbrella GWTC) answer. For a per-release "
              "answer (e.g. GWTC-5.0 only), pass --catalog; the two differ.")


def cmd_count(snap, a):
    if a.catalog:
        n = sum(1 for e in snap["events"].values() if e.get("catalog") == a.catalog)
        scope = a.catalog
    else:
        n = snap["_meta"].get("n_events", len(snap["events"]))
        scope = snap["_meta"].get("umbrella_catalog") + " (cumulative, all runs)"
    if a.json:
        print(json.dumps({"scope": scope, "count": n,
                          "retrieved_utc": snap["_meta"].get("retrieved_utc")}))
        return
    print(f"{n} events in {scope}.")
    print(f"  PROVENANCE: snapshot retrieved {snap['_meta'].get('retrieved_utc')} from {snap['_meta'].get('source')}")


def cmd_list(snap, a):
    names = sorted(n for n, e in snap["events"].items()
                   if not a.catalog or e.get("catalog") == a.catalog)
    shown = names[: a.limit] if a.limit else names
    if a.json:
        print(json.dumps(shown))
        return
    scope = a.catalog or "GWTC (cumulative)"
    print(f"{len(names)} events in {scope}" + (f" (showing {len(shown)})" if len(shown) < len(names) else "") + ":")
    for n in shown:
        print(" ", n)


def cmd_catalogs(snap, a):
    counts = {}
    for e in snap["events"].values():
        counts[e.get("catalog")] = counts.get(e.get("catalog"), 0) + 1
    dois = snap["_meta"].get("catalog_dois", {})
    if a.json:
        print(json.dumps({c: {"count": counts[c], "doi": dois.get(c) or None} for c in sorted(counts)}, indent=1))
        return
    print(f"Catalogs in snapshot (retrieved {snap['_meta'].get('retrieved_utc')}):")
    for c in sorted(counts):
        print(f"  {c}: {counts[c]} events   doi={dois.get(c) or '(not exposed)'}")


def cmd_meta(snap, a):
    m = snap["_meta"]
    if a.json:
        print(json.dumps(m, indent=1))
        return
    for k in ("umbrella_catalog", "n_events", "retrieved_utc", "source"):
        print(f"  {k}: {m.get(k)}")
    print(f"  note: {m.get('note')}")


def main():
    ap = argparse.ArgumentParser(description="Query the frozen GWTC snapshot (fast, offline, cited).")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("event"); s.add_argument("id")
    s = sub.add_parser("max"); s.add_argument("param"); s.add_argument("--catalog")
    s = sub.add_parser("min"); s.add_argument("param"); s.add_argument("--catalog")
    s = sub.add_parser("count"); s.add_argument("--catalog")
    s = sub.add_parser("list"); s.add_argument("--catalog"); s.add_argument("--limit", type=int, default=0)
    sub.add_parser("catalogs")
    sub.add_parser("meta")
    a = ap.parse_args()
    snap = load()
    {
        "event": lambda: cmd_event(snap, a),
        "max": lambda: cmd_extremum(snap, a, "max"),
        "min": lambda: cmd_extremum(snap, a, "min"),
        "count": lambda: cmd_count(snap, a),
        "list": lambda: cmd_list(snap, a),
        "catalogs": lambda: cmd_catalogs(snap, a),
        "meta": lambda: cmd_meta(snap, a),
    }[a.cmd]()


if __name__ == "__main__":
    main()
