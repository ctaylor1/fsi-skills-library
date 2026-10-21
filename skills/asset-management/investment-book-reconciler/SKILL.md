---
name: investment-book-reconciler
description: "Compare compatible supplied position and cash records with exact decimal arithmetic, explicit aggregation and neutral correction alternatives; preserve unknown materiality and unresolved matching bases."
license: MIT
compatibility: Amazon Quick Desktop; requires accounting/IBOR (books of record), custodian, prime-broker, fund-administrator, counterparty, and approved-calculation MCP integrations (all read-only).
metadata:
  aws-fsi-category: "Asset Management"
  aws-fsi-skill-type: "Analysis and evaluation skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Reconcile & validate"
  aws-fsi-agent-pattern: "Interactive production copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Draft-only; no system-of-record change"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "US (default); configure additional jurisdiction packs per deployment"
  aws-fsi-owner: "Asset Management investment & product"
  aws-fsi-primary-user: "Fund operations analyst"
  aws-fsi-version: "0.2.0"
  aws-fsi-recertification-date: "2027-09-20"
---

# Investment position and cash reconciliation

Compare compatible supplied position and cash records with exact decimal arithmetic, explicit aggregation and neutral correction alternatives; preserve unknown materiality and unresolved matching bases.

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

Supplied position/cash reconciliation; not full IBOR/ABOR platform

This package performs only its documented local supplied-input operations. Live source access, authenticated permissions, production engines and professional acceptance are separate deployment requirements. Generated resources are pinned in `references/package-manifest.json`; maintain the canonical shared source. Legacy identifiers resolve through the repository migration registry.

Arithmetic supports the [documented decimal and record-count bounds](references/schema.md); unsupported precision or magnitude fails closed. Use decimal strings to preserve supplied digits.
