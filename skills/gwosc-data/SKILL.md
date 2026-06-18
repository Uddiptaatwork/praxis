---
name: gwosc-data
description: How to fetch real gravitational-wave data from the LVK / GWOSC public archive — event catalogs, parameter-estimation summaries, and strain. Use BEFORE answering ANY question that names a GW event (e.g. "GW190521's masses", "GW230529", any GW######_###### id), names a GWTC catalog (GWTC-1…GWTC-5.0 or the umbrella GWTC), poses a superlative about events ("largest / most massive / heaviest / closest / most distant / farthest / highest-SNR / first … in GWTC-N"), or requests an event's masses / distance / spins / SNR / redshift — even when the user did NOT type /event or /investigate. Trigger on the bare question itself, not only inside a command, so the answer comes from the live API with DOI provenance rather than recalled values. Endpoints are public, no-auth, and CORS-enabled.
---

# GWOSC data access

The Gravitational Wave Open Science Center hosts the public LVK data. The v2 API is public, requires no authentication, and is CORS-enabled (fetchable from a browser app or `curl` or the `gwosc` Python client). Always retrieve real values here rather than recalling them.

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

Consequence: the largest-total-mass BBH overall, **GW231123_135430** (M_total ~236 M☉), lives under **GWTC-4.1 (O4a)** and is **NOT in GWTC-5.0**. The largest in GWTC-5.0 (O4b) is **GW241230_233618** (~116 M☉). A "largest in GWTC-5.0" answer is not the largest overall.

Each catalog detail (`/api/v2/catalogs/<CATALOG>`) returns `{name, description, doi, events_url}`. Numbered releases carry a real `doi` — e.g. GWTC-5.0 → `https://doi.org/10.7935/bk00-6a89`, GWTC-4.1 → `https://doi.org/10.7935/6xqf-ba54`. The umbrella `GWTC` has `doi: null` (cite the relevant numbered release + the event-version DOI instead).

## Superlative rule (hard)

Any superlative query scoped to a named release — "largest / most massive / heaviest / first / closest / farthest / highest-SNR **in GWTC-N**" — is **SCOPE-AMBIGUOUS**, because GWTC-N is one run, not the whole catalog. You MUST:

1. Query the umbrella **`GWTC`** catalog for the global answer, AND the named release for the in-release answer (page both fully via `next`, reduce client-side).
2. **Report BOTH** — the cumulative-largest and the release-largest — or ask the user which scope they mean.
3. Never answer a superlative from a single numbered-release subset alone.

Worked example (the right behavior): asked "largest BBH in GWTC-5", report that within GWTC-5.0 it is GW241230_233618 (~116 M☉, O4b), **but** the cumulative-largest in the full `GWTC` is GW231123_135430 (~236 M☉, GWTC-4.1 / O4a) — and surface that the question conflated a run-slice with the catalog.

## Provenance rule

Log event name, version, catalog, retrieval source, and **DOI** for anything you compute. Capture both the event-version DOI and the catalog DOI (`/api/v2/catalogs/<CATALOG>` → `doi`), and report the actual DOI with any number — upgrade weak provenance like "GWOSC API v2" to e.g. `GWTC-5.0, https://doi.org/10.7935/bk00-6a89`. A number without provenance is not usable in an investigation. Catalog snapshots are also archived on Zenodo if a frozen reference is needed.
