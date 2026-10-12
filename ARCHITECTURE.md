# Praxis 2.0 — Unified Architecture

*A typed plugin ecosystem for data-driven natural science: a domain-agnostic `praxis-core` plus N domain packs, with mechanically-enforced **cache** integrity, an explicit **oracle capability tier** that gates which integrity claims a pack may advertise, convention-driven runtime resolution, and a single expensive — and transactional — bootstrap.*

---

## 1. Overview, the core/pack thesis, and the honest scope of "with teeth"

Today's plugin fuses three things with three different lifecycles: the **method** (loop, roles, integrity rules — almost never changes), the **GW domain knowledge** (Siren — changes per GWTC release), and the **eval harness**. The fusion is shallow and provable in the code:

- `skills/scientific-method/SKILL.md:44` hard-references `gwosc-data` (the one hard GW rule).
- `agents/principal-investigator.md:10,16` hard-reference `domain-expert-gw` / `query_snapshot.py`.
- `rules/scientific-integrity.md` rule 9 names the GWOSC `doi`.
- `commands/quick.md`, `commands/event.md`, and `eval/score.py` (live GWOSC diff) bind the rest.

Eight of nine agents are *nominally* domain-agnostic; six of those eight still carry GW tokens in prose (verified: `principal-investigator`, `analyst-coder`, `literature-reader`, `interpreter`, `cross-domain-bridge`, `next-steps` all grep-hit `gw/gwosc/chirp/bilby/detector`). The snapshot (`_meta`/`events`/`records`, 391 events) and `query_snapshot.py` (exit-2 fallback, `provenance()`, `COMMON_ORDER`) are largely reusable but not literally lift-and-shift (see §8).

### The thesis

The hard split is governed by a **strict typed contract** because the panel's hardest constraint — preserving integrity (no-fabrication / provenance / retrieve-don't-recall) for **cached** knowledge — is the one thing prose conventions cannot guarantee. We make the **cache** invariants **mechanically enforced** (`pvalidate.py` gates + a deterministic Tier-0 serving filter) rather than merely documented. We bolt on **convention-over-configuration runtime resolution** so "install one pack, zero config" is free, and we keep all query code in core so a pack ships *zero* query logic.

### The honest scope: where "mechanically enforced" is true, and where it is not

Two corrections to an over-broad "mechanically enforced integrity" claim are baked into this architecture from the start, because the reference data and the reference eval already disprove the naive version:

1. **The gates validate the cache artifact, not the answer.** A green `pvalidate.py` run certifies the cache is well-formed; it says nothing about whether the *next generated answer* used the cache, carried the uncertainty, or cited the DOI. This repo's own flagship eval proves it: the most-tuned instance (GW) scores `provenance_rate = 0.889` (8/9 runs in `eval/aggregate.json`), with one B run returning `has_gwosc_doi: false`. So answer-layer integrity is ~89%, prompt-driven, and stochastic — exactly the "prose convention" the thesis says is insufficient. We therefore split enforcement into two points and never conflate them (§6): **mechanically enforced for cache integrity and Tier-0 serving; eval-gated for Tier-1 generation.**

2. **"No live API" is not a localized weakness — it removes the ground-truth oracle, the live-fallback safety net, and the grading loop simultaneously.** A no-API domain cannot diff its cache against an independent source (the grader checks the cache against itself — circular, catches zero transcription errors), has nowhere for `query_snapshot.py`'s exit-2 fallback to land (a cache miss becomes a refusal or a recall — the exact failure the architecture claims to prevent), and for most of science (most of biology, chemistry, condensed matter) the cache is LLM-transcribed from PDFs/tables at init with no oracle that can ever catch the error. We do not paper over this with a single "honestly weaker oracle" footnote. We make `oracle.kind` a **hard capability tier** (§3.3) that gates which integrity claims a pack may advertise, and we state the generalization scope out loud: **Praxis-with-teeth covers tier-LIVE and tier-REDERIVE fields; tier-ASSERTED fields get the method loop but NOT the mechanical integrity guarantee, and must say so on every served value.**

```
praxis-core/          one plugin, depends on nothing.
                      The method + 8 generic roles + integrity rules
                      + the cache ENGINE (query/build/validate) + eval methodology.
                      Ships ZERO domain knowledge, ZERO cached data.

praxis-<domain>/      N plugins (praxis-gw, praxis-pta, ...), each depends on praxis-core.
                      A pack.json manifest (declaring its oracle TIER + corpus license)
                      + one domain-expert agent + one data skill + one provenance-stamped
                      cache + a refresh builder + a domain eval suite + an oracle adapter
                      + a cited SOTA index.

/praxis-init <domain> a core command. The ONE expensive step, run transactionally.
                      A headless discover/build/validate phase + an interactive
                      ratification phase. Emits a validated pack to disk — atomically.
```

**The boundary rule, stated once:** *if removing GW would leave the file working for PTA tomorrow, it is core; if the file knows what a chirp mass or a GWTC catalog is, it is a pack.* The cache engine is core because it operates on the **schema**, not on physics. Core refers to the active domain through exactly **two indirections**: a name (`${PRAXIS_DOMAIN}`, resolved by a convention resolver) and a generic reader (`lib/pcache.py`). Nothing else.

**Why core ships no data:** the invariant "cached knowledge must be distinguishable from live retrieval by provenance" is only enforceable if core literally *cannot* answer a domain question without a pack. A core-shipped snapshot would let it answer from a stale, ownerless blob. Core ships the *machinery*; packs ship the *provenance-stamped knowledge* — under a declared oracle tier.

---

## 2. praxis-core contents

```
praxis-core/
  .claude-plugin/plugin.json            # name: "praxis-core", version, praxis_contract: "1.0"
  CLAUDE.md                             # operating principle, role table, extension recipe
  rules/scientific-integrity.md         # the 10 rules — DE-GW-ified (rule 9 generalized)
  skills/
    scientific-method/SKILL.md          # the loop + triage — line-44 GW rule -> domain hook
    paper-reading/SKILL.md              # de-GW'd (worked examples neutralized)
    simulation-based-inference/SKILL.md # de-GW'd
    praxis-cache/SKILL.md               # NEW: how ANY pack's cache is shaped + queried
  agents/                               # the 8 generic roles (no domain-expert here)
    principal-investigator.md  literature-reader.md  analyst-coder.md
    skeptic.md  interpreter.md  cross-domain-bridge.md  teacher.md  next-steps.md
  commands/
    investigate.md  quick.md            # generic: route to the ACTIVE pack, not gw
    praxis-init.md                      # the bootstrap (transactional, two-phase) (§4)
    praxis-use.md                       # switch the active domain (writes .praxis/active)
    praxis-packs.md                     # list packs + cache staleness + on-disk size
    praxis-refresh.md                   # re-run a pack's builder + re-validate (§5)
  lib/                                  # the domain-agnostic cache ENGINE (stdlib only)
    pcache.py                           # generic query CLI + Tier-0 serving filter (§6)
    pbuild.py                           # generic builder framework (resumable, completeness)
    pvalidate.py                        # validates pack.json + cache against the contract
    pack_resolver.py                    # ~30-line convention resolver (§2.2)
    schema/pack.schema.json             # JSON Schema for pack.json (incl. oracle.tier)
    schema/cache.schema.json            # JSON Schema for the cache artifact
    schema/sota.schema.json             # JSON Schema for the cited SOTA index
    templates/                          # what /praxis-init stamps out (§4)
      domain-expert.md.tmpl  data-skill.SKILL.md.tmpl
      build.py.tmpl  oracle.py.tmpl  suite.md.tmpl
  eval/
    suite-general.md                    # G1–G10, re-skinnable
    score_core.py                       # generic checks + a DomainScorer interface (§8)
    run_ab.sh  aggregate.py             # harness, unchanged
```

Everything in `agents/` (8 roles), `rules/`, `skills/{scientific-method, paper-reading, simulation-based-inference}`, and the eval methodology moves into core — but **not verbatim**: §8 specifies the de-GW pass each touched file needs, with grep as the acceptance check.

### 2.1 The cache engine is fully core (zero pack query code)

Per-pack query code is retired entirely. `lib/pcache.py` reads any schema-conforming cache; a pack ships only its cache JSON and a thin builder. The reducer logic already in `query_snapshot.py` (`cmd_extremum`, `resolve`, `provenance`, the exit-2 fallback, `COMMON_ORDER`) is domain-agnostic — it just reads JSON. Promotion edits:
- parameterize the cache path (resolved via `pack_resolver.py`, or CLI `--cache <path>`, or `PRAXIS_CACHE`, instead of the hard-coded `SNAP` at `query_snapshot.py:36`);
- rename `events → entities` (keep an `events` alias read for back-compat);
- read `COMMON_ORDER` from `_meta.record_params` / a per-pack `display_order` instead of the GW constant;
- add the **Tier-0 serving filter** (§6): refuse to emit a numeric value without `(best, asymmetric error)` or an explicit `is_exact`/`bare-with-reason` flag, and refuse to emit a value without composing `provenance()`. This is the only enforcement layer that is *truly* mechanical, because `pcache.py` controls the bytes.

The **build** side stays a thin pack shim: `lib/pbuild.py` is the framework (paging, backoff, provenance stamping, superlative precompute, schema-write) and now also enforces **resumability + completeness** (§4, §5); a pack's `cache/build.py` supplies only endpoints/DOIs/param-field names — all already constants in the current `build_snapshot.py:32-47`.

### 2.2 Runtime domain resolution (convention-driven, cheap, ambiguity-safe)

`lib/pack_resolver.py` (~30 lines, stdlib, no LLM tokens, no network) reads each installed pack's `pack.json` and resolves the active domain in this order:

1. **`PRAXIS_DOMAIN` env var** — wins; supports A/B and multi-domain users.
2. **`.praxis/active` file** (working dir or repo root) — a one-line `pta`, written by `/praxis-use`.
3. **Sole-pack auto-detect** — if exactly one `praxis-*` pack is installed, use it. *(A judge who installs only `praxis-gw` never configures anything — "install one pack, zero config.")*
4. **One-question prompt** — if ≥2 packs and no selector, core asks once and writes the answer to `.praxis/active`.

It exposes `active_domain()`, `pack_dir()`, `data_skill_name()`, `cache_path()`, `expert_agent_name()`, `oracle_module()`. Resolution is a file read, never a token spend.

**Cross-domain ambiguity is a refusal, not a silent pick (mitigation folded in).** The dangerous case is a scope-sensitive question with ≥2 packs installed and a stale `.praxis/active`: *"What's the most massive black hole observed?"* is answerable by `praxis-gw` (stellar-mass BH) and a future `praxis-em` X-ray pack (Sgr A*-class) — defaulting to the active pack answers confidently in the wrong domain's scope, with valid provenance and no error. So:
- When **≥2 installed packs' data-skills both plausibly match a query's vocabulary**, the resolver **asks** rather than defaulting to active. `pvalidate.py` warns at install time when two co-installable packs' data-skill trigger vocabularies overlap (gate 2 below records each pack's `id_field` pattern; the resolver compares them).
- **Superlative / "ever" / "observed" / "so far" questions are inherently scope-sensitive** and always disambiguate domain first when ≥2 packs are present, even with a set `active`.
- Data-skill `description` triggers are **domain-qualified** (they include the `id_field` pattern), narrowing accidental cross-fire.

This is the one place the zero-config story and safe multi-pack routing genuinely tension; we resolve it by treating single-pack as the common case and forcing disambiguation only on the scope-sensitive minority (see Open questions, §10).

---

## 3. The domain-pack CONTRACT

A directory `praxis-<id>/` is a valid pack **iff** it ships these pieces and `lib/pvalidate.py` passes all gates (§3.4). The `pack.json` manifest is the single source of truth that both the resolver and the validator read.

### 3.1 Required pieces

| # | Piece | Path (convention) | Role |
|---|---|---|---|
| 1 | **Manifest** | `pack.json` | The typed contract: domain id, contract version, depends, **oracle tier + corpus license + expert attestation**, pointers, sources, scope model, threat taxonomy, M/I/S split, open limits, bridges. |
| 2 | **Domain-expert agent** | `agents/domain-expert-<id>.md` | The field authority: classification, well-measured-vs-prior-dominated, degeneracies, conventions, and the **hard scope/significance backstop**. Its irreducible judgment slots are *authored*, not generated (§4 Step 5). |
| 3 | **Data-access skill** | `skills/<id>-data/SKILL.md` | The retrieval contract: cache-first → `pcache.py` → live fallback *(tier-LIVE only)*; NL→command table; live-fallback conditions; the scope rule; the provenance/identifier rule. `description` triggers on the bare, domain-qualified question. |
| 4 | **Cache** | `cache/<id>_snapshot.json` | Provenance-stamped entity params with asymmetric uncertainty + precomputed superlatives; conforms to `cache.schema.json`; carries `results_count_reported` for the completeness gate (§5). |
| 5 | **Builder** | `cache/build.py` | Thin, **resumable** shim over `lib/pbuild.py`; the refreshable bootstrap; stamps `retrieved_utc` + DOIs + `results_count_reported`. |
| 6 | **SOTA index** | `cache/sota.json` | First-class, schema'd, cited literature **index** (DOI + your own one-line characterization + status + per-claim freshness), license-gated (§3.5). |
| 7 | **Oracle adapter** | `oracle/<id>_oracle.py` | Implements the core Oracle interface at the declared **tier**; `score_core.py` calls it for ground-truth-at-grade-time (tier-LIVE/REDERIVE) or registers "no machine oracle" (tier-ASSERTED). |
| 8 | **Domain eval suite** | `eval/suite-<id>.md` | The S-suite: G1–G10 re-skinned onto the field's failure modes. |
| | *(optional)* | `commands/<id>-brief.md` | A per-object brief (the re-skinned `/event`). |

### 3.2 The manifest (`pack.json`), filled in for `praxis-pta`

```jsonc
{
  "praxis_contract": "1.0",                 // core<->pack wire format (semver)
  "domain": {
    "id": "pta",                            // [a-z0-9-]+  -> plugin name praxis-pta
    "title": "Pulsar Timing Arrays",
    "band": "nanohertz gravitational waves",
    "depends": { "praxis-core": ">=1.0 <2.0" }
  },

  "expert_agent": "agents/domain-expert-pta.md",
  "data_skill":   "skills/pta-data/SKILL.md",
  "expert_attestation": {                   // who ratified Checkpoint B (or null = unverified)
    "name": "Dr. <name>", "affiliation": "<inst>", "ratified_utc": "2026-06-25T12:00:00Z"
  },
  "corpus_license": "open-only",            // attestation: SOTA corpus is open-license (§3.5)

  "cache": {
    "path": "cache/pta_snapshot.json",
    "schema": "praxis-core://cache.schema.json/1.0",
    "entity_kind": "release",               // what one record IS (event|release|pulsar|sample)
    "id_field": "release_tag",              // NANOGrav-15yr, EPTA-DR2, IPTA-DR2 ...
    "id_aliases": true,
    "cumulative_scope": "IPTA-DR2",         // default "so far/ever" set (superlative backstop)
    "supersede_rule": "complement",         // IPTA COMBINES members; releases don't replace
    "display_order": ["A_gwb","gamma_gwb","hd_significance_sigma","n_pulsars","timespan_yr"],
    "record_params": ["A_gwb","gamma_gwb","hd_significance_sigma","n_pulsars","timespan_yr"]
  },

  "sources": {
    "primary": [
      { "name": "NANOGrav 15yr", "kind": "zenodo", "doi": "10.5281/zenodo.8092551",
        "license": "CC-BY-4.0", "access": "dataset-doi",
        "products": ["par","tim","noise","gwb-posterior"] },
      { "name": "EPTA DR2",       "kind": "zenodo", "doi": "10.5281/zenodo.8091568",
        "license": "CC-BY-4.0" },
      { "name": "IPTA DR2",       "kind": "zenodo", "doi": "10.5281/zenodo.5787557",
        "license": "CC-BY-4.0" }
    ],
    "live_api": null,                        // PTA has NO live catalog REST API (see §3.6)
    "latest_release_probe": null,            // tier-LIVE only: cheap "newest tag/count" endpoint
    "clients": ["enterprise","enterprise_extensions","PINT","la_forge","PTArcade"]
  },

  "oracle": {
    "adapter": "oracle/pta_oracle.py",
    "tier": "REDERIVE",                      // LIVE | REDERIVE | ASSERTED  (HARD capability, §3.3)
    "kind": "cached-release-table",
    "transcription_audit": {                 // required for REDERIVE/ASSERTED
      "audited_n": 12, "audited_by": "Dr. <name>", "audited_utc": "2026-06-25T12:00:00Z" },
    "checks": ["entity_exists","param_within_sigma","scope_resolved","identifier_resolves"]
  },

  "sota": { "path": "cache/sota.json", "schema": "praxis-core://sota.schema.json/1.0",
            "refresh": { "trigger": "new-data-release", "cadence_hint": "P2Y",
                         "hard_expiry": "P3Y" } },   // tier without latest_release_probe MUST expire

  "conventions": {
    "frames": ["red-noise power-law: A, gamma", "f_ref = 1/yr",
               "h_c characteristic strain", "gamma=13/3 for SMBHB GWB"],
    "identifier_formats": { "pulsar": "J\\d{4}[+-]\\d{4}", "release": "[A-Za-z]+-\\w+" },
    "asymmetric_errors": true,
    "scope_trap": "no naive cross-release combination; resolve to the right release"
  },

  "skeptic_threats": [
    "common-uncorrelated red noise (CURN) vs Hellings-Downs correlation",
    "solar-system ephemeris systematics (BayesEphem)",
    "DM variations / solar wind / pulsar jitter mismodeling",
    "look-elsewhere / sky-scramble & phase-shift significance",
    "amplitude alone is NOT HD-correlated evidence"
  ],

  // measured / inferred / data-doesn't-answer -> feeds the interpreter's M/I/S split
  "measured_vs_inferred": {
    "measured":               ["timing residuals", "white-noise params"],
    "inferred_under_assumptions": ["A_gwb", "gamma (given a power-law spectrum)"],
    "speculative":            ["GWB source class: SMBHB vs cosmic strings vs phase transition"]
  },
  "open_limits": [
    "GWB source not yet distinguished (SMBHB population vs cosmological)"
  ],

  "bridges": ["SMBHB demographics / galaxy-merger history",
              "early-universe cosmology (cosmic strings, phase transitions, inflation)",
              "LISA (mHz) complementarity"],

  "commands": ["commands/release-brief.md"],
  "version": "0.1.0"
}
```

### 3.3 The oracle CAPABILITY TIER — the load-bearing addition

`oracle.tier` is a **hard capability**, not a label. It is what makes the no-API problem honest instead of hidden, and it gates which integrity claims `pvalidate.py` will let a pack advertise:

| Tier | What grades it | Catches | Integrity claim it may advertise | Eval `fabrication=0` claim? |
|---|---|---|---|---|
| **LIVE** | Independent API diff at grade-time (`score_core.py` calls the source's REST API; e.g. GW vs `gwosc.org/api/v2`) | Fabrication, transcription error, semantic error, staleness | Full mechanical cache integrity; live-fallback safety net; serve-time staleness check | **Yes** (with eval rate reported) |
| **REDERIVE** | No API, but `build.py` is **deterministic** over a fetched dataset DOI; a second run (human or second model) must **byte-match** the cache | Transcription drift; partial-build corruption (completeness gate) — **not** semantic error | Re-derivable cache integrity; **no** live fallback; hard-expiry staleness | Only for *re-derivability*, not for semantic correctness |
| **ASSERTED** | LLM-transcribed from prose/PDFs/tables; **no machine oracle** | Nothing automatically | **None.** Every served value carries an `UNVERIFIED-CACHE` banner | **No** — barred from the fabrication=0 claim |

Rules the validator enforces around the tier:
- A **tier-LIVE** pack must supply `sources.live_api` and `latest_release_probe`; only it gets the exit-2 live-fallback path in `pcache.py` and the serve-time staleness check (§6).
- A **tier-REDERIVE** pack must ship a deterministic `build.py` and pass a re-derivation check (re-run must byte-match), and must carry `oracle.transcription_audit` (a human-signed audit of N sampled values).
- A **tier-ASSERTED** pack **cannot be marked `initialized`** without a human-signed transcription audit (`oracle.transcription_audit`), serves every value with an `UNVERIFIED-CACHE` banner, and is barred from advertising the `fabrication=0` eval result. In the marketplace it is flagged `community/unverified` unless `expert_attestation` is also present.

**The generalization story, stated plainly:** Praxis-with-teeth (mechanical cache integrity) covers tier-LIVE and tier-REDERIVE fields. Tier-ASSERTED fields — which is most of science with no single queryable catalog — get the full method loop and the integrity *discipline*, but not the mechanical *guarantee*; the banner and the marketplace flag say so to the user. Whether the tier-LIVE/REDERIVE set is large enough to justify "generalize to science" is an open question (§10), not a claim we bury.

### 3.4 Validation gates (`lib/pvalidate.py` — the teeth)

Run by CI and by `/praxis-init` before it declares success. A pack is **contract-valid** iff:

0. **Reference-pack self-check (gate-0, CI):** the reference pack (`praxis-gw`) must pass *all* its own gates. The contract may never drift from the pack that defines it. (This gate caught the empty-DOI problem in §8.)
1. `pack.json` validates against `pack.schema.json`; `praxis_contract` major matches an installed core; `oracle.tier ∈ {LIVE,REDERIVE,ASSERTED}`.
2. `expert_agent` and `data_skill` files exist; the expert's frontmatter declares `model` + `tools`; the data skill's `description` contains the `id_field` pattern (triggers on the bare domain question); the trigger vocabulary is recorded for cross-pack overlap warnings (§2.2).
3. The cache exists, validates against `cache.schema.json`, `_meta.retrieved_utc` is present and parseable, and **`len(entities) == _meta.results_count_reported`** (the **completeness gate** — catches a partial-page build death that would otherwise validate structurally and compute superlatives over the wrong subset). **No cache → pack is marked `uninitialized` and cannot answer from a stale blob.**
4. Every `sources.primary[].doi` **resolves** (HTTP HEAD via doi.org online; offline, must be well-formed `10.\d+/…`). **Empty-string DOIs fail; an explicitly-allowed `null`-with-flag (`"doi_status": "not-exposed"`) passes** (see §8 — the reference pack has two empty catalog DOIs today). doi.org resolutions are cached so refresh does not re-HEAD every DOI.
5. The oracle adapter is importable and exposes the four `checks`; for REDERIVE it passes the byte-match re-derivation check; for REDERIVE/ASSERTED `oracle.transcription_audit` is present.
6. `cumulative_scope` resolves to a scope present in the cache (the superlative backstop has somewhere to land).
7. `record_params` ⊆ the param names present in the cache.
8. Every `sota.json` entry carries a resolvable DOI, an **open-license source** when `corpus_license: "open-only"` (§3.5), and a per-claim `asserted_utc`.
9. **No expert-judgment slot is still a template placeholder** (§4 Step 5) — the scope traps, prior-dominated params, key degeneracies, and significance pitfalls must be filled, or the pack stays `uninitialized`.
10. **Drift-check (every pack, not just the reference):** the scope rule encoded in `pack.json` (`cumulative_scope` + `scope_trap`) matches the scope rule the authored `domain-expert-<id>.md` prose encodes.
11. **Tier consistency:** tier-LIVE requires `live_api` + `latest_release_probe`; tier-REDERIVE/ASSERTED require `transcription_audit`; tier without a `latest_release_probe` requires a `sota.refresh.hard_expiry`.

Gates 3, 4, 5, 6, 7, 8, 9, 10, 11 are the teeth that keep cache integrity enforceable across every third-party pack. Note what they do *not* do: validate the next generated answer. That is §6's two-point split.

### 3.5 The SOTA index (`cache/sota.json`) — citation-index by default, license-gated

To remove redistribution liability (a marketplace of packs each shipping scraped structured paper-extracts is takedown-bait), `sota.json` is a **citation index by default**, not a stored structured-abstract: it stores the **pointer + your own one-line characterization + status + freshness**, and the richer extraction (claim/method/assumptions/limitations) is fetched **live at deep-loop time** so the copyrighted derived text is never redistributed inside the artifact. This also fixes a staleness path (see §5).

```jsonc
{
  "_meta": { "retrieved_utc": "2026-06-25T12:00:00Z", "corpus_version": "2023-GWB-evidence",
             "corpus_license": "open-only" },
  "papers": [
    {
      "id": "arXiv:2306.16213", "doi": "10.3847/2041-8213/acdac6",
      "source_license": "CC-BY-4.0",                 // gate 8: must be open when corpus open-only
      "title": "NANOGrav 15yr: Evidence for the GWB",
      "my_characterization": "Headline HD-correlated GWB evidence paper; defines the 15yr A_gwb.",
      "status": "multi-PTA convergent (EPTA/PPTA/CPTA); source class contested",
      "asserted_utc": "2026-06-25T12:00:00Z",        // freshness of THIS judgment
      "valid_until_release": "IPTA-DR3"              // status auto-flags stale past this release
    }
  ]
}
```

If a pack author elects the **richer stored-extraction** form, `pvalidate.py` gate 8 requires every entry to come from an open-license source (arXiv/Zenodo with a declared CC license) and stores the license field; closed-license extractions are refused. The bootstrap fetcher (§4) carries a per-source robots/ToS allowlist and a polite global rate limit (generalizing the `time.sleep(0.3)` already in `build_snapshot.py`). Redistribution-license responsibility sits explicitly with the pack author via the required `corpus_license` attestation, so the marketplace can filter.

### 3.6 The honest GW-vs-PTA asymmetry (named via the tier, not hidden)

GW has a live REST API (`gwosc.org/api/v2`) → `oracle.tier: "LIVE"`, the strongest form (the grader can't bake in our own errors; exit-2 has somewhere to fall back; superlatives are checkable against live). **PTA has no live catalog API** → at best `oracle.tier: "REDERIVE"`: the cache is built deterministically from the published release tables (Zenodo DOIs) and must byte-match on a second `build.py` run, with a human-signed audit of N sampled values. This is *categorically* weaker — it catches transcription drift, not semantic error, and it has no live-fallback — and the **tier**, not a footnote, is what carries that fact through validation, serving (§6), and the marketplace.

---

## 4. The `/praxis-init <domain>` bootstrap — the ONE expensive step, made transactional

`/praxis-init <domain>` is a core command run **as the principal-investigator** — itself a rigor-governed Praxis investigation ("characterize this field and build its pack"), obeying the same integrity rules (every source retrieved + cited, nothing recalled). It is the **only** token-hungry, network-heavy operation; everything afterward is cheap. The naive "happy-path narrative" version is dangerous: a long multi-agent web-heavy run with no transactional semantics leaves a poisoned half-pack that validates. So init is **two-phase and transactional**:

- **Phase H (headless, CI-runnable, retryable unattended):** discover → build → validate into a **staging dir**. Produces a *draft* pack. No human blocking. Resumable across throttling/502s.
- **Phase R (interactive ratification):** the three checkpoints, applied to the draft. Only human judgment is blocking.

Atomicity rule: the staging dir is **atomically renamed to the pack dir only when all gates are green AND the post-build smoke A/B passes**; `.praxis/active` is set only then. It accepts hints: `/praxis-init pta --archive "NANOGrav/EPTA/IPTA/MPTA" --sota "NANOGrav 15yr GWB evidence"`. It refuses to overwrite an initialized pack without `--reinit`. It **prints a cost/time estimate per oracle tier and confirms before the expensive Phase-H fetch** (the "cheap N packs" economics depend on this number; see §10).

**Step 0 — Frame & scaffold (Phase H).** Resolve `<domain>` → `id`. Create a **staging dir** and stamp the `templates/` into place: skeleton `pack.json` (status `uninitialized`), empty `cache/`, `agents/`, `skills/`, `oracle/`, `eval/`.

**Step 1 — Discover authoritative sources (Phase H,** `literature-reader` + `skeptic`, live web). Identify (a) the field's **authoritative data archive(s)** + access protocol — and thereby its achievable **oracle tier** — and (b) the **landmark SOTA papers** with open-license status. *Retrieval, never recall* — every source gets a resolvable DOI/URL pulled from the source; the fetcher obeys the robots/ToS allowlist and global rate limit. The skeptic vets each. → **CHECKPOINT A (Phase R):** the human ratifies the source list + DOIs **and the proposed oracle tier**. Nothing is promoted out of staging until ratified (satisfies rule 9 at the moment identifiers enter the system).

**Step 2 — Learn the conventions (Phase H,** `literature-reader` + a transient generalist domain pass). Extract, *from the sources*, the glossary, frames/units, identifier scheme, release/cumulative model + default scope, the threat taxonomy, the **measured/inferred/speculative split**, the open limits, and the bridge targets. These populate `conventions`, `skeptic_threats`, `measured_vs_inferred`, `open_limits`, `bridges`. → **CHECKPOINT B (Phase R):** the human reviews the conventions/glossary **and authors the irreducible expert-judgment slots** (the worked scope/significance pitfalls). Every nontrivial entry is cited (paraphrased, per integrity rule 5).

**Step 3 — Ingest the SOTA index (Phase H,** `paper-reading` skill). For each landmark paper, write the **citation-index** entry (DOI + your one-line characterization + status + `asserted_utc` + `valid_until_release` + `source_license`) to `cache/sota.json`. The richer claim/method/assumptions/limitations extraction is fetched **live at deep-loop time**, not stored, unless the author opts into the license-gated stored form (§3.5). Any source that can't resolve to a real identifier is dropped, not invented.

**Step 4 — Build the data cache (Phase H,** `analyst-coder`). Generate `cache/build.py` from the template, specialized to the archive from Step 1 (REST endpoints/pagination for tier-LIVE; Zenodo dataset products + published parameter tables for tier-REDERIVE; PDF/table transcription for tier-ASSERTED). Run it once into staging. **Resumability + completeness are mandatory:** `build.py` checkpoints per page to staging (a 502 at page 12 of 20 resumes, not restarts — the GW builder already needs a 5-try backoff because "the v2 API is throttled and 502s on load", `build_snapshot.py:51`), records `results_count_reported` (`build_snapshot.py:85` already fetches it), and pvalidate gate 3 fails if `len(entities) != results_count_reported`. Each entity's params are collected with asymmetric errors, each release DOI resolved, superlatives precomputed, and the snapshot stamped with `source`, `retrieved_utc`, `dois`, `cumulative_scope`, `builder_version`, `results_count_reported`. A value it can't retrieve is set null+flag (never guessed); a param it can't retrieve is omitted, not fabricated.

**Step 5 — Emit the pack artifacts (Phase H draft + Phase R authoring).** Fill from templates, *from the cited material* (the generation prompt is fed `conventions` + `sources` + a sample of the snapshot + `sota.json`, not the model's prior):
- `agents/domain-expert-<id>.md` — conventions, the threat list, the open limits, the M/I/S split **generated as a scaffold**; the irreducible judgment slots (scope traps, prior-dominated params, key degeneracies, significance pitfalls) are left as **explicit BLANK placeholders that block gate 9** until authored at Checkpoint B. We do **not** sell auto-generated expertise: a generated expert reads authoritative because it is *fluent*, and a fluent-but-wrong convention (a fabricated analog of `gamma=13/3`) is caught by no gate and invisible to a non-expert ratifier. The deliverable is a *scaffold + an expert-required worklist*, not a finished authority.
- `skills/<id>-data/SKILL.md` — "cache-first → `pcache.py` → live fallback *(LIVE only)*", the NL→command table, live-fallback conditions, the scope rule, the provenance rule; `description` written to trigger on the bare, domain-qualified question.
- `oracle/<id>_oracle.py` — from the oracle template at the declared tier (LIVE diff / REDERIVE byte-match / ASSERTED no-machine-oracle stub).
- `eval/suite-<id>.md` — G1–G10 re-skinned onto the field's failure modes (post-release retrieval, cross-release scope trap, numerical fidelity, nonexistent-entity trap, the field's overinterpretation trap).
- `commands/<id>-brief.md` if a per-object brief makes sense.

**Step 6 — Validate, smoke-test, adversarial self-test (Phase H validate + Phase R ratify).** Run all §3.4 gates against staging. Run a smoke A/B: 3 sample questions through `pcache.py` (must return cited values) and one through the oracle (must diff/byte-match cleanly — tier-LIVE/REDERIVE). **Adversarial self-test:** the `skeptic` generates N field-specific trap questions at init; the generated expert+cache must answer them correctly **against the oracle** before Checkpoint C — turning "looks fluent" into "survives the field's own pitfalls." *(This test only works for tier-LIVE/REDERIVE; for tier-ASSERTED there is no oracle to check against — the trap answers are reviewed by the human ratifier, and the pack remains marked unverified.)* → **CHECKPOINT C (Phase R):** show the validation report. On green, **atomically rename staging → pack dir**, print install instructions, and set `.praxis/active = <id>` — only after the smoke A/B actually passes, never on gate-green alone. On any red gate or failed smoke, staging is discarded and the failure reported (never silently shipped — integrity rule 1).

**What `/praxis-init pta` writes to disk (after the atomic rename):**
```
praxis-pta/.claude-plugin/plugin.json
praxis-pta/pack.json                         # status: initialized; oracle.tier: REDERIVE
praxis-pta/agents/domain-expert-pta.md       # scaffold + human-authored judgment slots
praxis-pta/skills/pta-data/SKILL.md
praxis-pta/cache/build.py                     # resumable, completeness-stamped
praxis-pta/cache/pta_snapshot.json            # provenance-stamped
praxis-pta/cache/sota.json                    # cited SOTA index (license-gated)
praxis-pta/oracle/pta_oracle.py               # REDERIVE byte-match flavor
praxis-pta/eval/suite-pta.md
praxis-pta/commands/release-brief.md
.praxis/active                                # -> "pta"
```

The expensive work (Phase H: web search + ingest + build) happens **once** and can be scheduled/retried unattended; afterward every quick query is a stdlib `pcache.py` call (zero LLM tokens, zero network).

---

## 5. Knowledge-cache design

### 5.1 On-disk structure (one schema, all packs — `cache.schema.json`)

Generalize today's `gwtc_snapshot.json` from `events` to `entities`; everything else identical (`_meta`/`records` keep their shape). The verified reference snapshot has `_meta` keys `{catalog_dois, n_events, note, record_params, results_count_reported, retrieved_utc, source, umbrella_catalog}` and 391 events — the generalization is a rename, not a restructure.

```jsonc
{
  "_meta": {
    "praxis_contract": "1.0",
    "domain": "pta",
    "entity_kind": "release",
    "cumulative_scope": "IPTA-DR2",
    "supersede_rule": "complement",
    "source": "https://doi.org/10.5281/zenodo.8092551 (+ EPTA/IPTA records)",
    "retrieved_utc": "2026-06-25T12:00:00Z",     // staleness marker + live/cache discriminator
    "builder_version": "praxis-pta/0.1.0",
    "results_count_reported": 3,                  // completeness gate: must == len(entities)
    "dois": { "NANOGrav-15yr": "10.5281/zenodo.8092551", "EPTA-DR2": "10.5281/zenodo.8091568" },
    "record_params": ["A_gwb","gamma_gwb","hd_significance_sigma","n_pulsars","timespan_yr"]
  },
  "records": {                                     // precomputed superlatives (argmax/argmin)
    "A_gwb": { "max": {"entity":"NANOGrav-15yr","best":2.4e-15,"scope":"NANOGrav-15yr"} }
  },
  "entities": {                                    // was "events"
    "NANOGrav-15yr": {
      "id_aliases": ["NG15","ng15yr"],
      "release_doi": "10.5281/zenodo.8092551",
      "parameters": {
        "A_gwb":  { "best": 2.4e-15, "upper_error": 0.7e-15, "lower_error": -0.6e-15, "unit": "" },
        "gamma_gwb": { "best": 3.2, "upper_error": 0.6, "lower_error": -0.6, "unit": "" },
        "hd_significance_sigma": { "best": 3.5, "upper_error": 0.5, "lower_error": -0.5, "unit": "sigma" },
        "n_pulsars": { "best": 67, "is_exact": true, "unit": "" },
        "timespan_yr": { "best": 16.0, "unit": "yr" }
      }
    }
  }
}
```

The per-param record `{best, upper_error, lower_error, unit, is_upper_limit, is_lower_limit, is_exact}` is **unchanged from GW** — that is the point: `pcache.py` reads this schema regardless of field. A pack with per-object lookups (PTA pulsars) ships a second cache file with `entity_kind: "pulsar"`, `id_field: "jname"`, same schema. Caches ship **gzipped** (`pcache.py` reads `json.load` over gzip trivially) so per-object packs don't bloat the marketplace.

### 5.2 Provenance tags (non-negotiable)

Provenance is reconstructable without storing it per value: each entity carries `release_doi`; `_meta` carries `source`/`retrieved_utc`/`dois`. `pcache.py`'s `provenance()` composes `"<release>, <doi>; snapshot retrieved <utc>"` — identical to the GW helper (`query_snapshot.py:58`). The `retrieved_utc` stamp is what makes a cached value reportable as **"retrieved <date>, <DOI>"** vs a live value as **"live, fetched now"** — the mechanical basis for "cache ≠ live" (§6).

### 5.3 Quick-lookup vs deep-research serving (same artifact, two tiers)

- **Tier-0 (quick / `/quick`):** core's `quick.md` → `pack_resolver` → `pcache.py entity|count|max|min|list|catalogs|meta` against the cache. Stdlib, offline, sub-second, **zero LLM tokens, zero network**. Prints `best ± asymmetric error`, unit, scope, DOI + snapshot date, through the **deterministic serving filter** (§6). **Never interprets.** Exit code 2 = not in cache → fall back to exactly one live fetch **(tier-LIVE only)** (same contract as `query_snapshot.py:102`); for tier-REDERIVE/ASSERTED a cache miss is an honest "absent — not in the cached release set" refusal, never a recall.
- **Tier-1 (deep / `/investigate`):** the full loop. The cache is the *cited background layer* — stage 2 reads `cache/sota.json` (and fetches the richer extraction live); stage 4 reads the snapshot for retrieved baselines and the scope-resolved superlative. The analyst-coder then goes live (tier-LIVE) or to the dataset DOIs/`clients` (REDERIVE) for full posteriors/raw products the catalog-level cache doesn't hold (PTA: `enterprise`/`PINT` over `.par`/`.tim`/noise files). The expert's scope backstop and the data skill's scope rule both fire. **Only the ACTIVE pack's agent/skill is loaded into the deep loop by default** (context cap); `cross-domain-bridge` may explicitly request a second pack's expert rather than all packs being ambient.

### 5.4 Staleness — a hard serve-time check, not a soft flag

A stale-but-cited wrong answer (an old GWTC mass served with a valid DOI and a clean provenance string after a newer release supersedes it) defeats "retrieve don't recall" *more* thoroughly than recall, because it looks rigorous and passes every build-time gate. So staleness is enforced at **serve time**, by tier:

- **tier-LIVE:** `pcache.py meta` does **one cheap live HEAD/count** against `sources.latest_release_probe`. If the live latest-tag/count differs from `_meta`, every served value is downgraded to *"CACHED `<utc>`, a newer release may exist — re-verify"*, and **superlatives exit non-zero** (superlatives are the most release-sensitive — the GW231123 "most massive ever" pitfall is exactly this). A **scheduled refresh check** (the env's cron/scheduled-task tooling) pings the probe per tier-LIVE pack and opens a refresh task — turning "human notices a release" into "system notices."
- **tier-REDERIVE / tier-ASSERTED:** there is **no latest-release endpoint to ping**, so there is no automated staleness signal at all. These carry a conservative **hard-expiry** (`sota.refresh.hard_expiry`, gate 11): past `retrieved_utc + hard_expiry` the cache **refuses to serve as authoritative** (downgrades to "expired cache — re-verify") rather than serving a soft flag. Choosing the expiry trades false-stale against confidently-outdated and is a guess (§10).
- **SOTA judgments rot too.** Each `sota.json` entry carries `asserted_utc` and `valid_until_release`; the deep loop flags *"this consensus judgment predates release X"* so it does not reason over a frozen "the data does not yet distinguish" conclusion that the field has since resolved. The citation-index-by-default design (§3.5) means the actual extraction is re-fetched live, so the contested/convergent status is re-derived at use time rather than frozen in the artifact.
- `praxis-packs.md` reads each pack's `_meta.retrieved_utc`, `sota.refresh.cadence_hint`/`hard_expiry`, and on-disk size, printing **age**, **expiry status**, and **size** so growth and rot are visible.

### 5.5 The refresh command

Refresh is **release-triggered, not clock-triggered** — but a tier-LIVE pack's scheduled probe (§5.4) makes the trigger a *system* event, not a human noticing. `/praxis-refresh <domain>` re-runs `<pack>/cache/build.py` (resumably, into staging) and re-extracts any SOTA entries whose DOIs changed/added, stamping a fresh `retrieved_utc` + `builder_version`, then re-runs `pvalidate.py` and atomically swaps. It re-runs init Steps 3–4 + 6 only, leaving the human-ratified conventions and the **authored expert judgment slots intact** (`/praxis-init <domain> --refresh` is the equivalent flag). `supersede_rule` encodes whether a new release **replaces** (GW: a GWTC catalog supersedes) or **complements** (PTA: IPTA combines members); `pbuild.py` honors it so refresh adds the new IPTA entity without deleting member entities.

---

## 6. How integrity rules apply to cached knowledge — two enforcement points, never conflated

The cache is *retrieval with provenance*, **not** recall. But "mechanically enforced" is precise about *where*:

**Build-time, mechanically enforced (the cache artifact).** `pvalidate.py` gates (§3.4) certify the cache is well-formed, complete (gate 3 completeness), DOI-resolvable (gate 4), scope-landable (gate 6), uncertainty-bearing (schema), tier-consistent (gate 11), and expert-slots-filled (gate 9). Core ships no data, so core *cannot* answer a domain question without a pack; gate 3 marks a pack with no cache `uninitialized` — it physically cannot answer from a stale blob.

**Serve-time, mechanically enforced (Tier-0 bytes).** `pcache.py` controls the output bytes, so its serving filter is *truly* mechanical: it **refuses to emit a numeric value** without `(best, asymmetric error)` or an explicit `is_exact`/`bare-with-reason` flag, and **refuses to emit any value** without composing `provenance()`. The exit-2 contract distinguishes absent from retrieved (rule 1); the serve-time staleness check (§5.4) prevents confidently-stale superlatives.

**Answer-time, eval-gated (Tier-1 free generation — NOT categorically enforceable).** The deep-loop synthesis is prose-steered and empirically fabricates ~11% even in the tuned GW pack (`provenance_rate 0.889`, one B run `has_gwosc_doi:false`). No design makes Tier-1 categorically non-fabricating. So the only honest claim is the **eval-measured fabrication rate per pack**, reported like `eval/aggregate.json` does, with a **release gate** (e.g. `provenance ≥ 0.95` over N runs) — not categorical enforcement. The thesis sentence is therefore: *integrity is mechanically enforced for cache integrity and Tier-0 serving, and eval-gated for Tier-1 generation.*

Per-rule mapping:
- **Cache ≠ live.** `release_doi` + `_meta.retrieved_utc` on every datum; `pcache.py` labels cached vs live; serve-time staleness downgrades stale values.
- **Still cite.** Gate 4 resolves every `sources` DOI; gate 8 resolves every `sota.json` DOI and checks license; Checkpoint A ratifies identifiers at entry (rule 9). Empty-string DOIs are rejected (§8 fix); `null`-with-flag is the only allowed absence.
- **No fabrication / retrieve-don't-recall.** Every answer flows through a pack's provenance-stamped cache or a live fetch (tier-LIVE); the builder writes null+flag for absent values; tier-REDERIVE/ASSERTED cache misses refuse rather than recall.
- **Uncertainty always carried.** `cache.schema.json` *requires* `upper_error`/`lower_error` per numeric param; the Tier-0 filter refuses a bare median for an asymmetric posterior.
- **M/I/S separability.** `measured_vs_inferred` feeds the interpreter's three-layer labeling; `open_limits` licenses honest declination.
- **Scope discipline.** `cumulative_scope` is a required, validated field (gate 6), wired into *both* the expert's backstop and the data skill's rule — deliberate double-enforcement.
- **Mandatory skeptic, made specific.** `skeptic_threats` feeds the generic skeptic a field-specific taxonomy.
- **Allow re-verification.** Tier-1 can force a live fetch (tier-LIVE) or re-derive (tier-REDERIVE byte-match audit) on demand; `/praxis-refresh` re-grounds the whole cache.
- **Tier honesty.** tier-ASSERTED values carry an `UNVERIFIED-CACHE` banner and are barred from the fabrication=0 claim — the user is told the guarantee is absent, not weaker.

---

## 7. Distribution + naming + versioning

- **Naming:** core is `praxis-core`; every pack is `praxis-<id>` (`praxis-gw`, `praxis-pta`, `praxis-gwspace` (LISA), `praxis-condmat`, …). The directory name, the `plugin.json` name, the `pack.json` `domain.id`, the `domain-expert-<id>` suffix, the `<id>-data` skill, and the `PRAXIS_DOMAIN` value are **the same token** — that identity is the convention the resolver rests on. "Siren" survives as the **display title** of `praxis-gw`, not its package id.
- **Marketplace:** one `.claude-plugin/marketplace.json` lists `praxis-core` plus each pack with its `depends`. Each pack entry advertises `domain.id`, `band`, `praxis_contract`, cache `retrieved_utc`, **`oracle.tier`**, **`corpus_license`**, and whether `expert_attestation` is present — so a browser sees freshness, the strength of the integrity guarantee, the redistribution posture, and whether a real expert signed off (vs an LLM solo run, flagged `community/unverified`) *before* installing.
- **Versioning — three independent axes:**
  1. **`praxis_contract`** (semver) — the core↔pack wire format. A contract **major** bump is the only thing that can break a pack.
  2. **core version** — the method/engine.
  3. **pack version** — bumped on each cache refresh / convention edit.
  A pack pins `depends.praxis-core: ">=1.0 <2.0"`; `pvalidate.py` enforces it. Payoff: **refreshing a pack's cache never touches core; upgrading core can't silently change a pack's science.**
- **Install models:** *Specialist* (`praxis-core` + one pack → sole-pack auto-detect → zero config); *Multi-domain* (core + several packs; switch with `/praxis-use <id>` or `PRAXIS_DOMAIN`; scope-sensitive questions force disambiguation, §2.2).
- **Testing/judging:** `claude --plugin-dir praxis-core --plugin-dir praxis-gw` (core first), matching the existing `--plugin-dir` A/B harness; `claude plugin validate .` per the testing memory, now backed by `pvalidate.py`. Eval `runs/` are **dev-only and kept out of the distributed pack** (this repo ships 18 run JSONs — they bloat distribution).

---

## 8. Migration plan: today's fused plugin → praxis-core + praxis-gw

Re-scoped honestly: this is a **refactor**, not a "mechanical, low-risk, lift-and-shift," because the "generic" pieces are still GW-coupled in code (verified) and the reference cache violates a gate the contract defines. Two regression gates govern acceptance, plus a verified-data prerequisite:

- **Score-parity:** `run_ab.sh` against `--plugin-dir praxis-core --plugin-dir praxis-gw` must match the committed `eval/aggregate.json`.
- **Sole-pack-equivalence:** running with *only* `praxis-gw` must behave **identically to today** — sole-pack auto-detect resolves every `${PRAXIS_DOMAIN}` to `gw`, `pcache.py` reads the renamed snapshot, scope rule + provenance unchanged.
- **Gate-0 self-check:** `praxis-gw` must pass *all* its own §3.4 gates (the contract may not drift from the pack that defines it).

**Step 0 — Fix the reference data FIRST (prerequisite, before gate 4 is even written).** The reference snapshot has **two empty `catalog_dois` strings** (`GWTC-2.1-confident`, `GWTC-3-confident` — verified). Gate 4 as designed (well-formed `10.\d+/` + HEAD) would **reject the reference pack's own cache**. So: decide the canonical form (bare DOI vs full URL — today they are full `https://doi.org/...` URLs), backfill the two missing DOIs *or* model them as explicit `null`-with-flag (`"doi_status":"not-exposed"`), and define gate 4 to **accept null-with-flag but reject empty-string**. Only then is the contract defined against conformant reference data.

**Step 1 — carve core.** Move into `praxis-core/`: `rules/scientific-integrity.md`, `skills/{scientific-method, paper-reading, simulation-based-inference}`, the 8 generic agents (everything except `domain-expert-gw.md`), `commands/{investigate.md, quick.md}`, `eval/{suite-general.md, run_ab.sh, aggregate.py}`. Add `praxis-core/.claude-plugin/plugin.json` (`name: praxis-core`).

**Step 2 — de-GW the "generic" agents (a real edit pass, not a move).** Six of eight grep-hit GW tokens (verified: `principal-investigator`, `analyst-coder`, `literature-reader`, `interpreter`, `cross-domain-bridge`, `next-steps`). Each needs worked GW examples replaced with neutral placeholders. **Acceptance check: `grep -riE 'gw|gwosc|chirp|bilby|detector' praxis-core/agents/` returns zero hits.** Drop the GW tool list from `analyst-coder.md` → point at the pack's `sources.clients`.

**Step 3 — promote the cache engine.** `skills/gwosc-data/query_snapshot.py` → `praxis-core/lib/pcache.py` (+ the Tier-0 serving filter and serve-time staleness check); `skills/gwosc-data/build_snapshot.py` → `praxis-core/lib/pbuild.py` (+ resumability + completeness) + a thin `praxis-gw/cache/build.py` shim. Edits: parameterize the cache path; rename `events → entities` (keep `events` alias read); read `display_order`/`record_params` from `_meta`. Add `pvalidate.py`, `pack_resolver.py`, the three JSON Schemas. **Per-pack query code is retired** — `praxis-gw` ships no `query_snapshot.py`.

**Step 4 — restructure the scorer BEFORE moving it (it is not separable as a "regex layer stays in core").** Verified: in `score.py`, generic regexes (`RE_ASYM_ERR`, `RE_ANY_DOI`, `RE_ARXIV`) and GW regexes (`RE_GWOSC_DOI=10.7935`, `RE_CATALOG=GWTC-`, `RE_EVENT=GW\d{6}`, `RE_GWTC_UMBRELLA`) live in the **same** `score_answer()`, and the superlative-word→param heuristic (`~line 465`: `massive→total_mass_source`, `distant→redshift`) plus `SUPERLATIVE_CONFIG` are GW physics inside the scorer. Factor `score_answer` into a generic `score_core.py` (asym-error / any-DOI / arxiv / citation checks) **+ a pack-supplied `DomainScorer`** (its DOI-prefix regex, event/catalog patterns, superlative param map) injected via the oracle adapter. The live-GWOSC diff (`GWOSC_BASE ~line 80`, fabrication check `~line 413`) becomes `praxis-gw/oracle/gwosc_oracle.py` behind the generic Oracle interface at `tier: LIVE`. The GW heuristics become `praxis-gw` config, not core code.

**Step 5 — de-GW the core text (the three surgical edits).**
- `skills/scientific-method/SKILL.md:44` → replace the GW hard rule with the domain hook: *"Any question about a specific entity, a release/catalog, or a superlative within a catalog MUST invoke the active pack's `<id>-data` skill and retrieve real values with their identifier BEFORE answering — cache first, live only on a miss; never from memory; never answer a catalog superlative without querying the cumulative scope."* Stage 4's `domain-expert-gw` → `domain-expert-${PRAXIS_DOMAIN}`.
- `agents/principal-investigator.md:10,16` and `commands/quick.md` → `gwosc-data`/`query_snapshot.py` → "the active pack's data skill (via `pcache.py`)"; `domain-expert-gw` → `domain-expert-${PRAXIS_DOMAIN}`; GW worked examples → generic placeholders.
- `rules/scientific-integrity.md` rule 9 → generalize "GWOSC `doi`" to "a resolvable identifier from the field's authoritative source (the pack defines its form)"; keep the principle verbatim.

**Step 6 — build `praxis-gw`.** Move `agents/domain-expert-gw.md`, `skills/gwosc-data/SKILL.md` → `praxis-gw/skills/gw-data/SKILL.md`, `commands/event.md` → `praxis-gw/commands/event.md`, `eval/{suite-gw.md, runs/(dev-only), FOR-JUDGES.md, comparison-set-*, results-demo.md, cost.md}`. Move the cache: `skills/gwosc-data/data/gwtc_snapshot.json` → `praxis-gw/cache/gwtc_snapshot.json`, renaming `events → entities`, `catalog_dois → dois`, `umbrella_catalog → cumulative_scope`; add `_meta.domain="gw"`, `entity_kind="event"`, `supersede_rule="replace"`, `builder_version`. (`records`, `record_params`, `source`, `retrieved_utc`, `results_count_reported` already match — verified.) Author `praxis-gw/pack.json` (`oracle.tier: "LIVE"`, `oracle.kind: "live-api"`, `cumulative_scope: "GWTC"`, `entity_kind: "event"`, `id_aliases: true`, `corpus_license`, `expert_attestation`). Build `praxis-gw/cache/sota.json` as the **citation index** over the GW landmark literature (mass-gap, H0, EOS) — the GW SOTA currently implicit in the agents' prose becomes the first-class artifact.

**Step 7 — validate + regression-gate.** Run `pvalidate.py praxis-gw/` (all §3.4 gates against the *moved, DOI-fixed* cache — proves the contract describes reality, gate-0). Run both regression gates. Run the grep acceptance check from Step 2.

**Step 8 — marketplace + docs.** Update `marketplace.json` to list `praxis-core` + `praxis-gw` (with tier/license/attestation fields). Update `CLAUDE.md`'s extension recipe to: "to add a field, run `/praxis-init <domain>`, ratify the three checkpoints (authoring the expert-judgment slots), ship the validated `praxis-<id>` pack." `praxis-pta` is then a `/praxis-init pta` away — no core or `praxis-gw` change.

---

## 9. Worked `praxis-pta` walkthrough

**(a) Init (the one expensive step — two-phase, transactional).**
```
$ claude --plugin-dir praxis-core
> /praxis-init pta --archive "NANOGrav/EPTA/IPTA/MPTA" --sota "NANOGrav 15yr GWB evidence"
```
PI prints a cost/time estimate for the tier and confirms. **Phase H (headless):** `literature-reader` + `skeptic` find NANOGrav/EPTA/PPTA/CPTA/IPTA Zenodo records + the 2023 evidence papers, resolving DOIs live (polite rate limit, robots/ToS allowlist). Because PTA has **no live catalog API**, the proposed oracle tier is **REDERIVE**. `build.py` builds **into staging**, checkpointing per page; it stamps `results_count_reported` and the completeness gate confirms `len(entities)==3`. `cache/sota.json` is written as a **citation index** (DOIs + characterizations + `asserted_utc` + `valid_until_release: IPTA-DR3`, license CC-BY). **Phase R (ratification):** **Checkpoint A** — human confirms the DOIs are the authoritative Zenodo records (not mirrors) **and ratifies tier REDERIVE**. **Checkpoint B** — human reviews conventions (red-noise `A`/`gamma`, `f_ref=1/yr`, HD vs CURN, `gamma=13/3`, the no-naive-cross-release scope trap, the M/I/S split) **and authors the expert-judgment slots** ("an `A_gwb` posterior alone is not HD evidence; significance needs sky-scrambles/optimal-statistic") — these BLANK slots had blocked gate 9. Adversarial self-test: the skeptic's N trap questions are answered against the REDERIVE oracle (byte-match) before green. **Checkpoint C** — validation report green, byte-match audit signed (`audited_n: 12`) → **atomic rename staging → praxis-pta/**, smoke A/B passes → `.praxis/active = pta`. The plugin is permanently a PTA specialist.

**(b) A quick query (Tier-0 — zero tokens, zero network).**
```
> /quick what is the GWB amplitude in NANOGrav 15yr?
```
`quick.md` → `pack_resolver` (sole pack → `pta`) → `pcache.py entity NANOGrav-15yr --cache praxis-pta/cache/pta_snapshot.json`, through the serving filter. Output:
```
NANOGrav-15yr
  A_gwb = 2.4e-15 +0.7e-15/-0.6e-15
  gamma_gwb = 3.2 +0.6/-0.6
  hd_significance_sigma = 3.5 sigma +0.5/-0.5
  PROVENANCE: NANOGrav-15yr, 10.5281/zenodo.8092551; snapshot retrieved 2026-06-25T12:00:00Z
```
No interpretation. tier REDERIVE → no live fallback: a cache miss is an honest "absent from the cached release set" refusal, never a recall. Because tier is REDERIVE (not LIVE), values past the hard-expiry would downgrade to "expired cache — re-verify." If the user asks "is that strong evidence for a SMBHB background?" the guardrail fires: that needs an *inference* → stop and offer `/investigate`.

A scope-trap superlative uses the cumulative backstop:
```
> /quick highest GWB amplitude detected so far?
→ pcache.py max A_gwb   # scope = IPTA-DR2 (cumulative_scope), NOTE that per-release
                        # (e.g. NANOGrav-15yr only) differs — report scope explicitly.
```
With ≥2 packs installed, this "so far" superlative would first force domain disambiguation (§2.2) rather than silently using `active`.

**(c) A deep investigation (Tier-1 — full loop + re-derive/live retrieval).**
```
> /investigate Does the NANOGrav 15yr signal favor a SMBHB background over cosmic strings?
```
PI runs the loop, loading **only the active pack's** expert/skill into context. **(2)** `literature-reader` reads `cache/sota.json` and fetches the richer claim/method/limitations extraction **live** (citation-index design — not redistributed); the `valid_until_release` flag warns if the consensus judgment predates a newer release. **(3)** competing hypotheses incl. the null (CURN, not HD). **(4)** `domain-expert-pta` supplies conventions + the *human-authored* scope/significance backstop ("amplitude alone is not HD evidence"); `analyst-coder` goes to the release dataset DOIs via `enterprise`/`PTArcade` over `.par`/`.tim`/noise products for the actual spectral fit (the catalog cache holds summary `A_gwb`/`gamma`, not full posteriors). **(5)** results with asymmetric uncertainty + assumptions (power-law, BayesEphem). **(6)** `interpreter` labels M/I/S using `measured_vs_inferred`: residuals = measured; `A_gwb`/`gamma` = inferred under a power-law model; SMBHB-vs-strings = speculative. **(7)** `skeptic` runs `skeptic_threats`: ephemeris systematics, pulsar-noise mismodeling, look-elsewhere on HD significance, and the `open_limits` flag that the source class is not yet distinguished. **(8)** `cross-domain-bridge` → SMBHB demographics, cosmic strings, LISA complementarity (may explicitly request a second pack's expert). **(10)** `next-steps`: more pulsars / longer baseline / IPTA-DR3 to sharpen `gamma` against `13/3`. Honest conclusion, licensed by `open_limits`: *the data does not yet distinguish the source class.* Every cached number is provenance-stamped; the live computation is reproducible (pinned env/seeds, logged source DOIs). The Tier-1 answer's fabrication rate is *eval-measured* (per-pack, release-gated), not categorically guaranteed (§6).

---

## 10. Open questions / risks (genuinely unresolved)

These are not deferred design work; they are issues the architecture **cannot fully close** and chooses to name rather than hide.

1. **Does Praxis-with-teeth actually generalize to *science*, or only to API-/rederive-backed fields?** The mechanical cache-integrity guarantee exists only for tier-LIVE and tier-REDERIVE. Most of science (much of biology, chemistry, condensed matter) has no single queryable catalog and lands in tier-ASSERTED — method loop + discipline, but no machine oracle and no mechanical guarantee. The honest scope of the "generalize to science" framing depends on how large the LIVE/REDERIVE set is, and we have not measured it. The tier banner makes the limitation visible per pack, but it does not make the set bigger.

2. **Tier-1 answer-time fabrication is irreducibly stochastic.** `pcache.py` mechanically enforces Tier-0 serving, but deep-loop synthesis is prose-steered and empirically fabricates ~11% even in the tuned GW pack (`provenance 0.889` in this repo's own `aggregate.json`). No design makes Tier-1 categorically non-fabricating; only per-pack eval-gating (`provenance ≥ threshold`). The "mechanically enforced" headline is true for cache + Tier-0 and *false* for Tier-1 — we scope the claim accordingly, but the residual risk is real.

3. **An auto-generated domain expert can be fluent-but-wrong, and in tier-ASSERTED fields no one — neither a gate nor a non-expert user — can catch it.** The mitigations (BLANK judgment slots that block gate 9, named `expert_attestation`, adversarial self-test against the oracle, drift-check on every pack) all assume either an oracle or a real domain expert at Checkpoint B. For tier-ASSERTED fields the self-test has no oracle and the ratifier may be a non-expert; a hallucinated convention (a fabricated analog of `gamma=13/3`) is then undetectable by the system. This is the deepest unresolved risk: the "add a domain with one command" story is really "find a domain expert, run a costly loop, have them author the hard parts, hope a non-expert can ratify the rest."

4. **Staleness of human-judgment fields has no automated freshness signal for non-API domains.** tier-LIVE packs ping a `latest_release_probe`; tier-REDERIVE/ASSERTED have nothing to ping. `sota.json` `status` (contested/convergent) and `open_limits` can rot into confidently-outdated "the data does not yet distinguish" conclusions. The only lever is a conservative **hard-expiry**, and choosing it trades false-stale (refusing a still-valid cache) against confidently-outdated (serving a superseded judgment). There is no principled value; it is a guess per field.

5. **Copyright / ToS posture of redistributing paper extractions in marketplace plugins is a legal/policy question, not just engineering.** The citation-index-by-default design (DOI + own characterization, extraction fetched live) plus the open-license gate plus the `corpus_license` attestation reduce exposure, but whether the citation-index-only fallback preserves enough deep-loop value — and whether bulk DOI HEAD-resolution and Phase-H scraping by *arbitrary third-party* pack authors stays within publisher ToS — likely needs counsel and an explicit marketplace policy. Unresolved.

6. **Bootstrap cost/time is unquantified.** Whether "the one expensive step" is $5 or $200, 2 minutes or 30, and whether the SDK context window survives a 10–30-paper extraction loop, is unknown until measured. The "cheap N packs" economics rest on a number nobody has put on the table. The two-phase/transactional/resumable design contains the *failure* cost, but not the *expected* cost. Init prints an estimate-and-confirm; we still owe a measured budget per tier.

7. **Zero-config single-pack UX vs safe multi-pack routing is a genuine tension, not a solved problem.** The resolver forces disambiguation on scope-sensitive questions (superlatives / "ever" / "observed") when ≥2 packs are installed, which erodes the "zero config" feel exactly when it matters most. We resolve it by assuming single-pack is the common case (true for the judge/demo path) — but a heavy multi-domain user pays a recurring disambiguation tax, and we have not found a way to make cross-domain vocabulary overlap safe *without* that tax.

---

**Net effect:** today's `domain-expert-gw.md` + `gwosc-data/` become the *first instance* of a typed, CI-checkable contract rather than the spine; the spine becomes a reusable, dependency-pinned core with convention-driven runtime resolution. Cache integrity (no fabrication into the cache, provenance-stamped, asymmetric uncertainty, scope discipline, completeness, DOI-resolvable) is enforced **mechanically** by `pvalidate.py` gates + the Tier-0 serving filter across every pack — and the architecture is honest about the three places that guarantee stops: Tier-1 free generation (eval-gated, not categorical), tier-ASSERTED no-oracle fields (discipline, not guarantee), and human-judgment staleness in non-API domains (hard-expiry, not detection).

**Key absolute paths for implementation:**
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/skills/scientific-method/SKILL.md` (line 44 hook + stage 4)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/agents/principal-investigator.md` (lines 10,16) + the 6 GW-tokened generic agents (de-GW pass, §8 Step 2)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/commands/{investigate.md,quick.md,event.md}` (event.md → pack; others re-skin)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/rules/scientific-integrity.md` (generalize rule 9)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/skills/gwosc-data/query_snapshot.py` → `praxis-core/lib/pcache.py` (+ Tier-0 serving filter + serve-time staleness)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/skills/gwosc-data/build_snapshot.py` → `praxis-core/lib/pbuild.py` (+ resumable + completeness) + `praxis-gw/cache/build.py`
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/skills/gwosc-data/data/gwtc_snapshot.json` → `praxis-gw/cache/gwtc_snapshot.json` (rename `events→entities`, `catalog_dois→dois`, `umbrella_catalog→cumulative_scope`; FIX the two empty `catalog_dois` strings first, §8 Step 0)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/eval/score.py` (factor `score_answer` into `praxis-core/eval/score_core.py` + a pack `DomainScorer`; live-GWOSC diff `GWOSC_BASE`~80 / fabrication check~413 → `praxis-gw/oracle/gwosc_oracle.py` at tier LIVE)
- `/Users/ubhardwaj/work/anthropic-ethai-hackathon/praxis/.claude-plugin/{plugin.json,marketplace.json}` (split into praxis-core + per-pack, with tier/license/attestation fields)
