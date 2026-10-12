---
name: simulation-based-inference
description: When and how to use simulation-based inference (SBI / likelihood-free inference) instead of stochastic sampling, and how to validate it before any scientific use. Use for inference problems with an intractable or expensive likelihood, amortized inference over many events, or when classical sampling is too slow — and always before trusting an SBI posterior.
---

# Simulation-based inference

SBI estimates a posterior from a simulator instead of an explicit likelihood. It shines for amortized inference (train once, infer on many datasets fast), intractable-likelihood problems, and population/hierarchical inference. It is powerful and easy to fool yourself with — validation is not optional.

## When SBI is the right tool

- The likelihood is intractable or only available through a simulator.
- You need the *same* inference repeated over many events → amortize: pay training cost once, get near-instant posteriors.
- Classical stochastic sampling (MCMC / nested sampling) is too slow for the throughput you need.

When a tractable likelihood exists and runtime is acceptable, classical sampling is often the safer default. Choose deliberately and say why.

## Methods (brief)

- **NPE** (neural posterior estimation): learn `p(θ|x)` directly; fast at inference.
- **NLE / NRE** (likelihood / ratio estimation): learn the likelihood or a ratio, then sample. Useful when the likelihood object itself is wanted.
- Tooling: `sbi`, `lampe`, normalizing flows in `torch`/`jax`.

## Validation — mandatory before any scientific claim

An SBI posterior that has not passed these is not evidence:

- **Simulation-based calibration (SBC)** / **coverage**: do the credible intervals have their stated frequentist coverage? Rank statistics should be uniform.
- **P–P plots**: empirical vs nominal credible levels lie on the diagonal.
- **Posterior predictive checks**: simulations drawn from the inferred posterior look like the observed data.
- **Out-of-distribution caution**: an amortized network is only trustworthy on data resembling its training prior/coverage. State where it stops being valid.

If validation fails, the posterior is wrong even if it looks tight and plausible. Report the validation diagnostics alongside the result — the skeptic agent will ask for them.
