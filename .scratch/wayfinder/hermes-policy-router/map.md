---
title: Hermes Policy Router — Wayfinding Map
labels: [wayfinder:map]
tracker: local-markdown
---

## Destination

Deliver a working V1 fork of `model-router` that routes each Hermes turn by capability tier, uses same-tier capacity fallback before budget-controlled PAYG overflow, and escalates tiers only for demonstrated capability failure.

## Notes

Execution is included in this map. Preserve the existing five tiers, `/auto`, `/t1`–`/t5`, profile configuration, WebUI integration, and tool-error escalation where they fit the new policy. Keep all live-Hermes access behind `integrations/hermes.py`. Consult `hermes-agent`, `research`, and `domain-modeling` when resolving tickets.

GitHub Issues are disabled on this fork, so this map uses the repository-local Markdown tracker under `.scratch/wayfinder/hermes-policy-router/`.

## Decisions so far

- [Verify Hermes provider-switching and error-hook seam](tickets/verify-hermes-routing-seam.md) — Hermes has no native per-turn route-selection hook; the adapter must use `AIAgent.switch_model(...)` until a supported override exists. See [research](../../../docs/research/hermes-routing-seam.md).
- [Discover the usable provider and model contract](tickets/discover-provider-model-contract.md) — use canonical provider slugs; bootstrap model names remain configurable placeholders until Hermes discovery returns account-usable IDs. See [research](../../../research/provider-model-contract.md).
- [Establish the baseline regression contract](tickets/establish-baseline-regression-contract.md) — five focused tests now protect classification fast paths, explicit tier selection, config normalization, pins, and tool-error escalation before refactoring.

## Not yet specified

- The smallest test seam that proves provider switching without real-provider quota use.
- Whether OpenRouter's coding/general routers meet the V1 overflow contract after fixed overflow works.
- WebUI badge changes after the policy core and adapter are working.

## Out of scope

- A standalone LLM proxy, LiteLLM, Redis/Postgres, proactive provider probes, dynamic model quality inference from price, and changes to Hermes authentication.
