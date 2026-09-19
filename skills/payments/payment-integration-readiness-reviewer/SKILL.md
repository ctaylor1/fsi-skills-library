---
name: payment-integration-readiness-reviewer
description: Review a payment integration checklist and supplied evidence-review records for operational/control gaps. Distinguishes evidence pointers from inspected artifacts; produces an internal readiness assessment without approving go-live.
license: MIT
compatibility: Python 3.10+ offline JSON analysis. Expected source-system integrations must be supplied by deployment; no connectors or actions bundled.
metadata:
  aws-fsi-category: "Payments"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII; cardholder data)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Payments operations & risk"
  aws-fsi-primary-user: "Payments implementation manager"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Payment integration readiness review

Use for a documented integration readiness review. Read
[references/source-map.md](references/source-map.md), then run
`python scripts/validate_input.py INPUT.json`,
`python scripts/calculate_or_transform.py INPUT.json`, and
`python scripts/validate_output.py OUTPUT.json`.

A supplied evidence_ref is a pointer, not inspected proof. To count a declared
inspection, the attestation needs evidence_review with status=inspected, reviewer,
reviewed_at, scope and result_ref. Offline validation does not authenticate the
reviewer or inspect the referenced artifact. Unknown or duplicated item states
remain gaps. N/A requires separate applicability review; manual reconciliation
requires alternative-control evidence and is not an exemption.

Report category coverage, missing evidence and the basis of each finding. Keep
certification, negative paths, duplicate/uncertain outcomes, reconciliation, refunds/
returns, support, monitoring, recovery and security in the deployment checklist.
The bundled checklist is illustrative, not universal completeness or production
acceptance. Neither a score nor ready-for-review authorizes go-live.

See [references/domain-rules.md](references/domain-rules.md),
[references/controls.md](references/controls.md),
[references/handoffs.md](references/handoffs.md) and
[references/payment-contract.md](references/payment-contract.md).
Run `python scripts/test_phase1.py`; no production connector is bundled.

## Phase 3 resilience and migration evidence

For a hub, orchestration, cloud/mainframe migration, ledger or active-active proposal,
use the additive [references/resilience-schema.md](references/resilience-schema.md).
Run `python scripts/validate_resilience_input.py INPUT.json`,
`python scripts/review_resilience.py INPUT.json > OUTPUT.json`, and
`python scripts/validate_resilience_output.py OUTPUT.json --input INPUT.json`.
The original CLI and input contract above remain supported unchanged.

Inspect explicit financial ownership, fencing, idempotency scope, changed payload
rejection and uncertain-outcome handling. Bind test evidence to the proposed release,
mode, component scope and exact observations. A pointer or pass flag cannot satisfy a
scenario: inspect supplied steps and observations, then retain missing/failed coverage.
Use [references/resilience-rules.md](references/resilience-rules.md) for the negative paths
and [assets/resilience-template.md](assets/resilience-template.md) for the review record.
No offline test record authenticates execution or authorizes go-live. Run
`python scripts/test_phase3.py` for boundary regressions.
