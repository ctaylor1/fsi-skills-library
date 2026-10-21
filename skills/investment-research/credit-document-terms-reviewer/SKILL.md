---
name: credit-document-terms-reviewer
description: "Extract cited credit terms and consolidate executed document versions using explicitly reviewed supplied amendment changes; preserve unresolved interpretations without covenant compliance or legal opinions."
license: MIT
compatibility: Python 3.10+ offline supplied-JSON methods; source retrieval, entitlements and authenticated delivery require institution-owned integration.
metadata:
  aws-fsi-category: "Investment Research"
  aws-fsi-skill-type: "Utility skills"
  aws-fsi-risk-tier: "R2"
  aws-fsi-archetype: "Analyze & review"
  aws-fsi-agent-pattern: "Interactive decision-support copilot"
  aws-fsi-delivery-wave: "Wave 5 - 2026 industry expansion"
  aws-fsi-action-mode: "Read-only analysis"
  aws-fsi-scheduled-agent: "no"
  aws-fsi-baseline-status: "existing-updated"
  aws-fsi-human-approval: "external-delivery"
  aws-fsi-data-classification: "Highly Confidential (MNPI / client-confidential)"
  aws-fsi-jurisdictions: "Institution-supplied applicability; no universal legal default"
  aws-fsi-owner: "Investment Research methods & evidence"
  aws-fsi-primary-user: "Credit research analyst"
  aws-fsi-version: "0.3.0"
  aws-fsi-recertification-date: "2027-09-20"
---

# Credit document term normalization

The native method normalizes supplied text candidates for maturity, coupon, seniority, collateral, call provisions, covenants and baskets. It is not a PDF parser or complete contract review. Simple date/coupon formats, keyword classification and limited USD literal extraction are supported. Guarantee enforceability, intercreditor priority, linked definitions, governing-term consolidation, covenant headroom, breach, waiver, default and recovery opinions remain outside the native method.

## Workflow

1. Confirm issuer/instrument, requested research use, economic period, source knowledge cutoff where relevant, applicable institutional profile and responsible reviewer. Use only authorized supplied material; the package opens no network connections.
2. Read [schema](references/schema.md) and [method limits](references/domain-rules.md). Run `python3 -B scripts/validate_input.py input.json` before computing. Preserve gaps and unsupported scope.
3. Run `python3 -B scripts/calculate_or_transform.py input.json` and retain the exact original input separately. Fixtures illustrate synthetic contracts and are never substitutes for missing source facts.
4. Run `python3 -B scripts/validate_output.py output.json --input input.json`. The output is immutable native evidence; authored narrative is a separate draft requiring review. Full reconstruction rejects altered/extra/removed fields and mismatched input binding.
5. Hand off the validated native artifact, retained original, source references, cutoff/basis, missing coverage and review gates under [handoffs](references/handoffs.md). Never promote software validity to professional acceptance, authenticated source truth or action authority.

## Inputs and outputs

Require nonempty `doc_id`, `doc_type`, `issuer`, legal `issuer_id`, `instrument`, `instrument_id`, `doc_version`, `governing_law` and valid calendar `effective_date`. `expected_fields[]` uses supported field labels. Each candidate requires supported `field`, nonempty string `raw_value`, positive integer `page`, and nonempty string `locator`; optional confidence is a finite number in [0,1]. `is_amendment` is boolean when supplied. Amendment/supersession indicators are retained as unresolved context. Economic effective dates are not knowledge timestamps or evidence of source availability.

The extraction packet retains issuer/instrument identifiers and labels, document identity/version/governing-law assertions, raw candidates, normalized values, status, reasons and page/locator citations. `not_found` means no supplied candidate, not absence from the full document. Drafts, amended or superseding documents have their term values withheld with `needs_review` until a governing-document review occurs outside this normalizer.

## Controls and unavailable behavior

Load-bearing legal entity, instrument and document version may not be inferred from a display label. A supplied execution label does not prove the document is controlling or complete. Amendment flags withhold values; the method does not consolidate amendments. A normalized security or seniority token is not a legal-priority conclusion.

The [controls](references/controls.md) distinguish executable guards from institution-owned controls. All work is read-only research/draft preparation. Respect MNPI, confidentiality, information barriers and source licensing; no publication, trade, lender consent, credit approval or system-of-record write is implemented. If sources, access, applicable policy or specialist methods are unavailable, return the useful supported partial, state precisely what is withheld and identify the owner of the next review.

## Validation evidence

The bundled executable eval commands and `tools/test_ir_credit_phase1.py` exercise bounded native behavior, expected arithmetic, mutations and invalid input shapes. Trigger/routing/narrative eval cases remain specifications unless separately executed. They do not establish practitioner, institution, deployment, legal or authority acceptance.

## Shared Phase 1 evidence standard

Read [the evidence and control standard](references/evidence-standard.md) for identity,
knowledge timing, permission use, detached source binding and professional acceptance
boundaries. The package retains its native schema; no universal adapter is implied.

## Phase 2 analytical mode

The explicit `schema_version: ir-phase2/1.0` intake adds the bounded method in [Phase 2 schema](references/phase2-schema.md) and [Phase 2 rules](references/phase2-rules.md). Legacy Phase 1 input remains supported. New analytical results use the source-gated `ir-analysis/2.0` result contract, not the legacy fields. Retain the exact original for full output reconstruction. This mode grants no source authentication, approval, publication, trade or live-model authority.
