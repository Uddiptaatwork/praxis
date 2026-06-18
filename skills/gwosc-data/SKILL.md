---
name: gwosc-data
description: How to fetch real gravitational-wave data from the LVK / GWOSC public archive — event catalogs, parameter-estimation summaries, and strain. Use whenever an investigation needs actual numbers for a GW event instead of recalled values. Endpoints are public, no-auth, and CORS-enabled.
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
- Catalog event list (with default params inline):
  `https://gwosc.org/api/v2/catalogs/<CATALOG>/events?include-default-parameters=true`
- Strain file links:
  `https://gwosc.org/api/v2/.../strain-files`

`<NAME>` accepts aliases (`GW230529`) or full ids (`GW230529_181500`). If a short name 404s, use the full id (e.g. `GW190521_030229`). The v2 API is paginated and throttled — page rather than hammering.

## Parameter fields

Each parameter carries `name`, `best`, `upper_error`, `lower_error`, `unit`, `decimal_places`, and upper/lower-limit flags. Common names: `chirp_mass_source`, `total_mass_source`, `mass_1_source`, `mass_2_source`, `chi_eff`, `final_mass_source`, `final_spin`, `luminosity_distance`, `redshift`, `network_matched_filter_snr`. **Always report `best` with its asymmetric errors** — never the point estimate alone. Note source-frame vs detector-frame mass.

## Provenance rule

Log event name, version, catalog, and retrieval source for anything you compute. A number without provenance is not usable in an investigation. Catalog snapshots are also archived on Zenodo if a frozen reference is needed.
