---
title: Verify Hermes provider-switching and error-hook seam
labels: [wayfinder:research]
parent: ../map.md
status: open
assignee: hermes-agent
blocked_by: []
---

## Question

What supported or currently available Hermes hooks, live-agent fields, and error-hook payloads can a plugin use to change provider, model, and reasoning for a turn; receive structured API failures; and detect native per-turn overrides if they exist?

Record exact source locations and a recommended minimal adapter boundary for `integrations/hermes.py`. Do not modify Hermes itself.
