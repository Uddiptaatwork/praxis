#!/usr/bin/env python3
"""pbuild -- the domain-agnostic Praxis cache builder framework (stdlib only).

A pack's cache/build.py is a THIN shim: it supplies endpoints/DOIs/param names
and calls pbuild.build(...). This framework owns the reusable machinery:
paging with retry/backoff, per-page checkpointing (resumability), DOI resolution,
superlative precompute, _meta stamping, and the completeness invariant
(len(entities) == results_count_reported). It writes a cache that pcache.py and
pvalidate.py both accept, for any field.

Two build modes:
  * LIVE-paged   -- pass events_url; the framework pages a REST catalog API,
                    resuming from <out>.staging on a re-run (a 502 at page 12
                    of 20 resumes, it does not restart).
  * transcribed  -- pass entities={...}; the framework skips the network and
                    just stamps/records/writes (REDERIVE packs whose values are
                    transcribed deterministically from a published table).
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

UA = {"User-Agent": "praxis-pbuild/1.0"}
DEFAULT_FIELDS = ("best", "upper_error", "lower_error", "unit",
                  "is_upper_limit", "is_lower_limit", "is_exact", "decimal_places", "note")


def get(url, tries=5):
    """GET JSON with retry/backoff. Public science APIs 502 under load."""
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


def params_to_dict(plist, fields=DEFAULT_FIELDS):
    out = {}
    for p in plist or []:
        name = p.get("name")
        if name:
            out[name] = {k: p.get(k) for k in fields if p.get(k) is not None}
    return out


def _staging(out):
    return out + ".staging"


def page_catalog(events_url, out, entity_from_row, param_fields, resume=True, polite=0.3):
    """Page a REST catalog, checkpointing to <out>.staging after each page."""
    entities, start_url, expected = {}, events_url, None
    stg = _staging(out)
    if resume and os.path.exists(stg):
        saved = json.load(open(stg))
        entities = saved.get("entities", {})
        start_url = saved.get("next") or events_url
        expected = saved.get("expected")
        print(f"resuming from {stg}: {len(entities)} entities, next={start_url}")
    url, page = start_url, 0
    while url:
        page += 1
        d = get(url)
        if expected is None:
            expected = d.get("results_count")
            print(f"catalog: {expected} entities across {d.get('num_pages')} pages")
        for row in d.get("results", []):
            name, ent = entity_from_row(row, param_fields)
            if name:
                entities[name] = ent
        url = d.get("next")
        print(f"  page {page}: total {len(entities)}")
        with open(stg, "w") as f:
            json.dump({"entities": entities, "next": url, "expected": expected}, f)
        if url:
            time.sleep(polite)
    return entities, expected


def resolve_dois(keys, doi_url, polite=0.2):
    """Resolve a DOI per key; empty/None becomes null + a doi_status flag."""
    dois, status = {}, {}
    for k in keys:
        try:
            v = get(doi_url(k)).get("doi")
        except SystemExit:
            v = None
        if v and isinstance(v, str) and v.strip():
            dois[k] = v.strip()
        else:
            dois[k] = None
            status[k] = "not-exposed"
        time.sleep(polite)
    return dois, status


def precompute_records(entities, record_params):
    records = {}
    for pname in record_params:
        vals = [(n, e["parameters"][pname]["best"]) for n, e in entities.items()
                if pname in (e.get("parameters") or {})
                and isinstance(e["parameters"][pname].get("best"), (int, float))
                and not e.get("context_only")]
        if not vals:
            continue
        hi, lo = max(vals, key=lambda t: t[1]), min(vals, key=lambda t: t[1])
        records[pname] = {
            "max": {"entity": hi[0], "best": hi[1], "catalog": entities[hi[0]].get("catalog")},
            "min": {"entity": lo[0], "best": lo[1], "catalog": entities[lo[0]].get("catalog")},
            "n_with_value": len(vals),
        }
    return records


def build(*, domain, entity_kind, cumulative_scope, record_params, out, builder_version,
          source, supersede_rule="replace", display_order=None, note="",
          events_url=None, entity_from_row=None, param_fields=DEFAULT_FIELDS,
          doi_keys=None, doi_url=None, dois=None, doi_status=None,
          entities=None, results_count_reported=None, resume=True):
    """Assemble + write a schema-conforming snapshot. Provide EITHER events_url
    (+entity_from_row) for a live paged build, OR entities=... for a transcribed one."""
    if entities is None:
        if not (events_url and entity_from_row):
            raise SystemExit("build(): need events_url+entity_from_row, or entities=...")
        entities, expected = page_catalog(events_url, out, entity_from_row, param_fields, resume=resume)
    else:
        expected = results_count_reported if results_count_reported is not None else len(entities)

    if dois is None and doi_keys and doi_url:
        dois, doi_status = resolve_dois(doi_keys, doi_url)
    dois = dois or {}
    doi_status = doi_status or {}

    records = precompute_records(entities, record_params)
    snapshot = {
        "_meta": {
            "praxis_contract": "1.0",
            "domain": domain,
            "entity_kind": entity_kind,
            "cumulative_scope": cumulative_scope,
            "supersede_rule": supersede_rule,
            "source": source,
            "retrieved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "builder_version": builder_version,
            "n_entities": len(entities),
            "results_count_reported": expected,
            "dois": dois,
            "doi_status": doi_status,
            "record_params": record_params,
            "display_order": display_order or record_params,
            "note": note,
        },
        "records": records,
        "entities": entities,
    }
    if expected is not None and expected != len(entities):
        print(f"WARNING: completeness -- len(entities)={len(entities)} != reported {expected}. "
              f"Do NOT ship; resume the build.", file=sys.stderr)
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with open(out, "w") as f:
        json.dump(snapshot, f, indent=1, sort_keys=True)
    stg = _staging(out)
    if os.path.exists(stg):
        os.remove(stg)
    print(f"wrote {out}: {len(entities)} entities (reported {expected}), "
          f"{sum(1 for v in dois.values() if v)} DOIs resolved")
    return snapshot
