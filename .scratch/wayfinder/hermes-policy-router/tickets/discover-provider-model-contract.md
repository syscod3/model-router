---
title: Discover the usable provider and model contract
labels: [wayfinder:research]
parent: ../map.md
status: closed
assignee: hermes-agent
blocked_by: []
---

## Question

Which exact provider identifiers, model slugs, and model-list discovery paths are usable in the installed Hermes environment for the bootstrap policy: OpenAI Codex, z.ai, LM Studio, OpenRouter, and DeepInfra?

Record only non-secret configuration facts. Identify placeholders that must remain configurable because the provider cannot expose a reliable local catalog.

## Resolution

Use canonical Hermes provider slugs: `openai-codex`, `zai`, `lmstudio`, `openrouter`, and `deepinfra`. Human-readable bootstrap model names are not valid configuration until a provider discovery result supplies the exact account-usable slug. Details: [`research/provider-model-contract.md`](../../../../research/provider-model-contract.md).
