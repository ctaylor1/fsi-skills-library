# Controls — portfolio-characteristics-change-monitor

- **Risk tier:** R2 — analytical. **Action mode:** Read-only analysis.
- **Human approval:** `external-delivery` — required before the packet goes outside the risk
  function or is written to a case/system of record. Internal analytical use may be
  reviewer-sampled.

## Prohibited (fail closed)

- No **rebalancing** in any form — never direct, recommend, size, stage, or execute a trade,
  reweight, trim, add, or "bring the book back to benchmark". Manager-directed remediation
  belongs to the portfolio manager and `portfolio-rebalancing-assistant`.
- No **limit change** — never set, raise, lower, loosen, widen, relax, modify, override, or
  reset a mandate limit, band, or threshold. The attention bands used here are drift-review
  bands, not mandate limits.
- No **compliance determination** — never assert a portfolio "is in breach", "breaches the
  mandate", or "is in violation". Any characteristic at or near a supplied mandate reference
  is **routed** to `investment-mandate-reviewer`, which is the authoritative limit test.
- No **personalized investment advice** (what to buy/sell/hold) — not licensed advice.
- No **opaque scoring** presented as decisive; every change is an explainable prior→current
  delta with cited evidence, and the priority maps deterministically from the flagged set.

## Required output screens (`scripts/validate_output.py`)

- Every exception has ≥1 cited evidence row (current + prior `source_ref`).
- `suggested_priority` equals the deterministic mapping from the exception set and routing
  (`route_to_compliance` OR ≥ 4 exceptions → Elevated; ≥ 1 → Review; else Informational).
- No rebalancing-direction, limit-modification, breach-determination, or advice language
  (regex screen over narrative + reasons + notes + handoff reason).
- Standing disclaimer present: "Change and exception evidence only; not a rebalancing
  instruction or a compliance determination. No trade, rebalancing, or limit change has been
  made or directed."
- If any characteristic is routed for limit proximity, a **handoff to
  `investment-mandate-reviewer`** is present and covers every routed item (a near/at-limit item
  is never swallowed or self-adjudicated).

## Input contract (`scripts/validate_input.py`)

- Both snapshots must be **approved** (`approval.approved: true`) with a `source_ref`; an
  unapproved/draft snapshot fails closed.
- `prior_as_of` strictly before `as_of`; `config_version` non-empty; at least one
  characteristic evaluable in both snapshots.

## Data classification, privacy, records

- **Highly Confidential (MNPI / client-confidential).** Minimize data in the packet to what
  evidences a change or exception.
- Retain the packet + citations + `config_version` per records policy; log the read and any
  external-delivery approval. Route only to approved risk/compliance queues; never exfiltrate
  holdings, characteristics, or trade intentions.

## Reproducibility

`packet_id` binds the output to the two approved snapshots, their effective dates, and the
`config_version`; re-running with the same inputs and config reproduces the changes,
exceptions, routing, and priority.
