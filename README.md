# Praxis

**The natural scientist's harness for Claude.** Everything-Claude-Code, but the operator is an ideal natural scientist instead of a software engineer.

Most "AI for science" turns the model into a single oracle you ask for an answer. Praxis instead configures Claude as a small lab that runs the **scientific method** explicitly: frame a falsifiable question, establish background from real literature, get the method right, compute on real data, interpret, *try to break the result*, connect it across fields, and map what to do next. The result is an investigation with provenance and uncertainty — not a confident paragraph.

## Core + packs

- **`praxis` (core)** is **domain-agnostic**: the method loop, the 8 scientist-roles, the integrity rules, and a typed **cache engine** (`lib/pcache.py` query · `lib/pbuild.py` build · `lib/pvalidate.py` the 11 contract gates). It runs the scientific method on *any* field, with no pack installed.
- **Domain packs** (`packs/<id>`) make it a fluent **expert** co-scientist on one field — a domain-expert agent, a `<id>-data` retrieval skill, a provenance-stamped cache, an oracle at a declared capability **tier**, and a domain eval suite. Shipped: **`lvk`** (ground-based gravitational waves — the "Siren" pack, tier **LIVE**) and **`pta`** (pulsar timing arrays, tier **REDERIVE**).

```
/init lvk    # one-time: caches the plugin + pack into memory -> a fluent LVK co-scientist
/quick most massive black hole merger so far
/investigate "Is GW190814's secondary a neutron star or a black hole?"
```

## Integrity, with teeth (and honest about its limits)

Cache integrity is **mechanically enforced**: `pvalidate.py` gates certify each pack's cache is complete, DOI-resolvable, uncertainty-bearing, and scope-landable; `pcache.py`'s serving filter refuses to emit a bare number or a value without provenance. The **oracle tier** is a hard capability, not a label: **LIVE** packs are diffable against an independent API; **REDERIVE** packs are byte-match re-derivable but carry no live oracle and, until a human audit, are flagged *community-unverified*; **ASSERTED** fields get the method + discipline but not the mechanical guarantee. Tier-1 deep-loop generation is **eval-gated, not categorically guaranteed** — the honest scope is stated in `ARCHITECTURE.md`.

## The lab (roles → agents)

`principal-investigator` orchestrates · `literature-reader` reads papers · `domain-expert-<id>` supplies field physics (from the active pack) · `analyst-coder` runs reproducible analysis · `interpreter` turns numbers into meaning · `skeptic` tries to break the result · `cross-domain-bridge` connects fields · `teacher` explains at any level · `next-steps` maps the forward agenda.

## Docs

- `INSTALL.md` — install, `/init`, usage
- `ARCHITECTURE.md` — the full typed core/pack contract, oracle tiers, and the honest limits
- `docs/index.html` — the single-page documentation site (GitHub Pages)

## Add a domain

`/praxis-build <domain>` runs the transactional two-phase bootstrap and stamps out a validated `packs/<id>`. The method loop and integrity rules are domain-agnostic — that's the point.

---
*polygrav · Anthropic–ETH AI Sprint.*
