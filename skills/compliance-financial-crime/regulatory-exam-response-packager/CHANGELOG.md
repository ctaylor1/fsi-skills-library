# Changelog — regulatory-exam-response-packager

## [0.1.0] — 2026-07-18
Initial authoring in the FSI Skills Library (baseline status: `new`). Created to assemble a
controlled, audit-ready **draft** examination/inquiry response package from evidence produced
by upstream skills and humans, with a human owning review and submission.

- **Scope:** map each regulator request to its narrative + evidence, verify provenance, compute
  per-request coverage/readiness, report issue/MRA status, and confirm required approvals.
  Draft-only; no system-of-record change.
- **Controls:** R3; never submits/sends the response, closes an exam item/finding/MRA, attests
  on the firm's behalf, presents an unsupported or unapproved claim as ready, or writes a
  system of record. SAR-confidentiality / tipping-off screen; versioned template + approver
  config; segregation of duties (preparer ≠ sole approver ≠ submitter).
- **Assets:** `assets/output-template.md` — ten-section response-package contract enforced by
  `validate_output` (template fidelity).
- **Scripts:** `validate_input` (request/response schema, orphan-response + provenance checks,
  gap/unsupported warnings), packaging engine (`calculate_or_transform`: coverage/readiness +
  citations + approvals + template sections), `validate_output` (template fidelity, allowed
  statuses, no unsupported/unapproved ready items, no submission/closure/attestation language,
  readiness + standing note). Python stdlib-only, each with `--selftest`.
- **Evaluations:** trigger/routing, golden 6-request package exercising every coverage/status
  path, deterministic script checks, fail-closed safety fixture (submission/closure/attestation),
  prompt-injection + tipping-off refusals, and a submission/closure authorization case.
- **Handoffs:** upstream from `aml-alert-triager`, `transaction-monitoring-alert-investigator`,
  `sanctions-match-adjudicator`, `suspicious-activity-report-drafter`,
  `kyc-customer-due-diligence-screener`, `enhanced-due-diligence-packager`,
  `customer-risk-rating-reviewer`, `policy-procedure-gap-analyzer`,
  `regulatory-change-impact-analyzer`, `audit-evidence-packager`,
  `regulatory-reporting-data-validator`, `risk-control-self-assessment-assistant`; downstream to
  a human (regulatory affairs / compliance / legal) who reviews and submits.

### Pending before release
- Compliance/legal + regulatory-affairs blind review; segregation-of-duty confirmation.
- Confirm the response template + required-approver config source, owner, and versioning.
- Wire read-only MCP integrations (case-management, records archive, regulatory corpus,
  approval broker) at deployment.
