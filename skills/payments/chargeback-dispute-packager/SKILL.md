---
name: chargeback-dispute-packager
description: >-
  Assemble a merchant-side card-chargeback representment (second-presentment) package: match
  the network reason code to its required evidence, compute the representment deadline, tie
  every exhibit back to the disputed transaction, and draft a concise, exhibit-cited rebuttal
  narrative from approved templates. Use when a merchant or merchant chargeback analyst needs
  to respond to a chargeback/dispute, build a representment or compelling-evidence package,
  check a reason code's evidence requirements or filing deadline, or verify transaction
  identity and evidence completeness before submission. Keywords: chargeback, representment,
  second presentment, reason code, Visa/Mastercard dispute, compelling evidence, proof of
  delivery, ARN, deadline. This skill NEVER submits, files, or transmits the representment to
  any acquirer or card network, never makes a fraud or liability determination, never
  guarantees a dispute outcome, and never invents evidence — it drafts a package for human
  review and authorized submission.
license: MIT
compatibility: Amazon Quick Desktop; requires card-network reason-code/deadline reference, acquirer/gateway, merchant OMS/fulfillment, controlled-template, and case-portal MCP integrations (all read-only; submission is out of scope).
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 1 - stabilize existing"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Merchant / merchant chargeback analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-07-17"
---

# Chargeback Dispute Packager

## Purpose and outcome
Turn a raw chargeback into an audit-ready, merchant-side **representment (second
presentment) draft**: identify the network reason code, compute the representment deadline,
confirm the supplied evidence satisfies that reason code's requirements, tie every exhibit
back to the disputed transaction, and draft a concise, exhibit-cited rebuttal from an
approved template. The outcome is a review-ready package (or a clear, itemized reason it
cannot be packaged yet) that a human authorizes and submits. The skill never submits, never
decides the dispute, and never guarantees an outcome.

## Use when
- "Respond to this chargeback / build a representment for dispute CB-XXXX."
- "What evidence and deadline apply to Visa 13.1 / Mastercard 4853?"
- "Is my evidence complete and does it match the disputed transaction?"
- "Assemble a compelling-evidence package for this card-absent fraud chargeback."

## Do not use
- **Issuer-/acquirer-side** dispute handling or applying network rules from the bank side →
  `dispute-operations-assistant`.
- **Fraud determination / fraud-alert investigation** → `payment-fraud-case-investigator`.
- **Reconciling** chargeback debits, transactions, or settlement to the ledger →
  `transaction-reconciliation-helper`, `settlement-break-reconciler`.
- **Interchange/fee economics** of chargebacks → `merchant-fee-optimizer`.
- **Interpreting a network rule change** itself → `network-rules-change-tracker`.
- Any request to **submit/file the representment, decide the dispute, or guarantee a win** →
  refuse; draft only and route to a human.

## Adjacent-skill handoffs
See [references/handoffs.md](references/handoffs.md). This skill is merchant-side drafting
only. It consumes the current ruleset (`ruleset_version`) from
`network-rules-change-tracker`, the chargeback from acquirer/gateway, and evidence from the
OMS; it emits a `dispute_id`-keyed draft with `reviewer_signoff_required`. Submission,
reconciliation, and fraud adjudication belong to the routes above or to an authorized human.

## Inputs and prerequisites
- The chargeback record: `dispute_id`, `network`, `reason_code`, `chargeback_date`,
  `dispute_amount`, `currency`, and the disputed `transaction` (txn_id/ARN, auth code,
  amount, currency, date); the evidence inventory (typed exhibits with source refs); and the
  merchant's asserted narrative points (each citing an exhibit). Optional: prior undisputed
  transactions for compelling-evidence eligibility. Schema:
  [scripts/validate_input.py](scripts/validate_input.py).
- The **current** card-network reason-code catalog + representment windows (`ruleset_version`).
- Read access to the reason-code reference, acquirer/gateway, OMS/fulfillment, and templates.

## Source hierarchy
See [references/source-map.md](references/source-map.md). The card-network reason-code &
deadline reference is authoritative for what evidence is required and by when; the acquirer
is the system of record for the chargeback; the OMS supplies evidence. Cite every exhibit
and rule. Reason codes and windows are a **versioned contract** — record `ruleset_version`
on every package.

## Workflow
1. **Validate & normalize** — run `validate_input`; confirm the dispute, transaction, and
   evidence are structurally complete; flag an unknown reason code as `needs-data`.
2. **Compute deterministically** — run
   [scripts/calculate_or_transform.py](scripts/calculate_or_transform.py): representment
   deadline and days remaining, evidence completeness against the reason code's required
   groups, transaction-identity tie-out, compelling-evidence eligibility (fraud codes), and
   narrative fidelity. Rules: [references/domain-rules.md](references/domain-rules.md).
3. **Assign status** — `past-deadline`, `insufficient-evidence`, `identity-mismatch`,
   `unsupported-claim`, or `needs-data` blocks packaging with an itemized reason; only a
   clean record becomes `draft-representment`.
4. **Draft the package** — for a packageable dispute, assemble the representment from
   [assets/output-template.md](assets/output-template.md): identifiers, deadline block,
   exhibit-cited rebuttal narrative, evidence index, compelling-evidence flag, and the
   reviewer sign-off block. No claim without an exhibit.
5. **Validate output** — run
   [scripts/validate_output.py](scripts/validate_output.py); fail closed on any miss.
6. **Never submit** — hand the reviewed draft to an authorized human for filing.

## Validation loop
Run `validate_input` before and `validate_output` after. The output screen enforces:
approved reason code; a packageable record is on-time, evidence-complete, identity-clean,
and fully exhibit-supported; no outcome-guarantee, advice, or "already submitted/filed"
language; standing disclaimer present. See [references/controls.md](references/controls.md).
Correct and re-run until it passes or the record is flagged not-packageable.

## Human approval
`external-delivery`. A human must review and authorize before the representment is submitted
to the acquirer/network or any system of record changes. This skill proposes and drafts; it
never files, never decides the dispute, and never guarantees a result. Internal drafting may
be reviewer-sampled per [references/controls.md](references/controls.md).

## Failure handling
- **Unknown reason code** → `needs-data`; map it to the current catalog first; do not guess
  the evidence set or deadline.
- **Missing evidence group** → `insufficient-evidence`; list the missing group(s); never
  fabricate an exhibit to close a gap.
- **Identity does not tie** (currency/amount/foreign exhibit) → `identity-mismatch`; a human
  confirms which transaction the evidence belongs to.
- **Past the representment deadline** → `past-deadline`; never mark packageable; surface the
  gap so a human can decide.
- **Unsupported narrative point** → `unsupported-claim`; drop or substantiate the claim.
- **Tool timeout / stale ruleset** → return partial output with an explicit incomplete flag
  and the `ruleset_version` used; no retry assumption.

## Output contract
1. **Package queue** — per dispute: `dispute_id`, `reason_code`/title, `deadline_status`
   with due date + days remaining, status, and `packageable`.
2. **Representment draft** (per packageable dispute) — identifiers, transaction identity,
   deadline, exhibit-cited rebuttal narrative, evidence index, compelling-evidence flag, and
   `reviewer_signoff_required: true`, following [assets/output-template.md](assets/output-template.md).
3. **Blocked list** — each non-packageable dispute with its itemized reason(s).
4. **Machine-readable** — the packaging records keyed by `dispute_id` with `ruleset_version`.
5. **Standing note** — "Draft representment package for human review only; this skill does
   not submit to any card network or acquirer, does not guarantee any dispute outcome, and
   every claim must be verified against current network rules before submission."

## Privacy and records
**Highly Confidential — customer NPI/PII and cardholder data.** Never place full PAN in the
package; mask to last four. Include only the evidence necessary to rebut the reason code
(data minimization; PCI DSS scope applies). Retain the draft package, `ruleset_version`,
evidence citations, and reviewer sign-off with the case; log every read and every package
produced with the analyst identity.

## Gotchas
- **Drafting ≠ submitting.** The package is a draft; a human files it. Never emit
  "submitted/filed" language or imply the dispute is resolved.
- **Deadlines are hard and network-specific.** A representment filed past the window is
  wasted; always compute against the current ruleset and a stated `as_of_date`.
- **Reason code drives everything.** The required evidence and window come from the code; the
  wrong code produces the wrong package. Map unknown codes before packaging.
- **Every claim needs an exhibit.** A persuasive sentence with no backing evidence is an
  unsupported claim and is stripped by the output screen.
- **Compelling-evidence eligibility is a flag, not a verdict.** It tells the reviewer a
  pathway may apply; it never predicts the outcome.
- **Ruleset is a versioned contract.** Record `ruleset_version` on every package so the
  deadline and evidence basis are reproducible and reviewable.
