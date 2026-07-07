---
name: praxis-packs
description: List installed Praxis domain packs with their oracle tier, cache age/expiry, and on-disk size, so freshness, integrity strength, and growth are visible.
---

List the installed Praxis packs and their health.

1. For each id from `python lib/pack_resolver.py list`, run `python lib/pcache.py meta --cache packs/<id>/cache/<cache>.json` (path from `python lib/pack_resolver.py cache <id>`) and read `packs/<id>/pack.json`.
2. Print a table: **id · title · oracle tier · cache retrieved_utc (age) · results_count · on-disk cache size · attestation (verified / community-unverified)**.
3. Flag staleness: LIVE packs can be probed against `sources.latest_release_probe`; REDERIVE/ASSERTED packs show age vs `sota.refresh.hard_expiry`. Mark any pack past hard-expiry as **EXPIRED — re-verify / refresh**.
4. Mark the currently active pack (`python lib/pack_resolver.py active`).
