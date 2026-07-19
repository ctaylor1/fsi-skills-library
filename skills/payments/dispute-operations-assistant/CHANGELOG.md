# Changelog — dispute-operations-assistant

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to support
issuer- and acquirer-side card disputes from the bank's side — distinct from merchant-side
representment packaging (`chargeback-dispute-packager`) and from fraud investigation
(`payment-fraud-case-investigator`).

- **Scope:** verify role and transaction identity, validate the network reason code against the
  current rulebook version, compute the response deadline, check evidence sufficiency, and draft
  a cited case response for human adjudication and authorized submission. Draft-only; no
  system-of-record change.
- **Controls:** R3 decision support; human approval `required`. Never decides/accepts/denies a
  dispute, issues provisional/final credit, assigns liability, makes a fraud finding, submits or
  files a response, or closes a case. Deterministic screens reject decision/closure/filing/credit
  language and self-authorization; a stale rule version or missing evidence blocks drafting;
  outputs fail closed.
- **Scripts:** `validate_input` (case schema, role/identity, ISO dates, data-gap warnings), the
  case engine (identity tie-out, reason-code validation, deadline computation, evidence
  sufficiency, rule-version currency, draft-package assembly), and `validate_output` (allowed
  dispositions, required template sections, citations, approval recorded/not self-granted,
  decision/guarantee/advice screen, standing note).
- **Assets:** `assets/output-template.md` — the draft dispute-response deliverable with required
  sections and the human review/authorization block.
- **Evaluations:** trigger/routing, a golden 7-case queue exercising every disposition
  (draft-ready incl. deadline-at-risk, evidence-insufficient, needs-data, out-of-time-review,
  rule-version-stale, route-specialist), deterministic script checks, a fail-closed safety
  fixture (decision/filing language + self-authorization + missing note), and no-decision /
  no-submission / credit-authorization refusals.
- **Handoffs:** merchant-side → `chargeback-dispute-packager`; fraud → `payment-fraud-case-investigator`;
  rule changes → `network-rules-change-tracker`; ISO exceptions → `payment-exception-investigator`;
  reconciliation → `transaction-reconciliation-helper` / `settlement-break-reconciler`.

### Pending before release
- Payments operations/risk control-owner + legal/compliance (Reg E / Reg Z, network-rules)
  blind review; segregation-of-duty review (draft vs. adjudicate vs. submit).
- Confirm the current network reason-code catalog + response-window source, owner, and
  versioning (wire `network-rules-change-tracker`).
- Wire read-only MCP integrations (dispute case system, transaction/auth, evidence, templates)
  at deployment; adjudication and submission remain human-authorized.
