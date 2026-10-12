# Install & Usage

## Install (Claude Code)

Praxis is a **core plugin + domain packs**. Install the core, then one or more packs.

```
/plugin marketplace add https://github.com/<you>/praxis
/plugin install praxis@praxis          # the domain-agnostic core
/plugin install praxis-lvk@praxis      # ground-based gravitational waves (Siren)
/plugin install praxis-pta@praxis      # pulsar timing arrays (optional)
```

For local testing without the marketplace (core first):

```
claude --plugin-dir praxis --plugin-dir praxis/packs/lvk
claude plugin validate .               # pre-flight
python lib/pvalidate.py packs/lvk packs/pta   # the contract gates
```

## Prime it (one-time, a few minutes)

```
/init lvk        # reads the plugin + the lvk pack, caches an expert briefing into memory
```

`/init` writes a compact briefing (the method loop + roles + integrity rules, and the pack's conventions / scope-traps / data-paths / landmark DOIs) into Claude's persistent memory and sets the active pack. Afterward every session operates as a fluent domain expert without re-reading. **Core works without `/init`** — it just runs as a generalist co-scientist on any field.

## Use

```
/quick most massive black hole merger so far        # Tier-0: cited, offline, no loop
/event GW150914                                      # (lvk) full Siren brief on a real event
/investigate "Is GW190814's secondary a NS or a BH?" # full method loop, skeptic-checked
/praxis-use pta                                      # switch active domain
/praxis-packs                                        # list packs + freshness + tier
```

Or just ask a scientific question — the `scientific-method` skill triggers and routes the loop.

## What runs

`/investigate` drives the loop: frame question → `literature-reader` (background) → `domain-expert-<id>` (method) → `analyst-coder` (real compute on the pack's clients) → `interpreter` (meaning) → `skeptic` (try to break it, mandatory) → `next-steps` → `teacher`. Tier-0 lookups skip the loop and serve from the pack's cache via `lib/pcache.py`.

## Rules of use

- Demand provenance: every number carries a retrieved source identifier + uncertainty. No source = reject it.
- Feed it open, falsifiable questions for `/investigate`; use `/quick` for lookups.
- The skeptic pass is never skipped.
- Oracle tiers are honest: **LIVE** (lvk) has a live-API ground truth; **REDERIVE** (pta) is re-derivable but has no live oracle and, until a human transcription audit, is flagged *community-unverified*.

See `rules/scientific-integrity.md` for the non-negotiables, `ARCHITECTURE.md` for the full contract, and `docs/index.html` for the documentation site.

## Add a new domain

```
/praxis-build <domain>    # transactional two-phase bootstrap -> packs/<domain>
```

## Uninstall

```
/plugin uninstall praxis-lvk@praxis
/plugin uninstall praxis@praxis
```
