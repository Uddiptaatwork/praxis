---
name: lvk-data
description: How to fetch real ground-based gravitational-wave data from the LVK / GWOSC public archive — event catalogs, parameter-estimation summaries, and strain. Use BEFORE answering ANY question that names a GW event (e.g. "GW190521's masses", "GW230529", any GW######_###### id), names a GWTC catalog (GWTC-1…GWTC-5.0 or the umbrella GWTC), poses a superlative about events ("largest / most massive / heaviest / closest / most distant / farthest / highest-SNR / first … in GWTC-N"), or requests an event's masses / distance / spins / SNR / redshift — even when the user did NOT type /event or /investigate. Trigger on the bare question itself, not only inside a command, so the answer comes from the cited snapshot / live API with DOI provenance rather than recalled values. Endpoints are public, no-auth, and CORS-enabled. Oracle tier LIVE.
---

# LVK / GWOSC data access (tier LIVE)

The Gravitational Wave Open Science Center hosts the public LVK data. The v2 API is public, requires no authentication, and is CORS-enabled (fetchable from a browser app or `curl` or the `gwosc` Python client). Always retrieve real values here rather than recalling them.

## Local snapshot first (the fast path) — use this before any live call

A frozen mirror of the cumulative `GWTC` catalog ships at `packs/lvk/cache/gwtc_snapshot.json` (all 391 events: catalog-level parameters with asymmetric errors, per-catalog DOIs, and a `retrieved_utc` timestamp). It is **retrieved data with provenance, not recalled values** — so it satisfies the integrity rules ("retrieve, don't recall"; "identifiers are retrieved"). Catalog data changes *only* when a new GWTC release is published, so the snapshot answers the overwhelming majority of questions with **zero network calls and in seconds** — no paging, no summarizing fetch.

For any single-event lookup, count, or superlative, call the shared core query engine `lib/pcache.py` against this pack's cache. It prints `best +upper/-lower` with units and provenance (catalog + DOI + snapshot date), through the Tier-0 serving filter (no bare numbers, no missing provenance):

```bash
C=packs/lvk/cache/gwtc_snapshot.json
python lib/pcache.py entity GW150914 --cache $C          # one event's parameters (alias: event)
python lib/pcache.py count --cache $C                    # cumulative event count
python lib/pcache.py count --catalog GWTC-5.0 --cache $C
python lib/pcache.py max total_mass_source --cache $C    # most massive (cumulative)
python lib/pcache.py max total_mass_source --catalog GWTC-5.0 --cache $C
python lib/pcache.py min luminosity_distance --cache $C  # closest
python lib/pcache.py catalogs --cache $C                 # catalogs + DOIs + counts
python lib/pcache.py meta --cache $C                     # provenance / snapshot age
```

The active pack's cache path is auto-resolvable (`PRAXIS_CACHE` / `.praxis/active`), so `--cache` can be omitted once the pack is active.

Natural-language → command:
- "how big / most massive / heaviest" → `max total_mass_source` (or `max mass_1_source`); "smallest / lightest" → `min total_mass_source`
- "closest / nearest" → `min luminosity_distance`; "farthest / most distant" → `max luminosity_distance`
- "loudest / highest-SNR" → `max network_matched_filter_snr`
- "how many … so far / in total" → `count`; "how many in GWTC-N" → `count --catalog GWTC-N`
- an event's masses / distance / spins → `event <id>` (accepts aliases like `GW150914`, `GW230529`)

Add `--json` for machine output (analyst-coder). The superlative scope rule below still holds — the helper flags cumulative-vs-release; report both or ask.

**Fall back to the LIVE v2 API only when the snapshot can't answer:**
- the event isn't in the snapshot (newer than `retrieved_utc`) — the helper exits with code 2 and prints the live URL to use;
- you need a full posterior or strain (the snapshot holds catalog-level summary params only);
- a catalog DOI is empty (`GWTC-2.1-confident`, `GWTC-3-confident`) and full per-event provenance is required — one `event-versions/<NAME>-vN` fetch fills it;
- the user explicitly asks to re-verify against the live catalog.

When you do go live, use `curl` / the `gwosc` client (deterministic) — **not** a summarizing fetch — and never request the same endpoint twice. **Refresh** the snapshot when a new GWTC release is published: `python packs/lvk/cache/build.py` (a thin shim over `lib/pbuild.py`).

## Python client (preferred for analysis)

```bash
pip install gwosc gwpy --break-system-packages
```

```python
from gwosc.datasets import event_gps
from gwosc import api
gps = event_gps("GW150914")                 # GPS time of the event
ev  = api.fetch_event_json("GW150914")       # event metadata + parameters
```

## v2 REST endpoints (for tools / browser / curl)

- Event metadata + version list:
  `https://gwosc.org/api/v2/events/<NAME>`  → `versions[].detail_url`
- Event version detail with PE parameters:
  `https://gwosc.org/api/v2/event-versions/<NAME>-v<N>`  → `parameters[]`
- Catalog detail (name, description, doi, events_url):
  `https://gwosc.org/api/v2/catalogs/<CATALOG>`
- Catalog event list (with default params inline):
  `https://gwosc.org/api/v2/catalogs/<CATALOG>/events?include-default-parameters=true`
- Strain file links:
  `https://gwosc.org/api/v2/.../strain-files`

`<NAME>` accepts aliases (`GW230529`) or full ids (`GW230529_181500`). If a short name 404s, use the full id — `GW231123` returns `{"detail": "No Event matches the given query."}` but `GW231123_135430` resolves (likewise `GW190521_030229`). The v2 API is paginated and throttled — page rather than hammering.

## Pagination & inline-parameter mechanics

- In catalog event listings, inline parameters live under the key **`default_parameters`** (NOT `parameters` — that key is for event-version detail). Each list row also carries `name`, `shortName`, `gps`, `version`, `catalog`, `detectors`, `detail_url`.
- `results_per_page` is effectively capped at **20**: requesting a larger `page-size` still returns 20 rows (and an oversized request can transiently 502). Do not rely on a single fat page — **follow the `next` link** until it is null, and retry on 502.
- The list envelope exposes `results_count`, `num_pages`, `page_number`, `next`, `previous`, `results[]`. To find a superlative you must page the whole catalog and reduce client-side.

## Parameter fields

Each parameter carries `name`, `best`, `upper_error`, `lower_error`, `unit`, `decimal_places`, and upper/lower-limit flags. Common names: `chirp_mass_source`, `total_mass_source`, `mass_1_source`, `mass_2_source`, `chi_eff`, `final_mass_source`, `final_spin`, `luminosity_distance`, `redshift`, `network_matched_filter_snr`. **Always report `best` with its asymmetric errors** — never the point estimate alone. Note source-frame vs detector-frame mass.

## Catalog semantics

The numbered GWTC catalogs on GWOSC are **per-observing-run segments, not cumulative**. The umbrella catalog literally named `GWTC` is the cumulative current-best set (391 events at last check); every numbered release is a slice of one run:

| Catalog | Run | Notes |
|---|---|---|
| `GWTC-1`, `GWTC-2`, `GWTC-2.1` | O1–O3a | |
| `GWTC-3` | O3b | |
| `GWTC-4.0`, `GWTC-4.1` | O4a | |
| `GWTC-5.0` | O4b | |
| `GWTC` (umbrella) | all runs | cumulative current-best view |

Consequence: the largest-total-mass BBH overall, **GW231123_135430**, lives under **GWTC-4.1 (O4a)** and is **NOT in GWTC-5.0**. The largest in GWTC-5.0 (O4b) is **GW241230_233618**. A "largest in GWTC-5.0" answer is not the largest overall.

Each catalog detail (`/api/v2/catalogs/<CATALOG>`) returns `{name, description, doi, events_url}`. Numbered releases carry a real `doi` — e.g. GWTC-5.0 → `https://doi.org/10.7935/bk00-6a89`, GWTC-4.1 → `https://doi.org/10.7935/6xqf-ba54`. The umbrella `GWTC` has `doi: null` (cite the relevant numbered release + the event-version DOI instead).

## Superlative rule (hard)

Any superlative query scoped to a named release — "largest / most massive / heaviest / first / closest / farthest / highest-SNR **in GWTC-N**" — is **SCOPE-AMBIGUOUS**, because GWTC-N is one run, not the whole catalog. You MUST:

1. Query the umbrella **`GWTC`** catalog for the global answer, AND the named release for the in-release answer (page both fully via `next`, reduce client-side).
2. **Report BOTH** — the cumulative-largest and the release-largest — or ask the user which scope they mean.
3. Never answer a superlative from a single numbered-release subset alone.

Worked example (the right behavior): asked "largest BBH in GWTC-5", report that within GWTC-5.0 it is GW241230_233618 (O4b), **but** the cumulative-largest in the full `GWTC` is GW231123_135430 (GWTC-4.1 / O4a) — and surface that the question conflated a run-slice with the catalog.

## Provenance rule

Log event name, version, catalog, retrieval source, and **DOI** for anything you compute. Capture both the event-version DOI and the catalog DOI (`/api/v2/catalogs/<CATALOG>` → `doi`), and report the actual DOI with any number — upgrade weak provenance like "GWOSC API v2" to e.g. `GWTC-5.0, https://doi.org/10.7935/bk00-6a89`. A number without provenance is not usable in an investigation. Catalog snapshots are also archived on Zenodo if a frozen reference is needed.
