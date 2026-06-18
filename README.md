# Praxis

**The natural scientist's harness for Claude.** Everything-Claude-Code, but the operator is an ideal natural scientist instead of a software engineer — and the flagship domain is gravitational-wave physics (the **Siren** pack), because that's what we do.

Most "AI for science" turns the model into a single oracle you ask for an answer. Praxis instead configures Claude as a small lab that runs the **scientific method** explicitly: frame a falsifiable question, establish background from real literature, get the method right, compute on real data, interpret, *try to break the result*, connect it across fields, and map what to do next. The result is an investigation with provenance and uncertainty — not a confident paragraph.

## Install (Claude Code)

```
/plugin marketplace add <your-repo-url>
/plugin install praxis@praxis
```

## Use

```
/investigate "Is GW190814's secondary a neutron star or a black hole?"
/event GW150914
```

Or just ask a scientific question — the `scientific-method` skill triggers and the principal-investigator routes the loop.

## The lab (roles → agents)

`principal-investigator` orchestrates · `literature-reader` reads papers · `domain-expert-gw` supplies GW physics · `analyst-coder` runs reproducible analysis · `interpreter` turns numbers into meaning · `skeptic` tries to break the result · `cross-domain-bridge` connects fields · `teacher` explains at any level · `next-steps` maps the forward agenda.

## Skills

`scientific-method` (the master loop) · `paper-reading` · `gwosc-data` (real LVK/GWOSC v2 access) · `simulation-based-inference` (when SBI beats sampling, and how to validate it). Extend during the sprint with `gw-parameter-estimation`, `gw-populations`, `multimessenger`, `uncertainty-and-systematics`, `science-communication`.

## Non-negotiables

`rules/scientific-integrity.md`: no fabricated numbers, retrieve don't recall, always carry uncertainty, separate measurement / inference / speculation, cite real sources, the skeptic pass is mandatory, reproducibility, and it's allowed to conclude the data doesn't answer the question.

## Beyond GW

Siren is the reference instantiation. To target another data-driven field, add a `domain-expert-<field>` agent and a few domain skills (data access + method + conventions). The method loop and the integrity rules are domain-agnostic — that's the point.

---
*Prototype scaffold · polygrav · Anthropic–ETH AI Sprint, 18 June 2026.*
