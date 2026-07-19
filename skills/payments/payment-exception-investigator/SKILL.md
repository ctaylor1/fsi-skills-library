---
name: payment-exception-investigator
description: >-
  Investigate ISO 20022 payment exceptions and investigation cases (pacs.008/pacs.002/pacs.004
  and camt.056/camt.029): emit a durable case_id, build a cited message chronology, trace status
  and reason codes, resolve parties and amounts, compute a documented priority, and recommend a
  disposition (repair, return, honor/reject a recall, request information) or route to a
  specialist. Use when a payments investigations or operations analyst works an exception or
  investigation queue, a returned/rejected wire, ACH, SEPA, or RTP payment, or an incoming
  recall, and needs an audit-ready evidence bundle with recommended next steps. HARD BOUNDARY:
  evidence and recommendations only — it never moves funds; repairs, returns, releases, reissues,
  or resubmits a payment; sends a camt.029/pacs.004/pacs.002 response; closes a case; makes a
  determination; or files. Fund movement routes to payment-repair-assistant, and every next step
  requires human adjudication and approval.
license: MIT
compatibility: Amazon Quick Desktop; requires investigations/case-management, payment-message-store (pacs/camt), ISO 20022 external code sets, correspondent/counterparty reference, and screening/repair-rule MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Investigate & casework"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments investigations / operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Exception Investigator

## Purpose and outcome
Take a payment exception (a rejected/returned/recalled/non-delivered ISO 20022 payment) and
produce an **audit-ready case**: a durable `case_id`, a cited message chronology, resolved
parties and amounts, the traced status and reason code, a documented priority, and a
**recommended** disposition with the evidence a human needs to adjudicate it. The outcome is an
evidence bundle and next-step recommendation — the substantive decision (repair, return, recall
response, closure) stays with the payments approver and the downstream execution skill.

## Use when
- "Investigate this rejected/returned payment and build the chronology."
- "We received a camt.056 recall — work the case and recommend honor or reject."
- "Assemble the evidence bundle (parties, amounts, status, citations) for this investigation case."
- "Why is this exception stuck, what does reason code AC04/RR04/DUPL mean, and what next?"

## Do not use
- **First-line, single-payment diagnosis** ("why did this bounce, quickly") → `payment-failure-diagnoser`.
- **Decoding raw pacs/camt XML** into fields → `iso-20022-message-interpreter`.
- **Executing** a repair/return/resubmission or moving funds → `payment-repair-assistant` (after approval).
- **Sanctions/fraud adjudication** → `sanctions-match-adjudicator` / `payment-fraud-case-investigator`.
- **Reconciliation / settlement breaks** → `transaction-reconciliation-helper` / `settlement-break-reconciler`.
- Any request to **close a case, move money, send a scheme response, determine, or file** → refuse; recommend and route.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). Diagnosis and message interpretation are
**upstream**; repair execution and specialist adjudication are **downstream**. This skill emits a
durable `case_id` + evidence bundle once and must not perform the upstream triage or the
downstream money movement.

## Inputs and prerequisites
- The exception(s) with `exception_id`, `case_ref`, `exception_type`, `scheme`, payment
  identifiers (uetr/instruction/e2e/txn), amount, masked parties, and the pacs/camt `messages`
  (type, direction, timestamp, status, reason_code, `msg_ref`); optional `open_cases`, `as_of`,
  and `sanctions_hold`/`fraud_indicator`/recall consent flags. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- Read access to investigations/case-management, the payment message store, the versioned ISO
  code set, correspondent/counterparty reference, and screening/repair rules.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The investigations/case system is the
system of record for case state; the payment message store is authoritative for status and
chronology. Cite every evidence item. Reason-code meanings and screening/priority rules are
**versioned contracts** (`reason_code_set_version`, `config_version`).

## Workflow
1. **Validate & normalize** — run `validate_input`; if there are no messages (no chronology) or
   no payment identifier, stop at `needs-data` and list what is missing (never guess to clear it).
2. **Build the case (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): emit `PEI-<id>`, sort
   messages into a cited chronology, trace last status + reason code, resolve parties/amounts, and
   compute the documented priority band.
3. **Apply precedence** — routing overrides (fraud/sanctions) → `possible-duplicate` link →
   recall (camt.056) handling → reason-code mapping → request-information fallback. See
   [references/domain-rules.md](references/domain-rules.md).
4. **Recommend, do not decide** — set exactly one recommendation disposition with a rationale that
   cites the reason code, and mark `requires_approval: true`. Fund movement, the camt.029 response,
   and closure are proposals for a human and the downstream skill.
5. **Route where needed** — sanctions/regulatory → `sanctions-match-adjudicator`; fraud →
   `payment-fraud-case-investigator`; approved repair/return execution → `payment-repair-assistant`.
6. **Never close, never move funds.**

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py) after.
The output screen enforces: durable `case_id` on every record; recommendation-only dispositions
with `decision_authority: human-adjudication-required`; every evidence item cited; specialist
routes resolve to a known skill; priority band ties out to the score under the same priority
thresholds and fraud/sanctions risk override the builder used; and no closure / determination /
fund-movement / filing language. Fail closed on any miss.

## Human approval
`required`. This skill proposes and packages; humans adjudicate. Every camt.029 recall response,
return, repair, resubmission, release of funds, case closure, and system-of-record change needs
the payments approver and (for execution) `payment-repair-assistant`.

## Failure handling
- **No messages / no identifier** → `needs-data` with an explicit list; no chronology invented.
- **Conflicting case vs. message state** → cite both; fail closed to `needs-data`.
- **Ambiguous duplicate** → `possible-duplicate` linked for human confirmation; never auto-merge.
- **Sanctions/fraud signal** → route to the specialist; do not adjudicate or recommend a repair.
- **Unknown reason code** → `recommend-request-information`; do not infer an action.
- **Tool timeout** → return the partial bundle with an explicit incomplete flag; assume no retry.

## Output contract
1. **Queue view** — per exception: `case_id`, `priority_band`, disposition (recommendation),
   one-line cited rationale.
2. **Evidence bundle** (per investigated exception) — scheme, identifiers, parties (masked),
   amount, cited chronology, last status + reason, linked cases, citations, priority band.
3. **Recommendation** — disposition, rationale citing the reason code, recommended next action,
   `requires_approval: true`, and any specialist route.
4. **Needs-data list** — exactly what is missing.
5. **Machine-readable** — the investigation records + bundles keyed by `case_id`.
6. **Standing note** — "Investigation evidence and recommendations only; no case has been closed,
   no determination made, no payment repaired, returned, or released, and no filing performed.
   Every next step requires human adjudication and approval."
See [references/controls.md](references/controls.md).

## Privacy and records
**Highly Confidential (customer NPI/PII; cardholder data).** Mask debtor/creditor account and
name identifiers to what the evidence requires. Retain investigation records, bundles, citations,
and the `reason_code_set_version` / `config_version` per payments recordkeeping. Log analyst
identity on every read, recommendation, and route.

## Gotchas
- **Recommend ≠ execute.** A repair or return recommendation is not a payment; the money moves
  only in `payment-repair-assistant` after approval.
- **A recall request is not a recall.** camt.056 asks; the camt.029 answer is a human decision —
  never sent from here.
- **Dedup links, never merges.** A `possible-duplicate` points to the open case; the owner confirms.
- **Risk signals win.** A fraud indicator or sanctions/regulatory reason routes to the specialist
  even if the field looks trivially repairable.
- **Codes are versioned.** Record the ISO code-set and config versions so the recommendation is
  reproducible and reviewable.
- **Scheme windows matter.** Recall/return eligibility is time-boxed by the scheme rulebook; capture
  `as_of` and cite it.
