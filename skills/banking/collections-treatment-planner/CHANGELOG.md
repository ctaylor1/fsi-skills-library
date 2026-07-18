# Changelog — collections-treatment-planner

## [0.1.0] — 2026-07-17
Initial authoring in the FSI Skills Library (baseline status: `new`).

- **Scope:** derive a delinquency band, run suppression + contact-frequency screens, flag
  enhanced care, and produce an evidenced shortlist of eligible treatment options with policy
  citations. Read-only decision support; no decision, no offer, no system-of-record change.
- **Screens & treatments (deterministic):** delinquency bands (Current/Early/Mid/Late/Severe);
  suppression screen (cease-communication, attorney-represented, dispute-pending, do-not-contact,
  bankruptcy, SCRA); Reg F 7-in-7 phone-frequency screen; enhanced-care on vulnerability; nine
  config-driven treatments (reminder, promise-to-pay, arrangement, hardship forbearance,
  due-date change, re-age review, settlement referral, counseling referral, specialist referral)
  — each cited (see `scripts/calculate_or_transform.py` and `references/domain-rules.md`).
- **Controls:** R3; mandatory human adjudication; hard boundary against approving/denying,
  granting forbearance, modifying, waiving, settling, re-aging, closing, charging off, filing,
  or bureau-reporting; suppression and contact-cap honored; no FDCPA/UDAAP threats;
  versioned-config eligibility only; `required` human approval.
- **Scripts:** `validate_input` (case schema, evaluability warnings), treatment engine,
  `validate_output` (adjudication + disclaimer, eligible-treatment citations, deterministic
  eligible-set tie-out, decision/threat-language screen, suppression + call-cap enforcement).
- **Evaluations:** trigger/routing, golden Mid/enhanced-care case, suppressed-outreach edge,
  deterministic script checks, fail-closed safety fixture + injection, human-adjudication
  authorization.
- **Handoffs:** downstream to `loan-servicing-exception-resolver` (execution, R4),
  `vulnerable-customer-support-assistant`, `loan-affordability-precheck`,
  `bank-statement-analyzer`, `cashflow-forecaster`, `complaint-resolution-assistant`.

### Pending before release
- Domain SME (collections & hardship) + control-owner blind review; fair-treatment/UDAAP and
  vulnerable-customer review of the eligibility rules and tone guidance.
- Confirm the versioned band/eligibility/contact-cap config source, its owner, and jurisdiction
  packs (Reg F specifics, state collection rules, SCRA).
- Wire read-only MCP integrations (servicing, CRM, product terms, config, affordability calc)
  at deployment.
