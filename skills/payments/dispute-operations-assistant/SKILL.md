---
name: dispute-operations-assistant
description: >-
  Support issuer- and acquirer-side card disputes from the bank's side: verify role and
  transaction identity, validate the network reason code against the CURRENT rulebook version,
  compute the response deadline, check evidence sufficiency, and draft a cited case response
  for a human to adjudicate and submit. Use when an issuer or acquirer disputes analyst needs
  to work a dispute queue, confirm a reason code and its evidence/deadline, assemble evidence,
  or draft a dispute case response for authorized submission. Keywords: card dispute,
  chargeback, reason code, Visa/Mastercard, response deadline, representment (bank side),
  Reg E / Reg Z, provisional credit, dispute case system. HARD BOUNDARY: this skill NEVER
  decides a dispute, accepts or denies a chargeback, issues provisional or final credit,
  assigns liability, makes a fraud finding, submits/files a response, or closes a case — it
  drafts decision-support for a human adjudicator who authorizes any submission.
license: MIT
compatibility: Amazon Quick Desktop; requires card-network rules/bulletins, issuer/acquirer dispute case system, transaction/authorization data, customer/merchant evidence (OMS/core/documents), and controlled-template MCP integrations (all read-only; adjudication and submission are out of scope).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Case agent + evidence bundle"
  aws-fsi-delivery-wave: "Wave 3 - regulated casework"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Issuer / acquirer disputes analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Dispute Operations Assistant

## Purpose and outcome
Turn a raw issuer- or acquirer-side card dispute into an audit-ready, **draft case response**:
verify the role and the disputed transaction's identity, validate the network reason code and
its required evidence against the **current** rulebook version, compute the response deadline,
confirm the supplied evidence is sufficient, and draft a concise, exhibit-cited response from
an approved template. The outcome is a review-ready package (or a clear, itemized reason it
cannot be drafted yet) that a human **adjudicates and submits**. The skill never decides the
dispute, never moves funds, never submits, and never closes a case.

## Use when
- "Work my issuer/acquirer dispute queue; validate the reason codes and deadlines."
- "Is reason code 10.4 / 4853 valid here, what's the response deadline, and is the evidence
  enough?"
- "Assemble the evidence and draft the case response for dispute DC-XXXX for review."
- "Confirm this dispute cites the current network rule version before I respond."

## Do not use
- **Merchant-side** representment / compelling-evidence packaging → `chargeback-dispute-packager`.
- **Fraud determination / fraud-alert investigation** → `payment-fraud-case-investigator`.
- **Interpreting or tracking a network rule change** itself → `network-rules-change-tracker`.
- **ISO 20022** payment exception (camt), not a card dispute → `payment-exception-investigator`.
- **Reconciling** dispute debits/transactions to the ledger → `transaction-reconciliation-helper`,
  `settlement-break-reconciler`.
- Any request to **decide/accept/deny a dispute, issue credit, submit/file, or close a case**
  → refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is bank-side drafting only. It
consumes the current ruleset (`current_rule_version`) from `network-rules-change-tracker`, the
dispute from the case system, and evidence from transaction/OMS sources; it emits a
`case_id`-keyed draft with `authorization_status: pending-human-authorization`. Adjudication,
credit, submission, closure, and fraud investigation belong to the routes above or an
authorized human.

## Inputs and prerequisites
- The dispute case(s): `case_id`, `role` (issuer|acquirer), `network`, `reason_code`,
  `rule_version_cited`, `dispute_received_date`, `dispute_amount`/`currency`, the disputed
  `transaction` (txn_id, auth_id, amount, currency, date, masked card), the typed evidence
  inventory (each exhibit with a source ref), and `source_ref`. Optional routing flags
  (`fraud_investigation_required`, `merchant_representment_requested`, `iso_exception`).
  Schema: [scripts/validate_input.py](scripts/validate_input.py).
- The **current** card-network reason-code catalog + response windows (`current_rule_version`).
- Read access to the network rules reference, dispute case system, transaction/auth data,
  evidence sources, and templates.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The current card-network rulebook is
authoritative for the reason code's required evidence and response window; the dispute case
system is the system of record for the dispute; transaction/auth and evidence sources supply
identity and exhibits. Cite every rule basis and exhibit. Reason codes and windows are a
**versioned contract** — record `current_rule_version` on every case.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm role, transaction identity, dates,
   and `source_ref` are present; flag an unknown reason code as `needs-data`.
2. **Compute deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): identity tie-out,
   reason-code validation, response deadline + days remaining, evidence sufficiency against the
   reason code's required groups, and rule-version currency. Rules:
   [references/domain-rules.md](references/domain-rules.md).
3. **Assign a decision-support disposition** — `needs-data`, `route-specialist`,
   `rule-version-stale`, `out-of-time-review`, or `evidence-insufficient` blocks drafting with
   an itemized reason; only a clean record becomes `draft-ready-for-review`.
4. **Draft the package** — for a draftable case, assemble the response from
   [assets/output-template.md](assets/output-template.md): identification, reason-code/rule
   basis, deadline block, evidence inventory, exhibit-cited narrative, a structured
   recommendation, and the human review/authorization block. No claim without an exhibit.
5. **Validate output** — run [scripts/validate_output.py](scripts/validate_output.py); fail
   closed on any miss.
6. **Never decide or submit** — hand the reviewed draft to an authorized human for
   adjudication and submission.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces: allowed
decision-support dispositions only; role/transaction identity recorded; a draft-ready case is
on-time (or at-risk), evidence-complete, rule-current, and fully exhibit-supported; approval
recorded and not self-granted; no decision/closure/filing/credit, guarantee, or advice
language; standing note present. See [references/controls.md](references/controls.md). Correct
and re-run until it passes or the record is flagged not-draftable.

## Human approval
`required`. A human must adjudicate the dispute and authorize before any response is submitted
or any credit/liability/closure is recorded in a system of record. This skill proposes, drafts,
and recommends; it never decides, never moves funds, never files, and never closes. Internal
drafting may be reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Unknown reason code** → `needs-data`; map it to the current catalog first; never guess the
  evidence set or window.
- **Role/identity incomplete or mismatched** (bad role, missing txn, currency/amount mismatch)
  → `needs-data`; a human confirms the transaction; never draft on an unresolved identity.
- **Stale rule version** (cited ≠ current) → `rule-version-stale`; refresh from
  `network-rules-change-tracker` before drafting, because the window and evidence set may have
  changed.
- **Past the response deadline** → `out-of-time-review`; never auto-accept liability or write
  off; surface it for a human to decide.
- **Missing evidence group** → `evidence-insufficient`; list the missing group(s); never
  fabricate an exhibit to close a gap.
- **Out-of-scope work** (fraud, merchant representment, ISO exception) → `route-specialist`.
- **Tool timeout / stale ruleset** → return partial output with an explicit incomplete flag and
  the `current_rule_version` used; no retry assumption.

## Output contract
1. **Case queue** — per case: `case_id`, `role`, `reason_code`/title, `deadline` (due date +
   days remaining + status), `disposition`, and `recommended_action`.
2. **Draft case response** (per `draft-ready-for-review` case) — identification, reason-code/rule
   basis, deadline, evidence inventory, exhibit-cited narrative, structured recommendation, and
   `authorization_status: pending-human-authorization`, following
   [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-draftable case with its itemized reason(s) and `needs`.
4. **Machine-readable** — the case records keyed by `case_id` with `current_rule_version`.
5. **Standing note** — "Draft decision-support only. This skill does not decide any dispute,
   accept or deny a chargeback, issue provisional or final credit, assign liability, submit or
   file a response, or close a case; ... A human adjudicator must review every recommendation
   and authorize any submission."

## Privacy and records
**Highly Confidential — customer NPI/PII and cardholder data.** Never place full PAN in the
package; mask to last four. Include only the evidence necessary to respond to the reason code
(data minimization; PCI DSS scope applies). Retain the draft package, `current_rule_version`,
evidence citations, and the human review/authorization record with the case; log every read and
every draft produced with the analyst identity.

## Gotchas
- **Drafting ≠ deciding or submitting.** The package is a draft; a human adjudicates and files
  it. Never emit "decided / accepted / submitted / credited / closed" language or imply the
  dispute is resolved.
- **Deadlines are hard and network-specific.** A response after the window is wasted; always
  compute against the current ruleset and a stated `processing_date`.
- **Reason code drives everything.** The required evidence and window come from the code under
  the current rulebook; the wrong code or a stale version produces the wrong package.
- **Every claim needs an exhibit.** A persuasive sentence with no backing evidence is an
  unsupported claim and is stripped by the output screen.
- **Reg E / Reg Z timing is the human's call.** The skill surfaces deadlines and evidence; the
  provisional/final credit decision and consumer obligations are adjudicated by an authorized
  human, never here.
- **Ruleset is a versioned contract.** Record `current_rule_version` on every case so the
  deadline and evidence basis are reproducible and reviewable.
