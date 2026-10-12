---
name: playbooks
description: Deep bug-class playbooks (RAG knowledge base). Use when you have a lead — read the matching playbook BEFORE exploiting, and check every playbook against a new target class. Trigger/detect/exploit/PoC/cases per class.
---

# PLAYBOOKS — bug-class knowledge base

This is the fleet's accumulated exploit intelligence. Each playbook is a deep, working recipe for one bug class: where it lives, how to detect it, how to exploit it, the PoC shape, real cases, and kill signals.

## HOW TO USE (mandatory order)
1. When a lead or target arrives, find the matching class below and READ that reference file fully before writing any exploit code.
2. Follow its DETECT steps exactly — they are ordered by signal strength.
3. Use its EXPLOIT + POC SHAPE as the starting skeleton; adapt, don't invent from scratch.
4. Check its KILL SIGNALS before escalating — most false positives die there.
5. If a playbook wins (or a new variant appears), record the case in your output so it can be appended here — the DB grows from verified findings only.

## INDEX (references/)
- `references/accumulator-dos.md` — unbounded accumulation structures → griefing/DoS. [TIER 1]
- `references/authorization-gap.md` — missing/incorrect authorization: origin checks, roles, signatures. [TIER 1]
- `references/accounting-drift.md` — share/balance accounting where rounding/ordering/fees leak value. [TIER 1]

## RETRIEVAL
Grep this skill's references/ dir for keywords from your lead (function names, struct names, error strings) to find the closest class:
`grep -ril "<keyword>" /opt/skills/playbooks/references/`

## GROWTH RULE
One verified finding = one case entry (target, mechanism, root cause, fix, proof). Quality over quantity — a playbook is only as good as its kill signals.
