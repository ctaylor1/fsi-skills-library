---
name: insurance-policy-transaction-packager
description: "Prepare a source-bound policy issue, endorsement, renewal, cancellation, nonrenewal or reinstatement request with current-version checks, before/after changes, authority, document and notice plans and supplied premium effects. Use for policy administration preparation; no policy change, notice delivery, coverage decision or invented refund rule."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Artifact-creation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Draft & package"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 2"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction and product profiles required; synthetic US-TEST is not a legal profile"
  aws-fsi-owner: "Insurance policy administration and finance"
  aws-fsi-primary-user: "Policy administration specialist"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Policy Transaction Package

Bind the requested transaction to the actual policy ID, current version, represented party and dates before drafting changes. Preserve the before value from the policy snapshot; a request cannot replace it. Separate issuing a new policy, changing a live term, terminating midterm, nonrenewing at expiry and reinstating from cancellation. Select the applicable supplied profile rather than inferring statutory rights from a transaction name.

For an endorsement, build an explicit before/after field table, identify the versioned form and carry the sourced signed written-premium change. Check concurrent or duplicate requests before suggesting a sequence. For notice planning, use the supplied calendar-day convention and required recipients; an overdue planned send date is not proof of delivery. Escalate business-day, service-method, receipt and legal-deadline questions to the policy/rule owner. Draft-only readiness is neither authorization nor proof that coverage changed.

Life/annuity value or ownership-rights changes require the separate contract-service review. Health payer eligibility, group enrollment, rescission and premium refund law are outside the implemented native method. A profile may document a local practice, but does not make that practice legal or current.

## Native preparation and review

Read [references/source-map.md](references/source-map.md) for the structured input and [references/domain-rules.md](references/domain-rules.md) for method limits. Preserve supplied unknowns, conflicting versions and source passages. Do not manufacture missing facts to satisfy the schema. The examples are invented records, not institutional rule profiles.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Validate the saved output with `python scripts/validate_output.py OUTPUT.json`; this recomputes the native result from retained evidence. Use [assets/output-template.md](assets/output-template.md) to present a readable professional draft. Keep authored interpretation separate from the deterministic artifact and cite the underlying source passages.

Follow [references/controls.md](references/controls.md) and [references/handoffs.md](references/handoffs.md). [references/insurance-contract.md](references/insurance-contract.md) describes shared provenance and status fields. The receiving workflow must validate its actual native input. A role label, hash, complete checklist or prior approval is not permission to act.

Run `python scripts/test_domain.py` and the checks in [evals/evals.json](evals/evals.json). Local checks do not establish specialist or deployment acceptance.

See [native workflow foundation](references/insurance-foundation.md) for source-bound context mappings, inherited uncertainty and output validation.
