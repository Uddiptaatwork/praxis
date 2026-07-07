---
name: praxis-use
description: Switch the active Praxis domain pack (writes .praxis/active). Use when several packs are installed and you want to route Tier-0 lookups and the deep loop to a specific field.
---

Switch the active domain pack to: **$ARGUMENTS**

1. Run `python lib/pack_resolver.py list` to see installed packs.
2. If `$ARGUMENTS` matches an installed pack id, write it to `.praxis/active` (create `.praxis/` if needed). Otherwise report the valid ids.
3. Confirm the new active pack with `python lib/pack_resolver.py json` and print its title + oracle tier.
4. Suggest `/init <id>` if `.praxis/primed` does not yet cover this pack, so the domain briefing is in memory.

Note: `PRAXIS_DOMAIN=<id>` (env var) overrides `.praxis/active` for a single session without switching the default.
