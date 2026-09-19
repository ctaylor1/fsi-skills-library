---
name: insurance-capital-solvency-analyzer
description: "Reconcile supplied approved additive capital components, a named capital requirement and approved stress bridges, with labeled control-ratio comparisons. Use for insurer capital evidence review; no RBC or Solvency II formula engine, inferred diversification or solvency certification."
license: MIT
compatibility: Python 3.10+; offline structured evidence only. No live connectors.
metadata:
  aws-fsi-category: "Insurance"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R3"
  aws-fsi-archetype: "Model & calculate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Insurance Phase 3"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "new"
  aws-fsi-human-approval: "required"
  aws-fsi-data-classification: "Highly Confidential (customer NPI/PII)"
  aws-fsi-jurisdictions: "Explicit reviewed jurisdiction, entity and measurement profiles required; synthetic US-TEST is not legal adoption"
  aws-fsi-owner: "Insurance capital management"
  aws-fsi-primary-user: "Insurance capital and solvency analyst"
  aws-fsi-version: "0.1.0"
  aws-fsi-recertification-date: "2027-09-18"
---

# Insurance Capital and Solvency Analysis

Reconcile supplied approved additive capital components, a named capital requirement and approved stress bridges, with labeled control-ratio comparisons. Use for insurer capital evidence review; no RBC or Solvency II formula engine, inferred diversification or solvency certification.

Prepare a source-bound professional draft for a named insurer or portfolio at a stated valuation date. Triage identity, methodology, measurement basis and evidence gaps before investigating differences. A supplied reviewer name is an assertion for accountable review; it does not authenticate approval. Keep recognized unknowns and conflicting versions visible. Do not fabricate values, legal adoption, source passages or approval evidence to satisfy a schema.

Read [references/domain-rules.md](references/domain-rules.md) for the actual bounded method and its exclusions, [references/native-schema.md](references/native-schema.md) to map input, and [references/source-map.md](references/source-map.md) for authority and freshness. The native input is a complete case record with `data` specific to this workflow. Synthetic examples show format only.

Run `python scripts/validate_input.py REQUEST.json`, then `python scripts/calculate_or_transform.py REQUEST.json`. Save the result and run `python scripts/validate_output.py OUTPUT.json`; validation recomputes the complete native output from retained evidence. An unchanged content hash alone is not a semantic check. Present results using [assets/output-template.md](assets/output-template.md), with native calculations separate from authored professional interpretation.

Apply [references/controls.md](references/controls.md), preserve case IDs and source versions, and follow [references/handoffs.md](references/handoffs.md) at adjacent boundaries. The receiving skill must validate its actual native input. [references/insurance-contract.md](references/insurance-contract.md) and [references/insurance-foundation.md](references/insurance-foundation.md) define provenance, inherited uncertainty and reviewed context mappings. A complete local subcheck never clears an unresolved upstream issue.

Run `python scripts/test_domain.py` and executable checks in [evals/evals.json](evals/evals.json). Natural-language trigger, adversarial, independent specialist, legal/control, latency and cost acceptance remain planned unless a separate dated record proves execution. This package is provisional R3, version 0.1.0, draft-only; recertification is due 2027-09-18.
