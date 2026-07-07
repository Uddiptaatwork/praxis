#!/usr/bin/env python3
"""pcache -- the domain-agnostic Praxis cache query engine (Tier-0 fast path).

Reads ANY schema-conforming pack snapshot (`entities`/`records`/`_meta`) and
answers single-entity lookups, counts, and superlatives instantly, offline, with
provenance -- ZERO LLM tokens, ZERO network (unless a LIVE staleness probe is
explicitly requested). This is the single query path for every pack; packs ship
their cache JSON and NO query code of their own.

  python lib/pcache.py entity GW150914 --cache packs/lvk/cache/gwtc_snapshot.json
  python lib/pcache.py entity NANOGrav-15yr --cache packs/pta/cache/pta_snapshot.json
  python lib/pcache.py max total_mass_source --catalog GWTC-4.1
  python lib/pcache.py min luminosity_distance
  python lib/pcache.py count [--catalog GWTC-4.1]
  python lib/pcache.py list [--catalog X] [--limit N]
  python lib/pcache.py catalogs | meta

Cache path resolution: --cache PATH  >  $PRAXIS_CACHE  >  pack_resolver (active pack).

Two mechanically-enforced serving guarantees (this file controls the bytes):
  * Tier-0 serving filter: a numeric value is NEVER emitted clean without either
    an asymmetric error, or an explicit is_exact / is_upper_limit / is_lower_limit
    / bare_reason flag -- otherwise it prints with an [UNCERTAINTY MISSING] marker.
  * Provenance: no value is emitted without a composed provenance string.

Staleness (opt-in, honors the pack's oracle tier):
  --max-age-days N          REDERIVE/ASSERTED hard-expiry: past it, downgrade to EXPIRED.
  --probe-url URL [--probe-count-field results_count]
                            LIVE: fetch, compare to results_count_reported; on drift,
                            downgrade values and make superlatives exit non-zero.

Exit code 2 == "not in this cache" (caller may fall back to live for a LIVE pack;
for REDERIVE/ASSERTED it is an honest absence, never a recall).
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone

_HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- cache access
def _resolve_cache_path(cli_path):
    if cli_path:
        return cli_path
    env = os.environ.get("PRAXIS_CACHE")
    if env:
        return env
    try:
        sys.path.insert(0, _HERE)
        import pack_resolver  # type: ignore
        pid = pack_resolver.active_domain()
        if pid:
            return pack_resolver.cache_path(pid)
    except Exception:
        pass
    return None


def load(path):
    if not path or not os.path.exists(path):
        sys.exit(f"cache missing: {path!r}. Pass --cache PATH or set PRAXIS_CACHE, "
                 f"or activate a pack (see /init).")
    with open(path) as f:
        snap = json.load(f)
    # entities is canonical; `events` is the legacy GW key.
    if "entities" not in snap and "events" in snap:
        snap["entities"] = snap["events"]
    return snap


def _meta(snap, key, *aliases, default=None):
    m = snap.get("_meta", {})
    for k in (key, *aliases):
        if k in m and m[k] is not None:
            return m[k]
    return default


def cumulative_scope(snap):
    return _meta(snap, "cumulative_scope", "umbrella_catalog")


def display_order(snap):
    return _meta(snap, "display_order", "record_params", default=[]) or []


def dois(snap):
    return _meta(snap, "dois", "catalog_dois", default={}) or {}


# ---------------------------------------------------------------- provenance
def doi_for(snap, ent, ent_name):
    """Prefer an entity-level release DOI, else the _meta.dois entry keyed by the
    entity's catalog or its own name. Empty string is treated as absent."""
    d = ent.get("release_doi")
    if not d:
        table = dois(snap)
        d = table.get(ent.get("catalog")) or table.get(ent_name)
    return d or None


def _doi_status(snap, key):
    return (_meta(snap, "doi_status", default={}) or {}).get(key)


def provenance(snap, ent, ent_name):
    doi = doi_for(snap, ent, ent_name)
    catalog = ent.get("catalog") or ent_name
    if doi:
        cite = f"{catalog}, {doi}"
    else:
        status = _doi_status(snap, ent.get("catalog")) or _doi_status(snap, ent_name)
        why = f"DOI {status}" if status else "DOI not in cache -- live/per-entity fetch for identifier"
        cite = f"{catalog} ({why})"
    return f"{cite}; snapshot retrieved {_meta(snap, 'retrieved_utc')}"


# ---------------------------------------------------------------- staleness
def _age_days(snap):
    ru = _meta(snap, "retrieved_utc")
    if not ru:
        return None
    try:
        t = datetime.strptime(ru, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - t).total_seconds() / 86400.0
    except ValueError:
        return None


def staleness_banner(snap, a):
    """Return (banner_or_None, superlative_blocked_bool)."""
    # hard-expiry (REDERIVE / ASSERTED)
    if a.max_age_days:
        age = _age_days(snap)
        if age is not None and age > a.max_age_days:
            return (f"EXPIRED CACHE: retrieved {_meta(snap,'retrieved_utc')} "
                    f"({age:.0f}d > {a.max_age_days}d hard-expiry) -- re-verify, do not report as authoritative.",
                    True)
    # live probe (LIVE)
    if a.probe_url:
        try:
            import urllib.request
            req = urllib.request.Request(a.probe_url, headers={"User-Agent": "praxis-pcache/1.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                live = json.load(r).get(a.probe_count_field)
            reported = _meta(snap, "results_count_reported")
            if live is not None and reported is not None and int(live) != int(reported):
                return (f"CACHED {_meta(snap,'retrieved_utc')}: live source reports {live} vs "
                        f"cached {reported} -- a newer release may exist; re-verify.", True)
        except Exception as e:
            return (f"NOTE: live staleness probe failed ({e}); serving cache as-of "
                    f"{_meta(snap,'retrieved_utc')}.", False)
    return (None, False)


# ---------------------------------------------------------------- Tier-0 filter
def fmt_param(name, p):
    """The serving filter. A numeric value never appears clean without an
    uncertainty or an explicit exactness/limit/bare flag."""
    best = p.get("best")
    if best is None:
        return f"  {name}: (no value in cache)"
    unit = (" " + p["unit"]).rstrip() if p.get("unit") else ""
    up, lo = p.get("upper_error"), p.get("lower_error")
    if p.get("is_upper_limit"):
        body = f"< {best}{unit}"
    elif p.get("is_lower_limit"):
        body = f"> {best}{unit}"
    elif p.get("is_exact"):
        body = f"{best}{unit} (exact)"
    elif up is not None and lo is not None:
        body = f"{best} +{abs(up)}/-{abs(lo)}{unit}"
    elif isinstance(best, (int, float)):
        reason = p.get("bare_reason", "no CI in cache -- live fetch for full posterior")
        body = f"{best}{unit}  [UNCERTAINTY MISSING: {reason}]"
    else:
        body = f"{best}{unit}"
    out = f"  {name} = {body}"
    if p.get("note"):
        out += f"\n      note: {p['note']}"
    return out


# ---------------------------------------------------------------- resolve
def resolve(snap, q):
    ents = snap["entities"]
    if q in ents:
        return q, ents[q]
    ql = q.lower()
    cands = []
    for name, data in ents.items():
        if name.lower() == ql or (data.get("shortName") or "").lower() == ql:
            return name, data
        if ql in [str(x).lower() for x in (data.get("id_aliases") or [])]:
            return name, data
        if name.lower().startswith(ql + "_") or name.lower().startswith(ql):
            cands.append(name)
    if len(cands) == 1:
        return cands[0], ents[cands[0]]
    if len(cands) > 1:
        sys.exit(f"'{q}' is ambiguous: {', '.join(sorted(cands))}\nUse the full id.")
    print(f"NOT IN CACHE: '{q}' is absent from this snapshot "
          f"(retrieved {_meta(snap,'retrieved_utc')}).", file=sys.stderr)
    sys.exit(2)


# ---------------------------------------------------------------- commands
def _banner_line(snap, a):
    banner, blocked = staleness_banner(snap, a)
    if banner:
        print(f"  [{banner}]")
    return blocked


def cmd_entity(snap, a):
    name, data = resolve(snap, a.id)
    prov = provenance(snap, data, name)
    if a.json:
        print(json.dumps({"name": name, **data, "provenance": prov}, indent=1))
        return
    hdr = name
    extra = []
    if data.get("shortName"):
        extra.append(f"shortName {data['shortName']}")
    if data.get("version") is not None:
        extra.append(f"version {data['version']}")
    if extra:
        hdr += "  (" + ", ".join(extra) + ")"
    print(hdr)
    if data.get("catalog") or data.get("detectors"):
        print(f"  catalog: {data.get('catalog')}   detectors: {data.get('detectors')}")
    _banner_line(snap, a)
    params = data.get("parameters", {})
    print("  --- parameters (best +upper/-lower) ---")
    seen = set()
    for k in display_order(snap):
        if k in params:
            print(fmt_param(k, params[k]))
            seen.add(k)
    for k in sorted(params):
        if k not in seen:
            print(fmt_param(k, params[k]))
    if data.get("context_note"):
        print(f"  CONTEXT: {data['context_note']}")
    print(f"  PROVENANCE: {prov}")


def _numeric(snap, param, catalog=None):
    out = []
    for n, e in snap["entities"].items():
        if catalog and e.get("catalog") != catalog:
            continue
        if e.get("context_only"):
            continue  # never let context-only entities win a superlative
        p = e.get("parameters", {}).get(param)
        if p and isinstance(p.get("best"), (int, float)):
            out.append((n, e, p))
    return out


def cmd_extremum(snap, a, which):
    blocked = _banner_line(snap, a)
    if blocked:
        print("  superlative SUPPRESSED while cache is stale/expired -- re-verify before quoting.",
              file=sys.stderr)
        sys.exit(3)
    rows = _numeric(snap, a.param, a.catalog)
    if not rows:
        sys.exit(f"no entities carry numeric '{a.param}'"
                 + (f" in {a.catalog}" if a.catalog else "") + " in this cache.")
    pick = (max if which == "max" else min)(rows, key=lambda t: t[2]["best"])
    n, e, p = pick
    scope = a.catalog or cumulative_scope(snap)
    prov = provenance(snap, e, n)
    if a.json:
        print(json.dumps({"which": which, "param": a.param, "scope": scope,
                          "entity": n, "value": p, "provenance": prov}, indent=1))
        return
    print(f"{which.upper()} {a.param} in {scope} ({len(rows)} entities have this param):")
    print(f"  {n}: {fmt_param(a.param, p).strip()}")
    print(f"  PROVENANCE: {prov}")
    if not a.catalog:
        print("  NOTE: cumulative-scope answer. A per-release answer may differ -- pass --catalog.")


def cmd_count(snap, a):
    if a.catalog:
        n = sum(1 for e in snap["entities"].values() if e.get("catalog") == a.catalog)
        scope = a.catalog
    else:
        n = _meta(snap, "n_events", "n_entities", default=len(snap["entities"]))
        scope = f"{cumulative_scope(snap)} (cumulative)"
    if a.json:
        print(json.dumps({"scope": scope, "count": n, "retrieved_utc": _meta(snap, "retrieved_utc")}))
        return
    print(f"{n} entities in {scope}.")
    print(f"  PROVENANCE: snapshot retrieved {_meta(snap,'retrieved_utc')} from {_meta(snap,'source')}")


def cmd_list(snap, a):
    names = sorted(n for n, e in snap["entities"].items()
                   if not a.catalog or e.get("catalog") == a.catalog)
    shown = names[: a.limit] if a.limit else names
    if a.json:
        print(json.dumps(shown))
        return
    scope = a.catalog or f"{cumulative_scope(snap)} (cumulative)"
    tail = f" (showing {len(shown)})" if len(shown) < len(names) else ""
    print(f"{len(names)} entities in {scope}{tail}:")
    for n in shown:
        flag = "  [CONTEXT-ONLY]" if snap["entities"][n].get("context_only") else ""
        print(f"  {n}{flag}")


def cmd_catalogs(snap, a):
    counts = {}
    for e in snap["entities"].values():
        c = e.get("catalog") or e.get("release_tag") or "(uncatalogued)"
        counts[c] = counts.get(c, 0) + 1
    table = dois(snap)
    if a.json:
        print(json.dumps({c: {"count": counts[c], "doi": table.get(c) or None}
                          for c in sorted(counts)}, indent=1))
        return
    print(f"Catalogs/releases in cache (retrieved {_meta(snap,'retrieved_utc')}):")
    for c in sorted(counts):
        d = table.get(c) or _doi_status(snap, c) or "(not exposed)"
        print(f"  {c}: {counts[c]} entities   doi={d}")


def cmd_meta(snap, a):
    m = snap.get("_meta", {})
    if a.json:
        print(json.dumps(m, indent=1))
        return
    for k in ("domain", "entity_kind", "cumulative_scope", "umbrella_catalog",
              "n_events", "n_entities", "retrieved_utc", "results_count_reported", "source"):
        if k in m:
            print(f"  {k}: {m.get(k)}")
    banner, _ = staleness_banner(snap, a)
    if banner:
        print(f"  STALENESS: {banner}")
    if m.get("note"):
        print(f"  note: {m.get('note')}")


def main():
    # Shared options live on a parent so they work either before OR after the
    # subcommand (argparse would otherwise reject them post-subcommand).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true")
    common.add_argument("--cache", help="path to the pack snapshot json")
    common.add_argument("--max-age-days", type=float, default=0.0, help="REDERIVE/ASSERTED hard-expiry")
    common.add_argument("--probe-url", help="LIVE staleness probe endpoint")
    common.add_argument("--probe-count-field", default="results_count")

    ap = argparse.ArgumentParser(
        description="Query any Praxis pack cache (fast, offline, cited).", parents=[common])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("entity", parents=[common]); s.add_argument("id")
    s = sub.add_parser("event", parents=[common]); s.add_argument("id")  # GW alias
    s = sub.add_parser("max", parents=[common]); s.add_argument("param"); s.add_argument("--catalog")
    s = sub.add_parser("min", parents=[common]); s.add_argument("param"); s.add_argument("--catalog")
    s = sub.add_parser("count", parents=[common]); s.add_argument("--catalog")
    s = sub.add_parser("list", parents=[common]); s.add_argument("--catalog"); s.add_argument("--limit", type=int, default=0)
    sub.add_parser("catalogs", parents=[common])
    sub.add_parser("meta", parents=[common])
    a = ap.parse_args()
    snap = load(_resolve_cache_path(a.cache))
    {
        "entity": lambda: cmd_entity(snap, a),
        "event": lambda: cmd_entity(snap, a),
        "max": lambda: cmd_extremum(snap, a, "max"),
        "min": lambda: cmd_extremum(snap, a, "min"),
        "count": lambda: cmd_count(snap, a),
        "list": lambda: cmd_list(snap, a),
        "catalogs": lambda: cmd_catalogs(snap, a),
        "meta": lambda: cmd_meta(snap, a),
    }[a.cmd]()


if __name__ == "__main__":
    main()
