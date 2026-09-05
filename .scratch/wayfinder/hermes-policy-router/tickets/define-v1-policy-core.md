---
title: Define the V1 policy-core contract
labels: [wayfinder:grilling]
parent: ../map.md
status: closed
assignee: hermes-agent
blocked_by: [verify-hermes-routing-seam.md, discover-provider-model-contract.md]
---

## Question

Given the verified Hermes seam and available provider contract, what is the smallest policy-core API and configuration schema that preserves five-tier classification while separating availability failover, capability escalation, PAYG overflow, and hard manual pins?

## Resolution

`model_router` is now a pure policy package. `Candidate`, `Tier`, `CandidateHealth`, `RoutingSession`, and `RoutingDecision` are provider-neutral values. `RoutingPolicy.select_tier(...)` handles capability-tier and manual-pin selection; `select_candidate(...)` delegates only same-tier ordering. Legacy `model: provider/model` configuration becomes a one-candidate pool. Health, overflow, escalation, and Hermes mutation remain separate follow-on modules.
