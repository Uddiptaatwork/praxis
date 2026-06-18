# Install & Usage

## Install (Claude Code)

```
/plugin marketplace add https://github.com/<you>/praxis
/plugin install praxis@praxis
```

Verify:

```
/plugin list praxis@praxis
```

Rules aren't distributed by the plugin system. Copy them once:

```
git clone https://github.com/<you>/praxis.git
mkdir -p ~/.claude/rules/praxis
cp praxis/rules/*.md ~/.claude/rules/praxis/
```

## Use

```
/event GW150914                                  # Siren brief on a real event
/investigate "Is GW190814's secondary a NS or a BH?"   # full method loop
```

Or just ask a scientific question — the `scientific-method` skill triggers and routes the loop.

## What runs

`/investigate` and `/event` drive the loop: frame question → `literature-reader` (background) → `domain-expert-gw` (method) → `analyst-coder` (real GWOSC compute) → `interpreter` (meaning) → `skeptic` (try to break it, mandatory) → `next-steps` (what's next) → `teacher` (explain).

## Rules of use

- Enter through a command, not freeform.
- Demand provenance: every number carries a GWOSC source + uncertainty. No source = reject it.
- Feed it open, falsifiable questions, not lookups.
- The skeptic pass is never skipped.

See `rules/scientific-integrity.md` for the non-negotiables.

## Uninstall

```
/plugin uninstall praxis@praxis
rm -rf ~/.claude/rules/praxis
```
