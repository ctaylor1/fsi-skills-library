---
name: investment-record-normalizer
description: "Normalize supported supplied holdings, cash, orders and transactions one-to-one using an explicitly matched mapping-ruleset version; preserve original-record lineage and unresolved basis fields."
license: MIT
compatibility: Amazon Quick Desktop; requires read-only custodian, fund-administrator, OMS, and accounting/GL feed integrations plus a controlled, versioned mapping-ruleset service and entity-resolution reference data. Deterministic stdlib-only scripts over documented JSON schemas + de-identified fixtures; no live connectors, network, or retries in this repository.
metadata:
  aws-fsi-category: "Data, AI & Model Governance"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Domain workflow"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Investment Data stewardship & governance"
  aws-fsi-primary-user: "Investment-data operations analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

# Investment record normalization

Normalize supported supplied holdings, cash, orders and transactions one-to-one using an explicitly matched mapping-ruleset version; preserve original-record lineage and unresolved basis fields.

## Workflow

1. Establish the named portfolio/fund, dates, source access, responsible reviewer and applicable policy. This development package has not received institutional acceptance.
2. Read [native schema](references/schema.md) and [bounded method](references/domain-rules.md). Obtain actual source fields; preserve missingness and unresolved upstream issues.
3. Run `python3 -B scripts/validate_input.py INPUT.json`, then `python3 -B scripts/calculate_or_transform.py INPUT.json`. These offline utilities use supplied JSON; no live connector or source authentication is bundled.
4. Validate the immutable result with `python3 -B scripts/validate_output.py OUTPUT.json --input INPUT.json`. Keep the retained input separate from outputs and downstream audiences. Source hashes establish reproducibility, not factual correctness, source authentication or authority.
5. Review exceptions and unknowns with the accountable professional. Write any narrative as a separate reviewed artifact; the native validator accepts only the computed schema. Apply [controls](references/controls.md) and [handoff boundaries](references/handoffs.md).

## Sources and operation

Use [source-map](references/source-map.md) for provenance requirements. Required enterprise integrations are deployment prerequisites, not installed capabilities. Jurisdiction metadata does not create applicable legal rules. Thresholds and synthetic fixtures are development conventions requiring target-specific review.

The eval manifest contains executable regression checks and declarative workflow/routing cases. Software checks establish bounded behavior only; natural-language quality, independent specialist review, audience isolation and deployment acceptance remain separate gates.

## Phase 1 support boundary

Bounded source-specific JSON normalization

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.
