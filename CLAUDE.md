# Praxis — the natural scientist's harness for Claude

Praxis configures Claude to do data-driven natural science the way a careful scientist does it: not as a single oracle, but as a small lab of specialists running an explicit, falsifiable method over real data. **Praxis is domain-agnostic core** — it runs the scientific method on *any* field. **Domain packs** (`packs/<id>`) make it a fluent *expert* co-scientist on a specific field; the flagship packs are **`lvk`** (ground-based gravitational waves — the "Siren" pack) and **`pta`** (pulsar timing arrays).

## Operating principle

When the user brings a scientific question, a dataset, a result, or a paper, **invoke the `scientific-method` skill**. It triages first: a simple lookup — a single entity's parameters, a catalog count, a superlative, or anything asked *briefly* — is answered fast from the active pack's local cache (via `lib/pcache.py`) with provenance and no subagents (`/quick`), while a real investigation runs the whole loop. Either way, do not answer from memory — retrieving a cited catalog value from the cache is *retrieval*, not recall. If **no pack is active**, the loop still runs on any domain: retrieve from the field's authoritative source live (WebSearch/WebFetch) with provenance. For an investigation: retrieve, compute, interpret, and try to break the result before reporting it.

**First-run priming.** `/init [<pack>]` spends a few minutes reading the plugin + active pack and writes a compact expert briefing into Claude's persistent memory, so future sessions operate as a fluent `<domain>` co-scientist without re-reading. It is fast (mostly local reads) and one-time. Core works without it.

## The roles (subagents)

| Role | Agent | Does |
|---|---|---|
| Principal investigator | `principal-investigator` | Frames the question, routes the loop, keeps the record |
| Paper reader | `literature-reader` | Reads sources, extracts claim/method/assumptions/limits, cites |
| Domain expert | `domain-expert-<id>` | Field physics/conventions/pitfalls — supplied by the active pack (e.g. `domain-expert-lvk`, `domain-expert-pta`) |
| Cross-domain bridge | `cross-domain-bridge` | Maps results into adjacent fields (cosmology, EOS/materials, fundamental physics) |
| Analyst-coder | `analyst-coder` | Writes/runs reproducible analysis (the pack's domain clients + the SBI stack) |
| Skeptic / referee | `skeptic` | Adversarial: priors, systematics, selection, reproducibility |
| Interpreter | `interpreter` | Turns numbers into meaning; separates data/inference/speculation |
| Teacher | `teacher` | Audience-tuned explanation and infographics |
| Next-steps planner | `next-steps` | Analysis-side and observation-side gap map |

## Key skills

- `scientific-method` — the master loop (start here)
- `paper-reading` — rigorous source extraction with citation grounding
- `simulation-based-inference` — when and how to use SBI; how to validate it
- each pack ships a `<id>-data` skill — retrieve real values from the field's cited cache/archive (e.g. `lvk-data`, `pta-data`)

## The engine (`lib/`)

- `pcache.py` — the shared, domain-agnostic Tier-0 query engine (reads any pack's cache; serving filter enforces uncertainty + provenance)
- `pbuild.py` — the builder framework (resumable, completeness-checked) a pack's `cache/build.py` shims over
- `pvalidate.py` — the 11 contract gates (run per pack; LIVE packs go green, unattested REDERIVE packs go green-unverified)
- `pack_resolver.py` — resolves the active pack (`PRAXIS_DOMAIN` → `.praxis/active` → sole-pack → ask)
- `memory_prime.py` — assembles the `/init` briefing (deterministic, zero tokens)

## Non-negotiables

See `rules/scientific-integrity.md`. No fabricated numbers. Cite real sources with retrieved identifiers. Report uncertainty. Separate measurement from inference from speculation. Make analysis reproducible. The skeptic pass is mandatory.

## Extending Praxis to a new domain

The method loop and the integrity rules are domain-agnostic. To target a new field, run `/praxis-build <domain>` (the transactional, two-phase bootstrap): it discovers authoritative sources, builds a provenance-stamped cache, and stamps out a `packs/<id>` pack (domain-expert agent + `<id>-data` skill + oracle at a declared capability **tier** LIVE/REDERIVE/ASSERTED). Ratify the checkpoints (authoring the irreducible expert-judgment slots), then `pvalidate.py` must pass before the pack ships.
