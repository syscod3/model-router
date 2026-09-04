---
title: Establish the baseline regression contract
labels: [wayfinder:task]
parent: ../map.md
status: closed
assignee: hermes-agent
blocked_by: []
---

## Question

What focused automated baseline must pass before refactoring the existing single-file router, covering classification, `/auto`, `/t1`–`/t5`, manual `/model` pinning, configuration loading, and tool-error escalation?

This ticket produces the regression boundary, not the router redesign.

## Resolution

The baseline is a small `pytest` suite in [`tests/test_baseline.py`](../../../../tests/test_baseline.py). It locks the existing five-tier contract, T1 acknowledgement fast path, explicit tier selection, session pin/unpin behavior, and two-consecutive-tool-error escalation. It does not make real provider calls.
