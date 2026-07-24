---
name: order-allocation-validator
description: >-
  Test a PROPOSED trade allocation against the firm's approved allocation policy, client/
  account eligibility, order/allocation timestamps, and documented deviations; produce a
  source-linked exception-evidence packet for a human allocation/compliance reviewer. Use
  when a trade-allocation analyst or trading-compliance officer asks to "check this
  allocation", "validate the pro-rata split", "did this allocation follow policy", or
  "flag allocation exceptions before booking". HARD BOUNDARY: R3 decision-support only — it
  NEVER allocates, re-allocates, amends, books, or approves an order, never overrides
  eligibility or entitlements, and never certifies an allocation as compliant; every
  disposition is a recommendation an authorized human must adjudicate. Routes trade/quantity
  breaks to trade-break-resolver.
license: MIT
compatibility: Amazon Quick Desktop; requires OMS/EMS allocation records, client/account eligibility & entitlements, approved allocation-policy config, and reference-data MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Capital Markets"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Capital Markets operations & compliance"
  aws-fsi-primary-user: "Trade-allocation analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Order Allocation Validator

## Purpose and outcome
Given a **proposed** allocation of an executed order across client accounts, deterministically
test it against the approved allocation policy (method, tolerance, deviation rules), account
eligibility/entitlements, and order/allocation timestamps; surface every exception with cited
evidence and a suggested review disposition. A successful output lets an allocation or
compliance reviewer decide — the allocation decision and any booking remain the human's.

## Use when
- "Validate/check this allocation", "did the pro-rata split follow policy".
- "Flag allocation exceptions before we book", "is this account eligible for this allocation".
- A reviewer needs a consistent, cited allocation-exception packet.

## Do not use
- The user wants you to **allocate, re-allocate, amend, or book** an order → out of scope; the
  human/OMS acts.
- There is a **quantity/trade break** between systems (fills don't reconcile) → route to
  `trade-break-resolver`.
- Best-execution/venue quality review → `best-execution-reviewer`.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Emits an exception packet with a durable
`validation_id`; it does not allocate or resolve breaks itself.

## Inputs and prerequisites
- The **proposed allocation**: order (id, security, executed qty, avg price, timestamp) and
  per-account lines (account_id, proposed qty, participation/target basis, eligibility flags,
  deviation reason). Schema: [scripts/validate_input.py](scripts/validate_input.py).
- Approved **allocation-policy config** (method, tolerance, deviation-approval rule) — a
  versioned contract. See [references/domain-rules.md](references/domain-rules.md).

## Source hierarchy
See [references/source-map.md](references/source-map.md). OMS/EMS allocation record is the
system of record; eligibility/entitlements from the client system; policy from versioned
config. Cite every exception to a source line + policy rule/version.

## Workflow
1. **Validate input** — run `validate_input`; confirm one order, a single as-of, and required
   fields.
2. **Compute checks (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): quantity tie-out,
   pro-rata (or price-time) target vs proposed per account within tolerance, eligibility, and
   timestamp ordering; each deviation must carry a documented reason.
3. **Assemble exceptions** — per exception: rule, expected vs proposed, evidence line, policy
   version.
4. **Suggest disposition** — `clean` or `exceptions-for-review` (a triage suggestion, not an
   allocation decision).
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py) for
   tie-out, citation coverage, the no-allocation-decision screen, and disclaimer.

## Validation loop
`validate_input` before, `validate_output` after. If quantities don't tie, an exception lacks
a citation, or the text contains allocation/amendment/approval language, **fix or fail closed**.

## Human approval
`required`: no allocation, amendment, booking, or compliance certification without an
authorized human. The skill only evidences exceptions.

## Failure handling
- **Quantity break** (Σ lines ≠ executed qty) → flag and route to `trade-break-resolver`; do
  not adjust.
- **Missing policy/eligibility** → fail closed; state what is missing; do not assume.
- **Undocumented deviation** → flag as an exception, never rationalize it.
- **Stale/conflicting source** → cite both; escalate. **Tool timeout** → partial + incomplete flag.

## Output contract
1. **Summary** — order (masked), policy version, count of exceptions, suggested disposition.
2. **Exceptions** — per exception: account (masked), rule, expected vs proposed, deviation
   reason (or "undocumented"), citation.
3. **Data gaps / not-evaluable checks.**
4. **Machine-readable** — checks + exceptions + `validation_id`.
5. **Standing disclaimer** — "Allocation-exception evidence only; not an allocation decision,
   amendment, or compliance certification. No order has been allocated or booked."
See [references/controls.md](references/controls.md).

## Privacy and records
Customer NPI/PII. Mask account numbers (last 4). Retain the validation + citations + policy
version. Log read + external-delivery approval. Never exfiltrate client/allocation data.

## Gotchas
- **A tolerance breach is an exception, not a decision.** Flag it; the reviewer decides.
- **Rounding**: pro-rata rounding to lot size is expected; distinguish lawful rounding from a
  material deviation using the policy tolerance, not a guess.
- **Timestamps**: an allocation stamped before the fill, or after the batch cutoff, is an
  exception — do not silently accept.
- **"Undocumented deviation" ≠ "prohibited"**: report the missing documentation factually;
  the reviewer determines significance.
