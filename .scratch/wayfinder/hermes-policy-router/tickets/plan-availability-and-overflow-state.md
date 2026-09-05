---
title: Plan shared availability state and fixed overflow
labels: [wayfinder:grilling]
parent: ../map.md
status: open
assignee: hermes-agent
blocked_by: []
---

## Question

How should V1 represent shared candidate health, classify API failures, persist cooldowns in SQLite WAL, and select only fixed budget-approved OpenRouter or DeepInfra overflow candidates before applying the exhausted-tier policy?

Dynamic catalog price sorting is explicitly excluded from this decision.
