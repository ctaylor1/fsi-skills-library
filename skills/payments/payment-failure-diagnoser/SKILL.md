---
name: payment-failure-diagnoser
description: >-
  Trace a failed, rejected, returned, or stuck payment across its lifecycle (initiation,
  authorization, routing, messaging, screening, clearing, settlement), interpret each
  rail's status and reason codes (ISO 8583 card response codes, NACHA ACH return codes,
  ISO 20022 pacs.002 status-reason codes), identify the most likely root cause, and suggest
  a safe downstream route (exception investigation, message interpretation, repair, dispute,
  or customer remediation). Use when a consumer, merchant, or payments-operations analyst
  asks "why did this payment fail / bounce / get rejected / return", "what does reason code
  R10 / AC04 / 51 mean", "why is this wire stuck", or needs an end-to-end payment trace with
  a root-cause read. This skill diagnoses and routes only; it NEVER repairs, resubmits,
  reverses, releases, cancels, refunds, or authorizes a payment, and NEVER makes a
  fraud/sanctions determination — those are human/authorized-system or downstream-skill actions.
license: MIT
compatibility: Amazon Quick Desktop; requires payment gateway/processor/acquirer, fraud-platform, settlement, network-rules, ISO 20022 parser, case-management, and ledger MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Guidance or domain-expertise skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Consumer / merchant / payments operations analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Payment Failure Diagnoser

## Purpose and outcome
Given a single payment's lifecycle trace (the ordered legs it moved through and the status /
reason code at each), reconstruct **where** it stopped, **interpret** the rail-specific
status and reason codes in plain language, determine the **most likely root cause**, and
emit a **diagnosis pack** with a deterministic **suggested route** and a `retry_eligible`
read. A successful output lets a consumer or merchant understand why a payment failed, or
lets a payments-ops analyst hand a clean, cited trace to the right exception, repair,
dispute, or investigation workflow — without the diagnoser itself touching the payment.

## Use when
- "Why did this payment fail / bounce / get rejected / get returned?"
- "What does reason code `R10` / `AC04` / `51` / `RC01` mean for this payment?"
- "This wire (pacs.008) is stuck — where did it stop and why?"
- "Trace this ACH/card/RTP/SEPA payment end to end and tell me the likely cause."
- An analyst needs a consistent, cited failure trace to attach to an exception case.

## Do not use
- The user wants the payment **repaired / resubmitted / re-presented / cancelled** →
  `payment-repair-assistant` (R4, approval-gated). This skill never modifies a payment.
- A **stuck / ambiguous / screening-held** payment needs substantive **investigation to
  disposition** (beneficiary follow-up, network trace, recall handling) →
  `payment-exception-investigator` (R3).
- The user needs a **field-level ISO 20022 message parse / validation** (element-by-element,
  schema, code-set lookups beyond the failure read) → `iso-20022-message-interpreter`.
- The failure is actually an **unauthorized / disputed** transaction (chargeback territory)
  → `chargeback-dispute-packager` (merchant) or `dispute-operations-assistant` (issuer/acquirer).
- Suspected **payment fraud** needing device/beneficiary-network investigation →
  `payment-fraud-case-investigator`. This skill flags the pattern; it never determines fraud.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill emits a cited diagnosis pack
with a durable `diagnosis_id` and a single suggested route; downstream investigation, repair,
dispute, and message-interpretation skills consume it. It must not duplicate their
disposition, repair, or filing steps.

## Inputs and prerequisites
- Payment identifier and the **lifecycle trace**: an ordered list of legs, each with a
  `stage`, `status`, optional `reason_code`, `timestamp`, and `source_ref`. Rail is one of
  `card` (ISO 8583), `ach` (NACHA), `iso20022` (pacs/pain/camt), `wire`, `rtp`.
- Enough legs to establish where the payment halted (initiation through the terminal leg).
- Read access to gateway/processor/acquirer, settlement, and the network-rules / code-set
  reference (see [references/domain-rules.md](references/domain-rules.md)). Schema and checks:
  [scripts/validate_input.py](scripts/validate_input.py).

## Source hierarchy
See [references/source-map.md](references/source-map.md). The processor/scheme trace is the
position of record for what happened; the settlement/ledger record confirms whether value
actually moved; the versioned network **code set** resolves each reason code's meaning. Cite
every leg and the decisive reason code to a source ref. Never substitute a customer
assertion for the scheme/settlement record.

## Workflow
1. **Scope & validate** — confirm the payment and rail; load the trace; run `validate_input`.
   Fail closed on structural gaps; note data-quality warnings (no timestamps, unknown codes).
2. **Interpret legs (deterministic)** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py) to look up each
   leg's status/reason code against the bundled, versioned code set (ISO 8583 / NACHA /
   ISO 20022), producing a plain-language meaning and a **root-cause category** per leg.
3. **Locate the halt & root cause** — identify the decisive leg (settled, the last failing
   leg, or a stuck/pending terminal), and its root-cause category with cited evidence.
4. **Suggest a route (deterministic)** — map the root-cause category to exactly one route
   per the documented table in [references/domain-rules.md](references/domain-rules.md), and
   set `retry_eligible` from the same mapping. This is a **triage suggestion for a human**,
   not an instruction to act.
5. **Write the pack** — halt stage, interpreted trace, root cause + evidence, suggested
   route, `retry_eligible` with rationale, and explicit **cautions** (e.g. confirm no prior
   settlement before any re-presentment) plus the standing disclaimer.

## Validation loop
Run `validate_input` before and [scripts/validate_output.py](scripts/validate_output.py)
after. The output check confirms: the root cause is cited; every reason-coded leg is
interpreted; the suggested route and `retry_eligible` equal the deterministic mapping from
the root-cause category; no repair/reversal/refund/release or fraud/sanctions-determination
language is present; the standing disclaimer is present; and cautions exist whenever a
duplicate/re-presentment or screening-hold risk applies. Fail closed on any miss.

## Human approval
`external-delivery`: human review is required before the diagnosis is sent to a customer or
written to a case/system of record. No approval is needed for the analyst's own read. The
skill never takes a payment action and never triggers a downstream repair/investigation on
its own — routing is a suggestion a human accepts.

## Failure handling
- **Incomplete trace** (missing legs / no terminal status) → report what is known, mark the
  trace `incomplete`, and route to investigation rather than guessing a root cause.
- **Unknown / unmapped reason code** → interpret category as `unknown`, keep the raw code,
  and route to `payment-exception-investigator` (or `iso-20022-message-interpreter` if the
  message itself is unparseable). Never invent a meaning.
- **Ambiguous payment identity** → stop and confirm; never trace the wrong payment.
- **No timestamps** → interpret status/reason codes but flag that ordering and stuck-in-flight
  detection are limited.
- **Conflicting sources** (scheme says rejected, ledger shows a debit) → cite both and route
  to investigation; do not resolve silently.
- **Tool timeout** → return the legs interpreted so far with a clear `incomplete` flag.

## Output contract
1. **Summary** — payment (masked), rail, amount/currency, halt stage, terminal status,
   root-cause category, suggested route, `retry_eligible`.
2. **Trace** — per leg: stage, status, reason code, plain-language meaning, category,
   cited `source_ref`.
3. **Root cause** — the decisive category + code + meaning + evidence citation.
4. **Route & retry** — the single suggested downstream route and the `retry_eligible` read
   with rationale.
5. **Cautions** — duplicate/re-presentment, screening-hold, and repair-is-downstream notes.
6. **Data gaps / unknown codes.**
7. **Machine-readable** — the trace + root cause + route + `diagnosis_id` for downstream skills.
8. **Standing disclaimer** — "Diagnostic assessment only; not a payment instruction, repair,
   or fraud/sanctions determination. No payment has been modified, resubmitted, reversed, or
   released."
See [references/controls.md](references/controls.md).

## Privacy and records
Highly Confidential (customer NPI/PII; cardholder data). Mask PAN/account numbers to last 4;
never emit a full PAN, and never emit CVV/track/PIN data. Minimize customer data to what
evidences the root cause. Retain the diagnosis + citations + code-set version per records
policy; log the read and any external-delivery approval. Never exfiltrate cardholder or
customer data.

## Gotchas
- **A reason code is not a verdict.** `59`/`AC06`/`RR04` describe a scheme/bank response;
  they are not a fraud or sanctions determination — describe them factually and route.
- **Rejected ≠ no money moved.** Confirm against settlement/ledger; a reject after a debit,
  or a return of an already-settled item, is an investigation case, not a simple retry.
- **Duplicate risk on timeouts.** `91`/`96`/pending-in-flight can mean the payment *did*
  complete downstream — never imply re-presentment without confirming no prior settlement.
- **Repair is downstream and gated.** Even an obviously fixable `RC01`/`AC01`/`R04` is
  repaired by `payment-repair-assistant` (R4, human-approved), never here.
- **Code sets are versioned contracts.** ISO 20022 external code sets and scheme response
  codes change; the diagnosis records the code-set version used so it is reproducible.
- **Rail matters.** The same digits mean different things per rail (`R10` ACH ≠ card `10`);
  always resolve the code within the declared rail's code set.
